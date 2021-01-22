from db import (
    AdsChannels,
    AdsMessages,
    Session,
    ensure_server
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from discord import Webhook, AsyncWebhookAdapter
import aiohttp, asyncio, logging, timeago


OUTPUT_DATETIME_FORMAT = '%A, %D at %T%p %Z'


# These are temporary templates, planning to migrate to embeds at a later date.
#INVITE TEMPLATES
NO_INVITE_PROVIDED = "\nNO INVITE.\n"
GOOD_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
expires: `{expires}`
"""
BAD_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
**INVITE HAS EXPIRED**
"""
EXPIRING_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
**expiring soon**: `{expires}`
"""
EXTRA_INVITES_TEMPLATE = 'There were {ad.invite_code} invites attached to this ad.'


# MESSAGE TEMPLATES
NEW_MESSAGE_TEMPLATE = """
{ts}
Channel: {channel_name} ({channel})
Author: {author}
{invite}
{timers}
Message: {url}
"""
EDITED_MESSAGE_TEMPLATED = """
<todo>
"""
DELETED_MESSAGE_TEMPLATE = """
{ts}
Channel: {channel_name} ({channel})
Author: {author}
{invite}
Message ID: {id}
"""


# CHANNEL TEMPLATES
DELETED_CHANNEL_TEMPLATE = 'Channel `{name}` was deleted with {count} active ads.'


# Notification rendering functions
def get_tz(tzone_name=None):
    if tzone_name is None:
        tzone_name = 'America/New_York'
    try:
        return ZoneInfo(tzone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo('America/New_York')


def render_invite(ad, tz):

    # If ad.invite_code is invalid
    # render BAD_INVITE_TEMPLATE
    if ad.invite_count == 0:
        return NO_INVITE_PROVIDED
    elif ad.invite_count == 1:
        if ad.invite_expires_at is None:
            good = True
            expires = 'No'
        else:
            alert_at = ad.invite_expires_at - timedelta(days=1)
            good = alert_at <= datetime.today()
            expires_exact = ad.invite_expires_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT)
            expires_at = timeago.format(ad.invite_expires_at)
            expires = f'{expires_at} on {expires_exact}'

        if not good:
            return EXPIRING_INVITE_TEMPLATE.format(ad=ad, expires=expires)
        else:
            return GOOD_INVITE_TEMPLATE.format(ad=ad, expires=expires)
    else:
        return EXTRA_INVITES_TEMPLATE.format(ad=ad)


def render_timers(ad, tz):
    return '<todo: in specific ads channel, last post for server, last post by this user>'


def render_new_ad(ad, message, channel, tzone_name=None):
    tz = get_tz(tzone_name)
    return NEW_MESSAGE_TEMPLATE.format(
        ts=datetime.now(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=message.author.mention,
        channel=message.channel.mention,
        invite=render_invite(ad, tz),
        timers=render_timers(ad, tz),
        url=message.jump_url
    )

def render_ad_deleted(ad, channel, bot, tzone_name=None):
    tz = get_tz(tzone_name)
    return DELETED_MESSAGE_TEMPLATE.format(
        ts=ad.deleted_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=f"<@{ad.author_id}> (id: {ad.author_id})",
        channel=f"<#{channel.id}>",
        invite=render_invite(ad, tz),
        id=ad.id
    )

def render_channel_deleted(channel, count, tzone_name=None):
    return DELETED_CHANNEL_TEMPLATE.format(name=channel.name, count=count)


async def send_notify(msg, channel, db_session, username='RR Bot'):
    """
    Call the webhook associated with the channel to create a
    notification message.
    """
    if channel is None or channel.webhook_url is None:
        return

    async with aiohttp.ClientSession() as wh_session:
        try:
            adapter = AsyncWebhookAdapter(wh_session)
            webhook = Webhook.from_url(channel.webhook_url, adapter=adapter)
            await webhook.send(msg, username=username)
        except (NotFound, Forbidden):
            channel.webhook_url = None
            db_session.commit()


"""
# the actual listeners are resolved on the bot itself at setup
"""

def setup(bot):
    logging.info('Loading `on_ready` listener for ads handler')

    @bot.listen()
    async def on_ready():
        # TODO: step 1 - verify ads_channels are still present, set deleted otherwise
        # TODO: foreach present channel in ads_channels process all messages for update
        #    messages = channel.history(limit=None, oldest_first=True)
        pass


    logging.info('Loading `on_message` listener for ads handler')

    @bot.listen()
    async def on_message(message):
        if message.author.id == bot.user.id:
            return

        db_session = Session()
        channel = db_session.query(AdsChannels).filter_by(id = message.channel.id).one_or_none()

        if channel is not None:
            ad = await AdsMessages.from_discord_message(db_session, message)
            db_session.add(ad)
            db_session.commit()
            server = ensure_server(db_session, message.guild.id)
            notice = render_new_ad(ad, message, channel, server.timezone)
            await send_notify(notice, channel, db_session, 'New Ad')

        db_session.close()


    logging.info('Loading `on_raw_message_edit` listener for ads handler')

    @bot.listen()
    async def on_raw_message_edit(message):
        if message.author.id == bot.user.id:
            return

        # TODO: call ads_messages.edit(message) if message.channel in ads.channels
        #    this call _really_ needs to debounce on send_notify such that only
        #    one notification is set to control every 2 or 3 minutes if someone is
        #    repeatedly editing an ad message.
        pass


    logging.info('Loading `on_raw_message_delete` listener for ads handler')

    @bot.listen()
    async def on_raw_message_delete(payload):
        db_session = Session()
        ad = db_session.query(AdsMessages).filter_by(id=payload.message_id).one_or_none()
        channel = db_session.query(AdsChannels).filter_by(id=payload.channel_id).one_or_none()

        if ad is not None:
            ad.delete()
            db_session.commit()
            server = ensure_server(db_session, payload.guild_id)
            notice = render_ad_deleted(ad, channel, bot, server.timezone)
            await send_notify(notice, channel, db_session, 'Ad Deleted')

        db_session.close()


    logging.info('Loading `on_guild_channel_delete` listener for ads handler')

    @bot.listen()
    async def on_guild_channel_delete(discord_channel):
        db_session = Session()
        channel = db_session.query(AdsChannels).filter_by(id=discord_channel.id).one_or_none()

        if channel is not None:
            ads = db_session.query(AdsMessages).filter_by(channel_id=channel.id, deleted_at=None)
            ads_count = ads.count()
            channel.delete()
            ads.update({ 'deleted_at': channel.deleted_at })
            db_session.commit()
            server = ensure_server(db_session, message.guild.id)
            #notice = render_channel_deleted(channel, ads_count, server.timezone)
            #await send_notify(notice, channel, db_session, 'Channel Deleted')

        db_session.close()


    logging.info('Loading `on_member_remove` listener for ads handler')

    @bot.listen()
    async def on_member_remove(member):
        if member.id == bot.user.id:
            return

        # TODO check for ads by this member, then notify
        pass
