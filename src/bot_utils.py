import os, sys, logging
from configuration import ADMINS, PREFIXES, PREFIX
from discord.ext import commands
from pathlib import Path
from db import Session, bot_session, Servers, Channels, Users, Roles
from functools import wraps

"""
Core utlities
"""

def load_extension_directory(bot, ext):
    cmd_path = os.path.join(os.getcwd(), ext)
    for f in os.listdir(cmd_path):
        if f == '__init__.py' or not f.endswith('.py'):
            continue
        bot.load_extension('{}.{}'.format(ext, Path(f).stem))

def load_prefixes():
    global PREFIXES
    PREFIXES.clear()
    prefix_list = Servers.prefixed(bot_session)
    if prefix_list:
        for server in prefix_list:
            print('prefix {} => {}'.format(server.id, server.prefix))
            PREFIXES[server.id] = server.prefix

    prefix_list = Channels.prefixed(bot_session)
    if prefix_list:
        for channel in prefix_list:
            print('prefix {} => {}'.format(channel.id, channel.prefix))
            PREFIXES[channel.id] = channel.prefix

    print('Preloaded prefixes:\n{}'.format(PREFIXES))

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
