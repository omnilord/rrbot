from sqlalchemy import Column, Boolean, BigInteger, String, JSON, event
from sqlalchemy.orm import relationship
from . import Base, prefixed
from configuration import update_live_prefix

@prefixed
class Servers(Base):
    __tablename__ = 'servers'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    # override the Global prefix with a custom
    # prefix specific to this server
    prefix = Column(String(10), nullable=True)

    # Ignore interactions in server except where a channel
    # has specifically been voiced.  Useful when you want to
    # limit bot interactions to only a few channels
    muted = Column(Boolean, nullable=False, default=False)

    # Storing Ad-hoc data made easy
    jsondata = Column(JSON)

    # Important for displaying times
    timezone = Column(String(32), nullable=True, default='America/New_York')

    # relationships
    roles = relationship('Roles', back_populates='server')
    channels = relationship('Channels', back_populates='server')


@event.listens_for(Servers, 'after_update')
def receive_after_update(mapper, connection, server):
    update_live_prefix(server.id, server.prefix)

@event.listens_for(Servers, 'after_insert')
def receive_after_insert(mapper, connection, server):
    update_live_prefix(server.id, server.prefix)
