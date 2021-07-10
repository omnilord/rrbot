def ads_report(ctx):
    return 'Report!'


def ads_sync(ctx):
    return 'Needs data'


def ads_add_channel(ctx, channel_id):
    return 'Needs new channel'


def ads_remove_channel(ctx, channel_id, delete=False):
    return 'Needs old channel' if delete else 'Needs current channel'


def ads_warn(ctx, message_id):
    return 'This is warning #x for this user/server combo.'


def ads_webhook(ctx, message_id):
    return 'Set or delete the ads webhook for a channel.'
