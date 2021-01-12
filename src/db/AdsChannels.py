from sqlalchemy import Column, Boolean, BigInteger, String, JSON, event
from . import Base

class AdsChannels(Base):
    __tablename__ = 'ads_channels'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    server_id = Column(BigInteger, nullable=False)

    # display name of the channel (may differ from the discord name)
    name = Column(String(255), nullable=True)

    # is this channel for server ads (True) or personal ads (False)
    invites = Column(Boolean, nullable=False, default=True)

    # is this channel currently being tracked
    active = Column(Boolean, nullable=False, default=False)

    # Storing Ad-hoc data made easy
    jsondata = Column(JSON)
