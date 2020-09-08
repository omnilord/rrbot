from discord.ext import commands
from database import DB
from bot_utils import LogCogMixin, guild_moderator_roles
import logging, uuid

logging.info('Loading `moderation commands`')

class ModCog(LogCogMixin, commands.Cog, name='Bot Administrator Commands'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx):
        pass

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx):
        pass

    @commands.command()
    @commands.has_any_role(*guild_moderator_roles)
    async def warn(self, ctx):
        pass

def setup(bot):
    bot.add_cog(ModCog(bot))
