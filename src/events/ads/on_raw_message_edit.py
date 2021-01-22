import logging


def setup(bot):
    logging.info('Loading `on_raw_message_edit` listener for ads handler')

    @bot.listen()
    async def on_raw_message_edit(message):
        if message.author.id == bot.user.id:
            return

        # TODO: call ads_messages.edit(message) if message.channel in ads.channels
        #    this call _really_ needs to debounce on send_notify such that only
        #    one notification is set to control every 2 or 3 minutes if someone is
        #    repeatedly editing an ad message.
        pass
