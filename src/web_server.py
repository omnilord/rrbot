"""
This is the main routing file for RR Bot's web administrative functionality

"""

import os, functools

from configuration import APP_SECRET, TOKEN, SECRET, CLIENTID, CALLBACK_ROOT, LOG_LEVEL, ADMINS
from flask import Flask, redirect, url_for, g, abort, render_template, session
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from web import contexts

DEBUGGING = (LOG_LEVEL=='DEBUG')

app = Flask(__name__, template_folder='web/templates')
app.secret_key = APP_SECRET

app.secret_key = b'random bytes representing flask secret key'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'      # !! Only in development environment.

app.config['DISCORD_CLIENT_ID'] = CLIENTID
app.config['DISCORD_CLIENT_SECRET'] = SECRET
app.config['DISCORD_REDIRECT_URI'] = f'{CALLBACK_ROOT}/callback/'
app.config['DISCORD_BOT_TOKEN'] = TOKEN

discord = DiscordOAuth2Session(app)


"""
root landing page
"""

@app.route('/')
def index():
    return render_template('index.html', login_url=url_for('login'))


"""
Discord OAuth2 workflow
"""

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for('.index'))

@app.route('/login')
def login():
    return discord.create_session()

@app.route('/callback')
def callback():
    discord.callback()
    return redirect(url_for('app'))

@app.route('/logout')
def logout():
    discord.revoke()
    return redirect(url_for('.app_index'))


"""
Every route below requies being on the admin list
"""

class NotAnAdmin(Exception):
    def __init__(self):
        super().__init__('This requires administrative access')

def requires_administrator_context(*opts):
    # fake default args
    if not opts:
        opts = ['user']

    def predicate(func):
        @functools.wraps(func)
        @requires_authorization
        def context_wrapper(*args, **kwargs):
            user = discord.fetch_user()
            if user.id in ADMINS:
                ctx = contexts.get_discord_context(discord)
                return func(ctx, *args, **kwargs)
            raise NotAnAdmin()
        return context_wrapper
    return predicate

@app.errorhandler(NotAnAdmin)
def redirect_not_an_admin(e):
    session
    return redirect(url_for('.logout'))

@app.route('/app/')
@requires_administrator_context()
def app_index(ctx):
    return render_template('app.html', **ctx)

"""
All API and API support decorators from here
"""


if __name__ == '__main__':
    app.run(debug=DEBUGGING)
