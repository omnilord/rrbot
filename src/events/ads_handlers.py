from db import (
    AdsChannels,
    AdsMessages,
    Session,
    ensure_server
)
from datetime import datetime
from zoneinfo import ZoneInfo
from discord import Webhook, AsyncWebhookAdapter
import aiohttp, asyncio

OUTPUT_DATETIME_FORMAT = '%A, %D %T%p %Z'

# These are temporary templates, planning to migrate to embeds at a later date.
NO_INVITE_PROVIDED = "\nNO INVITE.\n"
GOOD_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
expires: `{expires_at}`
"""
BAD_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
**INVITE HAS EXPIRED**
"""
EXPIRING_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
_**expiring soon: `{expires_at}**_`
"""
EXTRA_INVITES_TEMPLATE = 'There were {ad.invite_code} invites attached to this ad.'
NEW_MESSAGE_TEMPLATE = """
{ts} in {channel_name}
Author: `{author}`
Channel: {channel}
{invite}
{timers}
Message: {url}
"""
DELETED_MESSAGE_TEMPLATE = """
'<todo: what info when an ad is deleted...>'
"""
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
            alart_at = ad.invite_expires_at - timedelta(days=1)
            good = alert_at <= datetime.today()
            expires = ad.invite_expires_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT)

        if not good:
            return EXPIRING_INVITE_TEMPLATE.format(ad=ad, expires=expires)
        else:
            return GOOD_INVITE_TEMPLATE.format(ad=ad, expires=expires)
    else:
        return EXTRA_INVITES_TEMPLATE.format(ad=ad)


def render_timer():
    return '<todo: in specific ads channel, last post for server, last post by this user>'


def render_ad_notice(ad, message, channel, tzone_name=None):
    tz = get_tz(tzone_name)
    return NEW_MESSAGE_TEMPLATE.format(
        ts=datetime.now(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=message.author.mention,
        channel=message.channel.jump_url,
        invite=render_invite(ad, tz),
        timers=render_timers(ad, tz),
        url=message.jump_url
    )

def render_ad_deleted(ad, tzone_name=None):
    return DELETED_MESSAGE_TEMPLATE.format(ad=ad)

def render_channel_deleted(channel, count, tzone_name=None):
    return DELETED_CHANNEL_TEMPLATE.format(name=channel.name, count=count)


async def send_notify(msg, channel, db_session, username='RR Bot'):
    """
    Call the webhook associated with the channel to create a
    notification message.
    """
    if channel.webhook_url is None:
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
    print('Loading `on_ready` listener for ads handler')
    @bot.listen()
    async def on_ready():
        # TODO: step 1 - verify ads_channels are still present, set deleted otherwise
        # TODO: foreach present channel in ads_channels process all messages for update
        #    messages = channel.history(limit=None, oldest_first=True)
        pass


    print('Loading `on_message` listener for ads handler')
    @bot.listen()
    async def on_message(message):
        db_session = Session()
        channel = db_session.query(AdsChannels).filter_by(id = message.channel.id).one_or_none()

        if channel is not None:
            ad = await AdsMessages.from_discord_message(db_session, message)
            server = db.ensure_server(db_session, message.guild.id)
            notice = render_ad_notice(ad, message, channel, server.timezone)
            await send_notify(notice, channel, db_session, 'New Ad')

        db_session.close()


    print('Loading `on_raw_message_edit` listener for ads handler')
    @bot.listen()
    async def on_raw_message_edit(message):
        # TODO: call ads_messages.edit(message) if message.channel in ads.channels
        #    this call _really_ needs to debounce on send_notify such that only
        #    one notification is set to control every 2 or 3 minutes if someone is
        #    repeatedly editing an ad message.
        pass


    print('Loading `on_raw_message_delete` listener for ads handler')
    @bot.listen()
    async def on_raw_message_delete(message):
        db_session = Session()
        ad = db_session.query(AdsMessages).filter_by(id=message.id).one_or_none()

        if ad is not None:
            ad.delete()
            db_session.commit()
            server = db.ensure_server(db_session, message.guild.id)
            notice = render_ad_deleted(ad, server.timezone)
            await send_notify(notice, channel, db_session, 'Ad Deleted')
            
        db_session.close()


    print('Loading `on_guild_channel_delete` listener for ads handler')
    @bot.listen()
    async def on_guild_channel_delete(d_channel):
        db_session = Session()
        channel = db_session.query(AdsChannels).filter_by(id=d_channel.id).one_or_none()

        if channel is not None:
            ads = db_session.query(AdsMessages).filter_by(channel_id=channel.id, deleted_at=None)
            ads_count = ads.count()
            channel.delete()
            ads.update({ 'deleted_at': channel.deleted_at })
            db_session.commit()
            server = db.ensure_server(db_session, message.guild.id)
            notice = render_channel_deleted(channel, ads_count, server.timezone)
            await send_notify(notice, channel, db_session, 'Channel Deleted')

        db_session.close()


    print('Loading `on_member_remove` listener for ads handler')
    @bot.listen()
    async def on_member_remove(member):
        # TODO check for ads by this member, then notify
        pass
