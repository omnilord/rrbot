import logging
from bot_utils import notify_debug

def setup(bot):
    logging.info('Loading generic `on_ready` event')
    @bot.event
    async def on_ready():
        await notify_debug(bot, 'I am alive!')

