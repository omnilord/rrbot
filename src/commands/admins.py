import logging
from discord.ext import commands
from bot_utils import _is_bot_admin, db_session
from db import ensure_server, ensure_channel

logging.info('Loading `admin commands`')

class AdminCog(commands.Cog, name='Bot Administrator Commands'):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        """
        This checks to ensure only listed administrators can execute the commands in this cog.
        """
        id = ctx.message.author.id
        logging.info('Administrator check: {}'.format(id))
        logging.info(ctx.message.content)
        return _is_bot_admin(id)

    @commands.command()
    async def shutdown(self, ctx):
        await ctx.send('Goodbye')
        await ctx.bot.close()

    @commands.command(aliases=['sprefix'])
    @db_session(cog=True)
    async def prefix(self, ctx, prefix):
        server = ensure_server(ctx.db, ctx.guild.id)
        server.prefix = prefix
        ctx.db.add(server)
        ctx.db.commit()
        await ctx.send('Server prefix is now {}'.format(prefix))

    @commands.command()
    @db_session(cog=True)
    async def cprefix(self, ctx, prefix):
        channel = ensure_channel(ctx.db, ctx.channel.id, ctx.guild.id)
        channel.prefix = prefix
        ctx.db.add(channel)
        ctx.db.commit()
        await ctx.send('{} prefix is now {}'.format(ctx.channel.mention, prefix))

def setup(bot):
    bot.add_cog(AdminCog(bot))
