from db import (
    UTC_TZ,
    AdsMessages,
    Session
)
from datetime import datetime, timedelta
from discord import Webhook, AsyncWebhookAdapter
import aiohttp, asyncio, logging, timeago
from bot_utils import get_tz, bot_fetch


OUTPUT_DATETIME_FORMAT = '%A, %D at %T%p %Z'


# These are temporary templates, planning to migrate to embeds at a later date.
# INVITE TEMPLATES
NO_INVITE_PROVIDED = "\nNO INVITE PROVIDED.\n"
GOOD_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
invite: {invite.url}
"""
BAD_INVITE_TEMPLATE = """
server: `{ad.invite_server_name}`
**INVITE HAS EXPIRED**
"""
EXTRA_INVITES_TEMPLATE = 'There were {ad.invite_code} invites attached to this ad.'

# TIMING TEMPLATES
USER_LAST_POST = 'User last post {ta} on {ts} for {s}'
SERVER_LAST_POST = 'Server last posted {ta} on {ts} by <@{u}>'

# MESSAGE TEMPLATES
NEW_MESSAGE_TEMPLATE = """
{ts}
Channel: {channel_name} ({channel})
Author: {author}
{invite}
{timers}
Message ID: {id}
{url}
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
def time_labels_from_utc(field, tz):
    field_utc = field.replace(tzinfo=UTC_TZ)
    ta = timeago.format(field_utc, datetime.utcnow().replace(tzinfo=UTC_TZ))
    ts = field_utc.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT)
    return (ta, ts)


async def render_invite(bot, ad, tz):
    if ad.invite_count == 0:
        return NO_INVITE_PROVIDED
    elif ad.invite_count == 1:
        invite = await bot_fetch(bot.fetch_invite, ad.invite_code)
        if invite is None:
            return BAD_INVITE_TEMPLATE.format(ad=ad)
        return GOOD_INVITE_TEMPLATE.format(ad=ad, invite=invite)
    return EXTRA_INVITES_TEMPLATE.format(ad=ad)


def render_timers(db_session, ad, tz):
    output = []

    # Check the timing on the last post by this user in the
    #   same channel.
    past_user = AdsMessages.most_recent_user_ad(db_session, ad)
    if past_user is None:
        user_str = None
    else:
        #created_at = past_user.created_at.replace(tzinfo=UTC_TZ)
        #ta = timeago.format(created_at, datetime.utcnow().replace(tzinfo=UTC_TZ))
        #ts = created_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT)
        ta, ts = time_labels_from_utc(past_user.created_at, tz)
        if past_user.invite_server_name is None:
            server_name = '_unknown_'
        else:
            server_name = past_user.invite_server_name
        output.append(USER_LAST_POST.format(ta=ta, ts=ts, s=server_name))

    # Check the timing on the last post for this server in the
    #   same channel
    past_server = AdsMessages.most_recent_server_ad(db_session, ad)
    if past_server is None:
        server_str = None
    elif past_server != past_user:
        #created_at = past_server.created_at.replace(tzinfo=UTC_TZ)
        #ta = timeago.format(created_at, datetime.utcnow().replace(tzinfo=UTC_TZ))
        #ts = created_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT)
        ta, ts = time_labels_from_utc(past_server.created_at, tz)
        output.append(SERVER_LAST_POST.format(ta=ta, ts=ts, u=past_server.author_id))

    return '\n'.join(output).strip()


async def render_new_ad(bot, db_session, ad, message, channel, tzone_name=None):
    tz = get_tz(tzone_name)
    invite = await render_invite(bot, ad, tz)
    timers = render_timers(db_session, ad, tz)
    return NEW_MESSAGE_TEMPLATE.format(
        ts=datetime.now(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=message.author.mention,
        channel=message.channel.mention,
        invite=invite,
        timers=(timers+'\n' if timers else ''),
        id=ad.id,
        url=message.jump_url
    )


async def render_ad_deleted(bot, ad, channel, tzone_name=None):
    tz = get_tz(tzone_name)
    invite = await render_invite(bot, ad, tz)
    return DELETED_MESSAGE_TEMPLATE.format(
        ts=ad.deleted_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=f"<@{ad.author_id}> (id: {ad.author_id})",
        channel=f"<#{channel.id}>",
        invite=invite,
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