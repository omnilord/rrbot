from sqlalchemy import Column, Boolean, BigInteger, String, DateTime, JSON, event
from . import Base
from configuration import update_live_prefix

class AdsMessages(Base):
    __tablename__ = 'ads_messages'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    # basic metadata about where this message is located
    server_id = Column(BigInteger, nullable=False)
    channel_id = Column(BigInteger, nullable=False)
    author_id = Column(BigInteger, nullable=False)

    # basic metadata about known times of this message
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)

    # if it was deleted, do we know by who (author or staff)
    deleted_by_id = Column(BigInteger, nullable=True, default=None)

    # if the message contains an invite, track details about the invite
    invite_code = Column(String(20), nullable=True, default=None)
    invite_server_id = Column(BigInteger, nullable=True, default=None)
    invite_server_name = Column(String(255), nullable=True, default=None)
    invite_expires_at = Column(DateTime, nullable=True, default=None)
