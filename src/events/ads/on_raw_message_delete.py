import logging
from db import (
    UTC_TZ,
    AdsMessages,
    AdsChannels,
    Session,
    ensure_server
)
from . import render_ad_deleted, send_notify


def setup(bot):
    logging.info('Loading `on_raw_message_delete` listener for ads handler')

    @bot.listen()
    async def on_raw_message_delete(payload):
        db_session = Session()
        ad = db_session.query(AdsMessages).filter_by(id=payload.message_id).one_or_none()
        channel = db_session.query(AdsChannels).filter_by(id=payload.channel_id).one_or_none()

        if ad is not None:
            ad.delete()
            db_session.commit()
            server = ensure_server(db_session, payload.guild_id)
            notice = await render_ad_deleted(bot, ad, channel, server.timezone)
            await send_notify(notice, channel, db_session, 'Ad Deleted')

        db_session.close()
