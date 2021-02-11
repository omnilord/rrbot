from sqlalchemy import Column, Boolean, BigInteger, String, JSON, ForeignKey, event
from sqlalchemy.orm import relationship
from . import Base, prefixed
from configuration import update_live_prefix

@prefixed
class Channels(Base):
    __tablename__ = 'channels'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    # server
    server_id = Column(BigInteger, ForeignKey('servers.id'))
    server = relationship('Servers', back_populates="channels")

    # override the Global and Server prefixes with a custom
    # prefix specific to this channel
    prefix = Column(String(10), nullable=True)

    # Ignore interactions in this channel,
    # muted and voiced cannot both be True
    muted = Column(Boolean, nullable=False, default=False)

    # Specifically allow interactions in this channel
    # Only useful when server is globally muted such as
    # you only want 1 channel for bot interactions
    # muted and voiced cannot both be True
    voiced = Column(Boolean, nullable=False, default=False)

    # Storing Ad-hoc data made easy
    jsondata = Column(JSON)


@event.listens_for(Channels, 'after_update')
def receive_after_update(mapper, connection, channel):
    update_live_prefix(channel.id, channel.prefix)

@event.listens_for(Channels, 'after_insert')
def receive_after_insert(mapper, connection, channel):
    update_live_prefix(channel.id, channel.prefix)
