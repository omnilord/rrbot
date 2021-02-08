import logging, task_scheduler as tasker
from db import (
    UTC_TZ,
    AdsMessages,
    AdsChannels,
    Session,
    ensure_server
)
from . import render_ad_edited, notify_ad_webhook, diff_message
from bot_utils import bot_fetch


def setup(bot):
    logging.info('Loading `on_raw_message_edit` listener for ads handler')

    @bot.listen()
    async def on_raw_message_edit(payload):
        db_session = Session()
        ad = AdsMessages.one_message(db_session, payload.message_id)
        channel = AdsChannels.one_channel(db_session, payload.channel_id)

        if channel is not None and ad is not None:
            d_channel = await bot_fetch(bot.fetch_channel, payload.channel_id)
            message = payload.cached_message if payload.cached_message is not None else await bot_fetch(d_channel.fetch_message, payload.message_id)
            diffs = await diff_message(bot, ad, message, db_session)

            if diffs:
                ad.amend(**dict([(k,v[1]) for k,v in diffs.items()]))
                db_session.commit()
                server = ensure_server(db_session, channel.server_id)
                notice = await render_ad_edited(bot, db_session, ad, message, channel, diffs, server.timezone)
                key = f'edit_message_{ad.id}'
                tasker.register(notify_ad_webhook, notice, channel, db_session, 'Ad Edited', key=key, delay=30)

        db_session.close()
