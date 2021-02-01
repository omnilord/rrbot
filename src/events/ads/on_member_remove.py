import logging


def setup(bot):
    logging.info('Loading `on_member_remove` listener for ads handler')

    @bot.listen()
    async def on_member_remove(member):
        if member.id == bot.user.id:
            return

        # TODO check for ads by this member, then notify
        # await notify_ad_webhook(notice, channel, db_session, 'Ad User Left Server')
        pass
