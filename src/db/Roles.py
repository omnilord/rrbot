from sqlalchemy import Column, Boolean, BigInteger, String, JSON
from . import Base

class Roles(Base):
    __tablename__ = 'roles'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    # Allows this role to interact with this bot even if a
    # channel or server are muted.
    # muted and voiced cannot both be True
    voiced = Column(Boolean, nullable=False, default=False)

    # Prevents this role from interacting with the bot at all.
    # muted and voiced cannot both be True
    muted = Column(Boolean, nullable=False, default=False)

    # Specifies this role as able to use moderation all tools
    moderator = Column(Boolean, nullable=False, default=False)

    # Storing Ad-hoc data made easy
    jsondata = Column(JSON)
