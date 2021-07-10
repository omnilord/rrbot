import logging
from db import (
    AdsChannels,
    AdsMessages,
    Session
)
from . import render_new_ad, notify_ad_webhook


def setup(bot):
    logging.info('Loading `on_message` listener for ads handler')

    @bot.listen()
    async def on_message(message):
        if message.author.id == bot.user.id:
            return

        db_session = Session()
        if channel := AdsChannels.one_channel(db_session, message.channel.id):
            ad = await AdsMessages.from_discord_message(db_session, bot, message)
            db_session.add(ad)
            db_session.commit()
            notice = await render_new_ad(bot, db_session, ad, message, channel)
            notice_message = await notify_ad_webhook(notice, channel, 'New Ad')
            ad.last_notice_id = notice_message.id
            db_session.commit()

        db_session.close()
