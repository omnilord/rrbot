from db import (
    UTC_TZ,
    AdsMessages,
    ensure_server
)
from datetime import datetime, timedelta
from discord import Webhook, AsyncWebhookAdapter, NotFound, Forbidden
import aiohttp, asyncio, logging, timeago
from bot_utils import get_tz, bot_fetch
from contextlib import asynccontextmanager


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
Age Gate: {age_gate}
{invite}
{timers}
Message ID: {id}
{url}
"""
EDITED_MESSAGE_TEMPLATE = """
{ts}
Channel: {channel_name} ({channel})
Author: {author}
Age Gate: {age_gate}{ag_edited}
{invite}{invite_edited}
{timers}
Message ID: {id}
{url}
"""
DELETED_MESSAGE_TEMPLATE = """
{ts}
Channel: {channel_name} ({channel})
Author: {author}
{invite}
Message ID: {id}
"""


# CHANNEL TEMPLATES
DELETED_CHANNEL_TEMPLATE = """
{ts}
Channel `{name}` was deleted with {count} active ads.
"""


# Notification rendering functions
def fetch_server_tz(db_session, server_id):
    server = ensure_server(db_session, server_id)
    return get_tz(server.timezone)

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
        ta, ts = time_labels_from_utc(past_user.created_at, tz)
        if past_user.invite_server_name is None:
            server_name = '_unknown server_'
        else:
            server_name = past_user.invite_server_name
        output.append(USER_LAST_POST.format(ta=ta, ts=ts, s=server_name))

    # Check the timing on the last post for this server in the
    #   same channel
    past_server = AdsMessages.most_recent_server_ad(db_session, ad)
    if past_server is None:
        server_str = None
    elif past_server != past_user:
        ta, ts = time_labels_from_utc(past_server.created_at, tz)
        output.append(SERVER_LAST_POST.format(ta=ta, ts=ts, u=past_server.author_id))

    return '\n'.join(output).strip()


def render_age_gate(ad):
    valid, ages = ad.has_valid_age_gate()
    if ages is None:
        return '**No Age Gate ("18+" or similar) Found**'

    if valid:
        return ad.age_gate

    if len(ages) > 1:
        return f'**Multiple potential age gates found: {ad.age_gate}**'

    return f'**Invalid age gate: {ad.age_gate}**'


async def render_new_ad(bot, db_session, ad, message, channel):
    tz = fetch_server_tz(db_session, channel.server_id)
    invite = await render_invite(bot, ad, tz)
    timers = render_timers(db_session, ad, tz)
    age_gate = render_age_gate(ad)
    return NEW_MESSAGE_TEMPLATE.format(
        ts=datetime.now(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=message.author.mention,
        channel=message.channel.mention,
        age_gate=age_gate,
        invite=invite,
        timers=(timers+'\n' if timers else ''),
        id=ad.id,
        url=message.jump_url
    )


async def render_ad_edited(bot, db_session, ad, message, channel, diffs):
    tz = fetch_server_tz(db_session, channel.server_id)
    invite = await render_invite(bot, ad, tz)
    timers = render_timers(db_session, ad, tz)
    age_gate = render_age_gate(ad)

    dkeys = diffs.keys()
    ag_edited = '  **<<< EDITED**' if 'age_gate' in dkeys else ''
    invite_flag = any(k.startswith('invite_') for k in dkeys)
    invite_edited = '  **<<< EDITED**' if invite_flag else ''
    return EDITED_MESSAGE_TEMPLATE.format(
        ts=datetime.now(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=message.author.mention,
        channel=message.channel.mention,
        age_gate=age_gate,
        ag_edited=ag_edited,
        invite=invite,
        invite_edited=invite_edited,
        timers=(timers+'\n' if timers else ''),
        id=ad.id,
        url=message.jump_url
    )


async def render_ad_deleted(bot, db_session, ad, channel):
    tz = fetch_server_tz(db_session, channel.server_id)
    invite = await render_invite(bot, ad, tz)
    return DELETED_MESSAGE_TEMPLATE.format(
        ts=ad.deleted_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT),
        channel_name=channel.name,
        author=f"<@{ad.author_id}> (id: {ad.author_id})",
        channel=f"<#{channel.id}>",
        invite=invite,
        id=ad.id
    )


def render_channel_deleted(db_session, channel, count):
    tz = fetch_server_tz(db_session, channel.server_id)
    ts = channel.deleted_at.astimezone(tz).strftime(OUTPUT_DATETIME_FORMAT)
    return DELETED_CHANNEL_TEMPLATE.format(ts=ts, name=channel.name, count=count)


@asynccontextmanager
async def ad_webhook(webhook_url):
    async with aiohttp.ClientSession() as wh_session:
        adapter = AsyncWebhookAdapter(wh_session)
        webhook = Webhook.from_url(webhook_url, adapter=adapter)
        yield webhook

async def delete_ad_notification(channel, msg_id):
    """
    Call the webhook associated with the channel to delete a
    notification message.
    """

    if channel is None or channel.webhook_url is None:
        return

    try:
        async with ad_webhook(channel.webhook_url) as webhook:
            return await webhook.delete_message(msg_id)
    except (NotFound, Forbidden):
        # NotFound means the notification was probably deleted already
        # Forbidden probably means the webhook was modified recently
        pass


async def notify_ad_webhook(msg, channel, username='RR Bot'):
    """
    Call the webhook associated with the channel to create a
    notification message.
    """

    if channel is None or channel.webhook_url is None:
        return

    try:
        async with ad_webhook(channel.webhook_url) as webhook:
            return await webhook.send(msg, username=username, wait=True)
    except (NotFound, Forbidden):
        channel.webhook_url = None
