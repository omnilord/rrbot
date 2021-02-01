import logging
from db import (
    UTC_TZ,
    AdsMessages,
    AdsChannels,
    Session,
    ensure_server
)
from . import render_ad_deleted, notify_ad_webhook


def setup(bot):
    logging.info('Loading `on_raw_message_delete` listener for ads handler')

    @bot.listen()
    async def on_raw_message_delete(payload):
        db_session = Session()
        ad = AdsMessages.one_message(db_session, payload.message_id)

        if ad is not None:
            channel = AdsChannels.one_channel(db_session, payload.channel_id)
            ad.delete()
            db_session.commit()
            server = ensure_server(db_session, payload.guild_id)
            notice = await render_ad_deleted(bot, ad, channel, server.timezone)
            await notify_ad_webhook(notice, channel, db_session, 'Ad Deleted')

        db_session.close()
