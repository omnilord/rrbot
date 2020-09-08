from configuration import ADMINS, MOD_ROLES
from discord.ext import commands
from pathlib import Path
import os, sys, logging, uuid

"""
Core utilities
"""

def load_extension_directory(bot, ext):
    cmd_path = os.path.join(os.getcwd(), ext)
    for f in os.listdir(cmd_path):
        if f == '__init__.py' or not f.endswith('.py'):
            continue
        bot.load_extension('commands.{}'.format(Path(f).stem))


"""
Logging utilities
"""

def before_command_log(ctx):
    ctx.uuid = uuid.uuid1()
    logging.info('[{}] #{}/@{}: {}'.format(ctx.uuid, ctx.message.channel.id, ctx.author.id, ctx.message.content))

def command_error_log(ctx, error):
    logging.error('[{}] #{}/@{}: {}'.format(ctx.uuid, ctx.message.channel.id, ctx.author.id, error.text))


class LogCogMixin:
    async def cog_before_invoke(self, ctx):
        before_command_log(ctx)

    async def cog_command_error(self, ctx, error):
        command_error_log(ctx, error)

    async def cog_after_invoke(self, ctx):
        # TODO: figure out how to capture all messages sent and log them
        pass


"""
Auxiliary utilities
"""

def _is_bot_admin(user):
    return user.id in ADMINS

def is_bot_admin():
    """
    This is a command level check for bot administrators
    """
    def predicate(ctx):
        return _is_bot_admin(ctx.message.author)
    return commands.check(predicate)

def guild_moderator_roles():
    return MOD_ROLES

def _is_moderator(member):
    for r in member.roles:
        if r.id in MOD_ROLES:
            return True
    return False

def is_moderator():
    """
    This is a command level check for bot administrators
    """
    def predicate(ctx):
        return _is_moderator(ctx.message.author)
    return commands.check(predicate)
