def setup(bot):
    print('Loading generic `on_ready` event')
    @bot.event
    async def on_ready():
        channel = await bot.fetch_channel(738599835359510648)
        await channel.send('I am alive!')
