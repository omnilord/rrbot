import logging
from db import (
    UTC_TZ,
    AdsMessages,
    AdsChannels,
    Session
)
from . import render_channel_deleted, notify_ad_webhook


def setup(bot):
    logging.info('Loading `on_guild_channel_delete` listener for ads handler')

    @bot.listen()
    async def on_guild_channel_delete(discord_channel):
        db_session = Session()
        if channel := AdsChannels.one_channel(db_session, discord_channel.id):
            deleted_ads = channel.delete()
            db_session.commit()
            notice = render_channel_deleted(db_session, channel, len(deleted_ads))
            await notify_ad_webhook(notice, channel, 'Channel Deleted')
            db_session.commit()

        db_session.close()
