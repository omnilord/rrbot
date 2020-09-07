from discord.ext import commands
from configuration import CONFIG, PREFIX
from database import DB
import os
from pathlib import Path

print('Using `{}` as command token.'.format(PREFIX))
bot = commands.Bot(command_prefix=PREFIX)

cmd_path = os.path.join(os.getcwd(), 'commands')
for f in os.listdir(cmd_path):
    if f == '__init__.py' or not f.endswith('.py'):
        continue
    bot.load_extension('commands.{}'.format(Path(f).stem))


print('All aboard!')
bot.run(CONFIG['discord_client_secret'])