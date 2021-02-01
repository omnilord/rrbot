import asyncio, json, re, logging, glob
from os import path
from configuration import MQTT_URL
from asyncio_mqtt import Client, MqttError
from db import Session, Servers, Channels

TOPIC_PREFIX = 'rrbot/settings'
TOPIC_FILTER = f"{TOPIC_PREFIX}/+"
TOPIC = re.compile(f'{TOPIC_PREFIX}/(?P<topic>.+)')
MQTT_LIVE = True
DISPATCH = {}

def register_setting_callback(setting, callback):
    if DISPATCH.get(setting, None) is None:
        DISPATCH[setting] = [callback]
    else:
        DISPATCH[setting].append(callback)

def setting_callback(name):
    """
    decoractor for registering a function as an MQTT setting callback
    """
    def predicate(func):
        register_setting_callback(name, func)
        return func
    return predicate

async def dispatch_message(message):
    m = TOPIC.match(message.topic)
    if m is None:
        return

    fns = DISPATCH.get(m['topic'], None)
    if fns is not None:
        [await fn(json.loads(message.payload.decode())) for fn in fns]

async def mqtt_task():
    attempts = 1
    while MQTT_LIVE:
        try:
            async with Client(MQTT_URL) as client:
                logging.info(f'connected to client at {MQTT_URL}')
                attempts = 1
                await client.subscribe(TOPIC_FILTER)
                async with client.filtered_messages(TOPIC_FILTER) as messages:
                    async for message in messages:
                        await dispatch_message(message)
        except MqttError as err:
            logging.error(err)
        timeout = max(5 * attempts, 30)
        logging.info(f'Will attempt reconnect #{attempt} to {MQTT_URL} in {timeout}')
        await asyncio.sleep(timeout)
        attempts += 1


for f in glob.glob(path.join(path.dirname(__file__), "*.py")):
    if path.isfile(f) and not f.endswith('__init__.py'):
        __import__(f"mqtt_client.{path.basename(f)[:-3]}")

__running = asyncio.ensure_future(mqtt_task())

def shutdown():
    __running.cancel()
