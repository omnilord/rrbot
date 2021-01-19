import logging
from configuration import DB_URL, LOG_LEVEL, PREFIXES
from sqlalchemy import create_engine, sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class BotDBError(Exception):
    pass

"""
wire up the the engine basic database stuff, and related functionality
"""
logging.debug("database url: `{}`".format(DB_URL))
engine = create_engine(DB_URL, echo = (LOG_LEVEL == 'DEBUG'))
engine.connect()
Session = sessionmaker(bind = engine)
bot_session = Session() # special session reserved for core bot functionality

def update_prefix(id, prefix):
    if prefix != PREFIXES.get(id, None):
        if prefix is None:
            PREFIXES.delete(id)
        else:
            PREFIXES[id] = prefix

def prefixed(cls):
    """
    decorator for classes that have a prefix token for commands
    """
    def prefixed(session):
        return session.query(cls).filter(sql.column('prefix').isnot(None)).all()
    cls.prefixed = prefixed
    return cls


"""
Load all the models
"""
Base = declarative_base()
from .Channels import Channels
from .Roles import Roles
from .Servers import Servers
from .Users import Users
from .Warnings import Warnings
from .AdsChannels import AdsChannels
from .AdsMessages import AdsMessages
from .AdsWarnings import AdsWarnings

"""
The all-important session functionality
"""

def db_test():
    # TODO: make sure the engine connects
    # raise BotDBError if no connection
    pass


"""
utilities
"""

def get_or_create(session, model, **kwargs):
    """
    A fetch or create function for ensure methods
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
    return instance

def ensure_channel(session, id):
    return get_or_create(session, Channels, id=id)

def ensure_channels(session, ids):
    return [(id, ensure_channel(session, id)) for id in ids]

def ensure_server(session, id):
    return get_or_create(session, Servers, id=id)

def ensure_servers(session, ids):
    return [(id, ensure_server(session, id)) for id in ids]

def ensure_role(session, id):
    return get_or_create(session, Roles, id=id)

def ensure_roles(session, ids):
    return [(id, ensure_role(session, id)) for id in ids]

def ensure_user(session, id):
    return get_or_create(session, Users, id=id)

def ensure_users(session, ids):
    return [(id, ensure_user(session, id)) for id in ids]
