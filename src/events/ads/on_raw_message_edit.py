import logging, asyncio, task_scheduler as tasker
from db import (
    AdsMessages,
    AdsChannels,
    Session,
    ensure_server
)
from . import render_ad_edited, notify_ad_webhook, delete_ad_notification
from bot_utils import bot_fetch, pp


def setup(bot):
    logging.info('Loading `on_raw_message_edit` listener for ads handler')

    @bot.listen()
    async def on_raw_message_edit(payload):
        db_session = Session()
        ad = AdsMessages.one_message(db_session, payload.message_id)
        channel = AdsChannels.one_channel(db_session, payload.channel_id)

        # REFACTOR: we get an edit on a message that was missed by on_message
        #           how do we _create_ the ad once instead if the create event
        #           comes in asynchronously somehow?

        if channel is not None and ad is not None:
            d_channel = await bot_fetch(bot.fetch_channel, payload.channel_id)
            message = payload.cached_message if payload.cached_message is not None else await bot_fetch(d_channel.fetch_message, payload.message_id)

            if diffs := await ad.amend(bot, message):
                db_session.commit()
                server = ensure_server(db_session, channel.server_id)
                notice = await render_ad_edited(bot, db_session, ad, message, channel, diffs, server.timezone)
                #key = f'edit_message_{ad.id}'
                #message = await tasker.asyncregister(notify_ad_webhook, notice, channel, 'Ad Edited', key=key, delay=30)
                await asyncio.sleep(30)
                notice_message = await notify_ad_webhook(notice, channel, 'Ad Edited')
                if ad.last_notice_id is not None:
                    await delete_ad_notification(channel, ad.last_notice_id)
                ad.last_notice_id = notice_message.id
                db_session.commit()
            else:
                # TODO: render_ad_edited_content_only(...)?
                pass

        db_session.close()
