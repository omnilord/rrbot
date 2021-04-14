import logging
from db import (
    UTC_TZ,
    AdsMessages,
    AdsChannels,
    Session,
    ensure_server
)
from . import render_channel_deleted, notify_ad_webhook


def setup(bot):
    logging.info('Loading `on_guild_channel_delete` listener for ads handler')

    @bot.listen()
    async def on_guild_channel_delete(discord_channel):
        db_session = Session()
        if channel := AdsChannels.one_channel(db_session, discord_channel.id):
            ads_count = AdsMessages.count(db_session, channel_id=channel.id, deleted_at=None)
            channel.delete()
            AdsMessages.delete_all(db_session, channel_id=channel.id, deleted_at=channel.deleted_at)
            db_session.commit()
            server = ensure_server(db_session, message.guild.id)
            notice = render_channel_deleted(channel, ads_count, server.timezone)
            await notify_ad_webhook(notice, channel, 'Channel Deleted')
            db_session.commit()

        db_session.close()
