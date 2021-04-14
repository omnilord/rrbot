from sqlalchemy import Column, Boolean, BigInteger, String, DateTime, JSON, inspect
from . import Base, AdsMessages
from datetime import datetime


class AdsChannels(Base):
    __tablename__ = 'ads_channels'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    server_id = Column(BigInteger, nullable=False)

    # display name of the channel (admin-configurable, may differ from the discord name)
    name = Column(String(255), nullable=True)

    # is this channel for server ads (True) or personal ads (False)
    invites = Column(Boolean, nullable=False, default=True)

    # is this channel currently reporting ads (None means disabled)
    webhook_url = Column(String(255), nullable=True, default=None)

    # preserve this channel for auditing but mark as gone
    deleted_at = Column(DateTime, nullable=True, default=None)

    # Storing Ad-hoc data made easy
    jsondata = Column(JSON)

    def delete_ads(self):
        AdsMessages.delete_all(inspect(self).session, channel_id=self.id)

    def delete(self):
        self.delete_ads()
        # self.webhook_url = None # need webhook _after_ the channel is deleted for notify
        self.deleted_at = datetime.now()

    def discord_channel(self, bot):
        try:
            return self._discord_channel
        except AttributeError:
            self._discord_channel = bot.get_channel(self.id)
            if self._discord_channel is None:
                self.delete()
            return self._discord_channel

    async def reindex(self, bot):
        d_chan = self.discord_channel(bot)

        index = { 'new': [], 'edited': [], 'deleted': [] }

        end = None
        async for m in d_chan.history(limit=1):
            end = m

        edits = []
        if end is None:
            # All the messages were removed, but the channel remains
            self.delete_ads()
        else:
            last = None
            while last != end:
                async for m in d_chan.history(after=last, limit=100, oldest_first=True):
                    last = m
                    edits.append(m.id)

            # TODO: update messages in database to deleted_at=NOW()
            #       where not in index and created_at < end.created_at;
            #       if there is no index of the message, it was deleted,
            #       but we only want to do messages before we cut off (end.created_at)
            # TODO: if a message is found in discord that has a deleted_at datetime,
            #       update deleted_at to null.

        return index


    def one_channel(db_session, channel_id):
        return db_session.query(AdsChannels).get(channel_id)


    def all(db_session, server_id=None, exclude_deleted=False):
        query = db_session.query(AdsChannels)
        if exclude_deleted:
            return query.filter(AdsChannels.deleted_at == None)
        return query
