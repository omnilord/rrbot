import logging
from db import (
    UTC_TZ,
    AdsMessages,
    AdsChannels,
    Session,
    ensure_server
)
from . import render_channel_deleted, send_notify


def setup(bot):
    logging.info('Loading `on_guild_channel_delete` listener for ads handler')

    @bot.listen()
    async def on_guild_channel_delete(discord_channel):
        db_session = Session()
        channel = db_session.query(AdsChannels).filter_by(id=discord_channel.id).one_or_none()

        if channel is not None:
            ads = db_session.query(AdsMessages).filter_by(channel_id=channel.id, deleted_at=None)
            ads_count = ads.count()
            channel.delete()
            ads.update({ 'deleted_at': channel.deleted_at })
            db_session.commit()
            server = ensure_server(db_session, message.guild.id)
            #notice = render_channel_deleted(channel, ads_count, server.timezone)
            #await send_notify(notice, channel, db_session, 'Channel Deleted')

        db_session.close()
