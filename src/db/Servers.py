from sqlalchemy import ForeignKey, Column, Boolean, BigInteger, String, JSON, event
from . import Base, prefixed, bot_session
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


@event.listens_for(Servers, 'after_update')
def receive_after_update(mapper, connection, server):
    update_live_prefix(server.id, server.prefix)

@event.listens_for(Servers, 'after_insert')
def receive_after_insert(mapper, connection, server):
    update_live_prefix(server.id, server.prefix)
