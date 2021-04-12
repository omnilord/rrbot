from sqlalchemy import Column, Boolean, BigInteger, String, DateTime, JSON, event
from . import Base

class AdsWarnings(Base):
    __tablename__ = 'ads_warnings'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    # which message is this warning attached to?
    ads_message_id = Column(BigInteger, nullable=False)

    # Author of ad message
    author_id = Column(BigInteger, nullable=False)

    # basic metadata about known times of this warning
    created_at = Column(DateTime, nullable=False)
    created_by_id = Column(BigInteger, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(BigInteger, nullable=True)

    # additional ad-hoc data about the warning, including:
    # { "notes": [ { "user_id": #, "created_at": "", "note": "" } ] }
    jsondata = Column(JSON)
