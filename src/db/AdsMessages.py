from sqlalchemy import Column, Boolean, BigInteger, Integer, String, DateTime, JSON
from . import Base
from configuration import update_live_prefix
from discord import NotFound
from datetime import datetime, timedelta, timezone
import re
from bot_utils import bot_fetch

AGE_GATE_REGEXP = re.compile(r'(\d{2})\+')
NOTIFY_ON_EDIT = (
    'age_gate',
    'invite_code',
    'invite_count',
    'invite_server_id',
    'invite_server_name'
)

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
    invite_server_name = Column(String(100), nullable=True, default=None)
    invite_expires_at = Column(DateTime, nullable=True, default=None)

    # for RR, all ads should have 18+ age (adults only) constraint; store the age values found.
    age_gate = Column(String(50), nullable=True)

    # what was the last notification message sent to control for this ad
    last_notice_id = Column(BigInteger, nullable=True, default=None)


# INSTANCE METHODS

    def has_valid_age_gate(self):
        if self.age_gate is None:
            return (False, None)

        ages = [int(age) for age in AGE_GATE_REGEXP.findall(self.age_gate)]
        return (len(ages) == 1 and ages[0] >= 18, ages)

    def delete(self, who_id=None):
        self.deleted_at = datetime.now()
        self.delete_by_id = who_id

    async def discord_author(self, bot):
        try:
            return self.discord_author
        except AttributeError:
            self.discord_author = await bot_fetch(bot.fetch_user, self.author_id)
            return self.discord_author

    async def discord_channel(self, bot):
        try:
            return self.discord_channel
        except AttributeError:
            self.discord_channel = await bot_fetch(bot.fetch_channel, self.id)
            return self.discord_channel

    async def discord_server(self, bot):
        try:
            return self.discord_server
        except AttributeError:
            self.discord_server = await bot_fetch(bot.fetch_guild, self.guild_id)
            return self.discord_server

    async def discord_invite(self, bot):
        try:
            return self.invite
        except AttributeError:
            self.invite = await bot_fetch(bot.fetch_invite, self.invite_code)

    def valid_change(self, k, v):
        return k in NOTIFY_ON_EDIT and  v != getattr(self, k)

    async def diff_message(self, bot, message):
        """
        parse the message content and diff the new parsed data
        with the stored data from the last incarnation of this
        ad.

        returns:
        list(tuple(key, old value, new value))
        """

        if message is None:
            return

        new_fields = await AdsMessages.fields_from_discord_message(bot, message)
        for k, v in new_fields.items():
            if self.valid_change(k, v):
                yield (k, (getattr(self, k), v))

    async def amend(self, bot, message):
        """
        process provided fields for updating the instance if necessary
        """

        diffs = {}
        async for k, v in self.diff_message(bot, message):
            if hasattr(self, k) and getattr(self, k) != v:
                diffs[k] = v
                setattr(self, k, v[1])

        return diffs


# CLASS METHODS

    def parse_age_gate(message):
        """
        A super naive method for determining if an ad has an
        age flag or not.  This is not error-proof, nor exhaustive
        but it should find most 18+ flags, or give feedback on
        whether the ad contains proper age gate notices.
        """

        ages = AGE_GATE_REGEXP.findall(message)
        if len(ages) == 0:
            return None
        else:
            return '+, '.join(ages)+'+'


    async def invite_from_discord_message(bot, message):
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
            code = invites[0]
            invite = await bot_fetch(bot.fetch_invite, code)
            if invite is not None:
                data['invite_code'] = invite.id
                data['invite_server_id'] = invite.guild.id
                data['invite_server_name'] = invite.guild.name
                if invite.max_age is not None and invite.max_age > 0:
                    delta = timedelta(seconds=invite.max_age)
                    data['invite_expires_at'] = datetime.now() + delta
        return data


    async def fields_from_discord_message(bot, message):
        invite_data = await AdsMessages.invite_from_discord_message(bot, message)
        return {
            'id': message.id,
            'server_id': message.guild.id,
            'channel_id': message.channel.id,
            'author_id': message.author.id,
            'created_at': message.created_at,
            'updated_at': message.edited_at,
            'age_gate': AdsMessages.parse_age_gate(message.content),
            **invite_data
        }


    async def from_discord_message(db_session, bot, message, fields=None):
        if fields is None:
            fields = await AdsMessages.fields_from_discord_message(bot, message)
        instance = AdsMessages.one_message(db_session, message.id)
        if not instance:
            instance = AdsMessages(**fields)
        elif instance.updated_at != fields['updated_at']:
            instance.amend(**fields)
        return instance


    def most_recent_user_ad(db_session, ad):
        return db_session.query(AdsMessages).filter(
            AdsMessages.id!=ad.id,
            AdsMessages.channel_id==ad.channel_id,
            AdsMessages.author_id==ad.author_id
        ).order_by(AdsMessages.created_at.desc()).first()


    def most_recent_server_ad(db_session, ad):
        return db_session.query(AdsMessages).filter(
            AdsMessages.id!=ad.id,
            AdsMessages.channel_id==ad.channel_id,
            AdsMessages.invite_server_id==ad.invite_server_id
        ).order_by(AdsMessages.created_at.desc()).first()


    def one_message(db_session, message_id):
        return db_session.query(AdsMessages).get(message_id)


    def clear_notice(db_session, message_id):
        db_session.query(AdsMessages) \
            .filter(AdsMessages.last_notice_id==message_id) \
            .update({ AdsMessages.last_notice_id: None })



    def delete_all(db_session, channel_id, deleted_ts=datetime.now, *additional_filters):
        filters = [
            AdsMessages.channel_id==channel_id,
            AdsMessages.deleted_at==None,
            *addtional_filters
        ]
        ads = db_session.query(AdsMessages).filter(*filters).all()
        if len(ads) > 0:
            ads_ids = [ad.id for ad in ads]
            db_session.query(AdsMessages).filter(AdsMessages.id.in_(ads_ids)).update({
                AdsMessages.deleted_at: deleted_ts() if callable(deleted_ts) else deleted_ts
            })

        return ads


    def count(db_session, *filter):
        return db_session.query(AdsMessages).filter(*filter).count()
