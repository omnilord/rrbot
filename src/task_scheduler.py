import asyncio, uuid, logging

tasks = {}

DEFAULT_TASK_DELAY = 10


async def coroutine_runner(task, key, delay, *args):
    """
    internal execution of the coroutine task and cleanup
    of task runner artifacts.
    """

    await asyncio.sleep(delay)
    logging.info(f'Running coroutine task for key={key}')
    await task(*args)
    tasks.pop(key)
    logging.info(f'Completed coroutine task for key={key}')
    return


def runner(task, key, *args):
    """
    internal execution of the task and cleanup
    of task runner artifacts.
    """

    logging.info(f'Running standard task for key={key}')
    task(*args)
    tasks.pop(key)
    logging.info(f'Completed standard task for key={key}')
    return


def register(callback, *args, key=None, delay=DEFAULT_TASK_DELAY):
    """
    Add a callback to the asyncio call_later event loop.

    Returns the callback key on success.  Raises on any
    failures (don't know what downstream errors will propigate).

    Parameters:
    `callback` - the callback method.
    `args` - the parameterized list of arguments to be passed to the callback
            (no keyword args).
    `key`  - the optional keyword for deduplicating.  If `key` is provided,
            the task runner will cancel an existing previous task assigned
            that key and replace it with a new callback.
    `delay` - how long to wait in seconds before executing the callback.
    """

    if delay < 1:
        raise ArgumentError('task delay cannot be less than 1 second.')
    if key is None:
        key = uuid.uuid4()
    deregister(key, method='get')
    if asyncio.iscoroutinefunction(callback):
        logging.info(f'registering future task for key={key}')
        task = coroutine_runner(callback, key, delay, *args)
        tasks[key] = asyncio.ensure_future(task)
    else:
        logging.info(f'registering call later for key={key}')
        loop = asyncio.get_running_loop()
        tasks[key] = loop.call_later(delay, runner, callback, key, *args)
    return key


def deregister(key, method='pop'):
    """
    cancel and clear a key, if it exists.

    Parameters:
    `key` - the identity of a task to remove from the queue.
    `method` - <internal use>
    """

    fn = getattr(tasks, method)
    task = fn(key, None)
    if task is not None and not task.cancelled():
        logging.info(f'Cancelling task for key={key}')
        task.cancel()


def shutdown():
    """
    bot is going down, kill all the tasks
    """

    [task.cancel() for task in tasks.values()]
