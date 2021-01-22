import logging
from db import (
    AdsChannels,
    AdsMessages,
    Session,
    ensure_server
)
from . import render_new_ad, send_notify


def setup(bot):
    logging.info('Loading `on_message` listener for ads handler')

    @bot.listen()
    async def on_message(message):
        if message.author.id == bot.user.id:
            return

        db_session = Session()
        channel = db_session.query(AdsChannels).filter_by(id = message.channel.id).one_or_none()

        if channel is not None:
            ad = await AdsMessages.from_discord_message(db_session, bot, message)
            db_session.add(ad)
            db_session.commit()
            server = ensure_server(db_session, message.guild.id)
            notice = await render_new_ad(bot, db_session, ad, message, channel, server.timezone)
            await send_notify(notice, channel, db_session, 'New Ad')

        db_session.close()
