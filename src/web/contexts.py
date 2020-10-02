from flask import redirect, url_for, g, abort, render_template
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized


def get_discord_context(discord):
    if 'ctx' not in g:
        g.ctx = {
            'user': discord.fetch_user(),
            'guilds': discord.fetch_guilds(),
        }
    return g.ctx

def get_guild_context(discord, guild_id):
    ctx = get_discord_context(discord)
    if 'guild' not in g.ctx['guild']:
        guild = [el for el in g.ctx['guilds'] if el.id == guild_id]
        g.ctx['guild'] = guild[0] if guild else None
    return g.ctx['guild']

def get_db():
    if db not in g:
        # TODO
        g.db = object()

    return g.db
