import logging
from discord.ext import commands
from bot_utils import _is_server_moderator, db_session

logging.info('Loading `ads command`')

def ads_add_channel(ctx, channel_id):
    return 'Needs new channel'

def ads_remove_channel(ctx, channel_id):
    return 'Needs old channel'

def ads_sync(ctx):
    return 'Needs data'

def ads_report(ctx):
    return 'Report!'


class AdsCog(commands.Cog, name='Ads Command'):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        """
        Ensure that only listed administrators and moderators
        may manage advertising channels.
        """
        user = ctx.message.author
        logging.info('Moderator check: {}'.format(user.id))
        logging.info(ctx.message.content)
        return _is_server_moderator(user)

    @commands.group(invoke_without_command=True, pass_context=True)
    @db_session(cog=True)
    async def ads(self, ctx):
        """
        The Ads Command is uses to manage server-ads channels.
        """
        await ctx.send(ads_report(ctx))

    @ads.group(aliases=['sync', 'rebuild'])
    @db_session(cog=True)
    async def synchronize(self, ctx):
        await ctx.send(ads_sync(ctx))

    @ads.group()
    @db_session(cog=True)
    async def add(self, ctx, channel_id):
        await ctx.send(ads_add_channel(ctx, channel_id))

    @ads.group(aliases=['rem'])
    @db_session(cog=True)
    async def remove(self, ctx):
        await ctx.send(ads_remove_channel(ctx, channel_id))


def setup(bot):
    bot.add_cog(AdsCog(bot))
