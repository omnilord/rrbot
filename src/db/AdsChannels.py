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
        return AdsMessages.delete_all(inspect(self).session, channel_id=self.id, deleted_at=self.deleted_at)


    def delete(self):
        self.deleted_at = datetime.now()
        return self.delete_ads()
        # self.webhook_url = None # need webhook _after_ the channel is deleted for notify


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

        index = []

        end = None
        async for m in d_chan.history(limit=1):
            end = m

        if end is None:
            # All the messages were removed, but the channel remains
            if deleted := self.delete_ads():
                index.extend([ { 'action': 'deleted', 'ad': ad } for ad in deleted ])
                db_session.commit()
        else:
            last = None
            db_session = inspect(self).session
            while last != end:
                async for m in d_chan.history(after=last, limit=100, oldest_first=True):
                    last = m
                    if ad := AdsMessages.one_message(db_session, m.id):
                        # TODO deduplicate with on_raw_message_edit
                        if diff := await ad.amend(db_session, m):
                            index.append({ 'action': 'edited', 'ad': ad, 'message': m })
                            db_session.commit()
                    else:
                        # TODO deduplicate with on_message
                        ad = await AdsMessages.from_discord_message(db_session, bot, message)
                        db_session.add(ad)
                        index.append({ 'action': 'added', 'ad': ad, 'message': m })
                        db_session.commit()

            id_list = [mid for ad in index for mid in [ad['id'], ad['last_notice_id']] if mid is not None]
            if deleted := AdsMessages.delete_all(db_session, AdsMessages.id.not_in(id_list), AdsMessages.channel_id == self.id):
                index.extend([ { 'action': 'deleted', 'ad': ad } for ad in deleted ])
                db_session.commit()

        return index


    def one_channel(db_session, channel_id):
        return db_session.query(AdsChannels).get(channel_id)


    def all(db_session, server_id=None, exclude_deleted=False):
        query = db_session.query(AdsChannels)
        if exclude_deleted:
            return query.filter(AdsChannels.deleted_at == None)
        return query
