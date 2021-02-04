from configuration import PREFIXES, PREFIX
from db import bot_session, Servers, Channels

def cache_prefixes(prefixes, name):
    global PREFIXES
    if prefixes:
        for item in prefixes:
            logging.debug('{} prefix {} => {}'.format(name, item.id, item.prefix))
            PREFIXES[item.id] = item.prefix

def load_prefixes():
    global PREFIXES
    PREFIXES.clear()
    prefix_list = Servers.prefixed(bot_session)
    if prefix_list:
        cache_prefixes(prefix_list)

    prefix_list = Channels.prefixed(bot_session)
    if prefix_list:
        cache_prefixes(prefix_list)

    logging.info('Preloaded prefixes:\n{}'.format(PREFIXES))

def prefix_operator(bot, message):
    channel_id = message.channel.id
    server_id = message.guild.id
    return PREFIXES.get(channel_id, PREFIXES.get(server_id, PREFIX))
