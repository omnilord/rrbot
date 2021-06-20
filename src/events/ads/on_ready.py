import logging
from db import (
    AdsChannels,
    Session
)


def setup(bot):
    logging.info('Loading `on_ready` listener for ads handler')

    def added_handler(db_session, ad, message, **extras):
        print(ad, message)
        pass
    def edited_handler(db_session, ad, message, **extras):
        print(ad, message)
        pass
    def deleted_handler(db_session, ad, message, **extras):
        print(ad, message)
        pass

    ACTIONS = { 'added': added_handler, 'edited': edited_handler, 'deleted': deleted_handler }

    @bot.listen()
    async def on_ready():
        # TODO: step 1 - verify ads_channels are still present, set deleted otherwise
        # TODO: foreach present channel in ads_channels process all messages for update
        #    messages = channel.history(limit=None, oldest_first=True)

        db_session = Session()

        for channel in AdsChannels.all(db_session, exclude_deleted=True):
            if d_chan := channel.discord_channel(bot):
                reindex = await channel.reindex(bot)
                for message in reindex:
                    ACTIONS.get(message['action'], lambda : None)(**message)
            else: # Channel no longer exists.
                #notice = render_channel_reindexed(channel, ads_count, server.timezone)
                # TODO: deduplicate this with on_guild_channel_delete by creating relationships in models
                ads_count = AdsMessages.delete_all(db_session, channel_id=channel.id, deleted_at=channel.deleted_at)
                db_session.commit()
                server = ensure_server(db_session, server.id)
                notice = render_channel_deleted(channel, ads_count, server.timezone)
                await notify_ad_webhook(notice, channel, 'Channel Deleted')
                db_session.commit()

