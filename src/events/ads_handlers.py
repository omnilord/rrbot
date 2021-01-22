from db import (
    UTC_TZ,
    AdsChannels,
    AdsMessages,
    Session,
    ensure_server
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
def time_labels_for_utc(field, tz):
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
        ta, ts = time_labels_for_utc(past_user.created_at, tz)
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
        ta, ts = time_labels_for_utc(past_server.created_at, tz)
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
            ad = await AdsMessages.from_discord_message(db_session, bot, message)
            db_session.add(ad)
            db_session.commit()
            server = ensure_server(db_session, message.guild.id)
            notice = await render_new_ad(bot, db_session, ad, message, channel, server.timezone)
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
            notice = await render_ad_deleted(bot, ad, channel, server.timezone)
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
