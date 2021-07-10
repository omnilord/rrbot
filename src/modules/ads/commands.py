import logging
from discord.ext import commands
from bot_utils import _is_server_moderator, db_session
from db import AdsChannels, AdsMessages, AdsWarnings
from . import ads_report, ads_sync, ads_add_channel, ads_remove_channel, ads_warn, ads_webhook

logging.info('Loading `ads command`')

class AdsCog(commands.Cog, name='Ads Command'):
    def __init__(self, bot):
        self.bot = bot


    def cog_check(self, ctx):
        """
        Ensure that only listed administrators and moderators
        may manage advertising channels.
        """

        user = ctx.author
        server = ctx.guild
        logging.info('Moderator check: {}'.format(user.id))
        return _is_server_moderator(user, server)


    @commands.group(invoke_without_command=True, pass_context=True)
    @db_session(cog=True)
    async def ads(self, ctx):
        """
        The Ads Command is uses to manage ads channels.

        No provided parameters will yield a report of the state of ads
        consisting of a list of channels, states, and their basic statistics

        Additional paramters [add, remove, sync, warn, notify]
        will forward to the respective subcommand in the ads command group.
        """

        await ctx.send(ads_report(ctx))


    @ads.command(aliases=['sync', 'rebuild'])
    @db_session(cog=True)
    async def synchronize(self, ctx):
        """
        The Ads Synchronize command will loop through all monitored
        channels and rebuild the ads index to ensure it is current.
        """

        await ctx.send(ads_sync(ctx))


    @ads.command()
    @db_session(cog=True)
    async def add(self, ctx, channel_id, invites=None):
        """
        The Ads Add Channel command allows a moderator to add a
        channel to the monitoring queue.  If a truthy second parameter
        is added after the channel id, ads _must_ contain an invite.
        """

        await ctx.send(ads_add_channel(ctx, channel_id))


    @ads.command(aliases=['rem', 'del', 'delete'])
    @db_session(cog=True)
    async def remove(self, ctx, channel_id):
        """
        The Ads Remove Channel command allows a moderator to disable a
        channel from being monitored.  If a truthy second paramter is
        added after the channel id, removes all data associated with the
        channel from the database.
        """

        await ctx.send(ads_remove_channel(ctx, channel_id))


    @ads.command(aliases=['warning', 'warnings'])
    @db_session(cog=True)
    async def warn(self, ctx, message_id=None):
        """
        The Ads Warn command allows moderators to track information
        about the ads being warned, including private notes on the matter.
        """

        await ctx.send(ads_warning(ctx, message_id))


    @ads.command(aliases=['cntl', 'control', 'channel'])
    @db_session(cog=True)
    async def webhook(self, ctx, webhook_url):
        """
        Specify the channel used as a notification channel
        """

        await ctx.send(ads_webhook(ctx, webhook_url))


def setup(bot):
    bot.add_cog(AdsCog(bot))
