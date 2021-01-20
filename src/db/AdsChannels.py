from sqlalchemy import Column, Boolean, BigInteger, String, DateTime, JSON
from . import Base
from datetime import datetime

class AdsChannels(Base):
    __tablename__ = 'ads_channels'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    server_id = Column(BigInteger, nullable=False)

    # display name of the channel (may differ from the discord name)
    name = Column(String(255), nullable=True)

    # is this channel for server ads (True) or personal ads (False)
    invites = Column(Boolean, nullable=False, default=True)

    # is this channel currently reporting ads (None means disabled)
    webhook_url = Column(String(255), nullable=True, default=None)

    # preserve this channel for auditing but mark as gone
    deleted_at = Column(DateTime, nullable=True, default=None)

    # Storing Ad-hoc data made easy
    jsondata = Column(JSON)

    def delete(self):
        self.webhook_url = None
        self.deleted_at = datetime.now()

    def discord_channel(self, bot):
        try:
            return self.discord_channel
        except AttributeError:
            if bot is None:
                return None
            self.discord_channel = bot.get_channel(self.id)
            return self.discord_channel



def is_active_ads_channel(session, channel):
    # TODO: query for WHERE id=channel.id AND active=True
    pass
