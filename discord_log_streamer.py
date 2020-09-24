'''
import discord
import requests
from bs4 import BeautifulSoup
import asyncio

client = discord.Client()


@client.event
async def on_ready():

    # Create a task and run check_html and feed it a parameter of 5 seconds
    client.loop.create_task(check_html(5))
    print("Bot is active")


async def check_html(time):
    while True:
        url = 'url here'
        res = requests.get(url)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        html_element = soup.find_all('td', {"class": "eksam-ajad-aeg"})

        ret = []

        for t in html_element:
            ret.append(t.text)
        print(ret)
        if '.12.' in ret:
            for guild in client.guilds:
                for channel in guild.channels:
                    if channel.id == 758088198852182037:
                        await channel.send('message')

        # Asyncronously sleep for 'time' seconds
        await asyncio.sleep(time)


client.run('token')
'''