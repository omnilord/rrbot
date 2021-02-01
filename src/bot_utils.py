import os, sys, logging
from configuration import ADMINS, PREFIXES, PREFIX, DEBUG_CHANNEL
from discord.ext import commands
from discord import NotFound, Forbidden, HTTPException, InvalidData
from pathlib import Path
from db import Session, bot_session, Servers, Channels, Users, Roles
from functools import wraps
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

"""
Core utlities
"""

class RRBotException(Exception):
    pass

def load_extension_directory(bot, *ext):
    cwd = os.getcwd()
    ext_path = os.path.join(cwd, *ext)
    for root, dirs, files in os.walk(ext_path):
        for f in files:
            path = os.path.join(root, f)
            if not os.path.isfile(path) or not f.endswith('.py') or f.startswith('.') or f.startswith('_'):
                continue
            rel = os.path.splitext(os.path.relpath(path, cwd))[0]
            extension = rel.replace(os.sep, '.')
            bot.load_extension(extension)


def load_prefixes():
    global PREFIXES
    PREFIXES.clear()
    prefix_list = Servers.prefixed(bot_session)
    if prefix_list:
        for server in prefix_list:
            logging.debug('server prefix {} => {}'.format(server.id, server.prefix))
            PREFIXES[server.id] = server.prefix

    prefix_list = Channels.prefixed(bot_session)
    if prefix_list:
        for channel in prefix_list:
            logging.debug('channel prefix {} => {}'.format(channel.id, channel.prefix))
            PREFIXES[channel.id] = channel.prefix

    logging.info('Preloaded prefixes:\n{}'.format(PREFIXES))

def prefix_operator(bot, message):
    channel_id = message.channel.id
    server_id = message.guild.id
    return PREFIXES.get(channel_id, PREFIXES.get(server_id, PREFIX))

"""
Auxiliary utiltizes
"""

def _is_server_moderator(d_user):
    user_id = d_user.id

    if _is_bot_admin(user_id):
        return True

    user = bot_session.query(Users).filter(Users.id == user_id).first()
    if user is not None and user.moderator:
        return True

    for urole in d_user.roles:
        modrole = bot_session.query(Roles).filter(Roles.id == urole.id).first()
        if modrole is not None and modrole.moderator:
            return True

    return False

def _is_bot_admin(user_id):
    return user_id in ADMINS

def is_bot_admin():
    """
    This is a command level check for bot administrators
    """
    def predicate(ctx):
        return _is_bot_admin(ctx.message.author)
    return commands.check(predicate)

def _db_session(ctx):
    ctx.db = Session()

def cmd_db_wrapper(fn):
    def _cmd_db_wrapper(fn):
        """
        wrapper to inject a command context with a database session
        """
        @wraps(fn)
        async def predicate(ctx, *args, **kwargs):
            try:
                _db_session(ctx)
                return await fn(ctx, *args, **kwargs)
            except SQLAlchemyError:
                if db_errors_silent == False:
                    await ctx.send('DB Error.')
            finally:
                ctx.db.close()
        return predicate
    return _cmd_db_wrapper

def cog_db_wrapper(fn):
    def _cog_db_wrapper(fn):
        """
        wrapper to inject a cog command context with a database session
        """
        @wraps(fn)
        async def predicate(self, ctx, *args, **kwargs):
            try:
                _db_session(ctx)
                return await fn(self, ctx, *args, **kwargs)
            except SQLAlchemyError:
                if db_errors_silent == False:
                    await ctx.send('DB Error.')
            finally:
                ctx.db.close()
        return predicate
    return _cog_db_wrapper

def db_session(cog=False, db_errors_silent=True):
    return cog_db_wrapper(db_errors_silent) if cog else cmd_db_wrapper(db_errors_silent)

async def bot_fetch(fn, *args, **kwargs):
    try:
        return await fn(*args, **kwargs)
    except (NotFound, Forbidden, HTTPException, InvalidData):
        return None

async def notify_debug(bot, msg):
    channel = await bot_fetch(bot.fetch_channel, DEBUG_CHANNEL)
    if channel is None:
        logging.warning('Unable to send message to debug channel `{}`:\n{}'.format(DEBUG_CHANNEL, msg))
    else:
        await channel.send('I am alive!')

def get_tz(tzone_name=None):
    if tzone_name is None:
        tzone_name = 'America/New_York'
    try:
        return ZoneInfo(tzone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo('America/New_York')


