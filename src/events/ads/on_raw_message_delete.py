import logging, task_scheduler as tasker
from db import (
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
        if ad := AdsMessages.one_message(db_session, payload.message_id):
            channel = AdsChannels.one_channel(db_session, payload.channel_id)
            ad.delete()
            db_session.commit()
            server = ensure_server(db_session, payload.guild_id)
            notice = await render_ad_deleted(bot, ad, channel, server.timezone)
            tasker.deregister(f'edit_message_{ad.id}')
            await notify_ad_webhook(notice, channel, 'Ad Deleted')
        else:
            # The deleted message _might_ be a notice, so just clear that
            AdsMessages.clear_notice(db_session, payload.message_id)

        db_session.close()
