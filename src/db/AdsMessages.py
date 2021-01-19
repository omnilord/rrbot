from sqlalchemy import Column, Boolean, BigInteger, Integer, String, DateTime, JSON
from . import Base
from configuration import update_live_prefix
from discord import NotFound
from datetime import datetime
import re

class AdsMessages(Base):
    __tablename__ = 'ads_messages'
    id = Column(BigInteger, primary_key = True, autoincrement=False)

    # basic metadata about where this message is located
    channel_id = Column(BigInteger, nullable=False)
    server_id = Column(BigInteger, nullable=False)
    author_id = Column(BigInteger, nullable=False)

    # basic metadata about known times of this message
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True, default=None)
    deleted_at = Column(DateTime, nullable=True, default=None)

    # if it was deleted, do we know by who (author or staff)
    deleted_by_id = Column(BigInteger, nullable=True, default=None)

    # if the message contains an invite, track details about the invite
    invite_count = Column(Integer, nullable=False, default=0)
    invite_code = Column(String(20), nullable=True, default=None)
    invite_server_id = Column(BigInteger, nullable=True, default=None)
    invite_server_name = Column(String(255), nullable=True, default=None)
    invite_expires_at = Column(DateTime, nullable=True, default=None)

    def delete(self, who_id=None):
        self.deleted_at = datetime.now()
        self.delete_by_id = who_id


    async def invite_from_discord_message(message):
        regexp = re.compile('https?://(?:discord.gg|(?:discord|discordapp).com/invite)/(?P<code>\w+)')
        invites = re.findall(regexp, message.content)
        data = {
            'invite_count': len(invites),
            'invite_code': None,
            'invite_server_id': None,
            'invite_server_name': None,
            'invite_expires_at': None
        }
        if len(invites) == 1:
            try:
                code = invites[0]('code')
                invite = await message.bot.fetch_invite(code)
                dt = None if invite.max_age == 0 else datetime.now() + invite.max_age
                data['invite_code'] = invite.id
                data['invite_server_id'] = invite.guild.id
                data['invite_server_name'] = invite.guild.name
                data['invite_expires_at'] = dt
            except NotFound:
                pass
        return data


    def fields_from_discord_message(message):
        return {
            id: message.id,
            server_id: message.server.id,
            channel_id: message.channel.id,
            author_id: message.author.id,
            created_at: message.created_at,
            updated_at: message.edited_at,
            **invite_from_discord_message(message)
        }


    async def from_discord_message(session, message):
        fields = await fields_from_discord_message(message)
        instance = session.query(AdsMessages).filter_by(id=message.id).first()
        if not instance:
            instance = AdsMessages(fields)
        elif instance.updated_at != fields['updated_at']:
            instance.amend(fields)
        return instance


    def amend(self, fields):
        updates = 0
        for key, value in kwargs.items():
            if hasattr(self, key) and getattr(self, key) != value:
                updates += 1
                setattr(self, key, value)
