import pymongo
import dns
import discord
import random
import requests
import json
import calendar
import datetime
import pytz
import aiocron
import asyncio

utc = pytz.UTC

discord_token = "discord_token"
mongo_key = "mongo_connexion_string "
client = discord.Client()
mongo_client = pymongo.MongoClient(mongo_key)

db = mongo_client.YAPDP

emergency_cards = db.emergency_cards
cards = emergency_cards.find()
cards_length = len(list(cards))


class Card:
    def __init__(self, number, title, header, content, tips, image_url):
        self.number = number
        self.title = title
        self.header = header
        self.content = content
        self.tips = tips
        self.image_url = image_url

    def print_card_content(self):
        advice = "\u200b"
        for tip in self.tips:
            advice += f"\n \u2022 {tip} \n"

        embed = discord.Embed(
            title=f"**{self.number}\t-\t{self.title}**",
            description=self.header,
            colour=discord.Colour.dark_gold(),
        )

        embed.set_author(
            name="Writer emergency",
            url="https://www.writeremergency.com/",
            icon_url="https://i.postimg.cc/fRHXbhxG/writer-emergency.jpg"
        )
        embed.set_image(url=self.image_url)
        embed.add_field(name="\u200b", value=f"{self.content}\n\u200b", inline=False)
        embed.add_field(name="**Essayez ça :**", value=advice, inline=False)
        embed.set_footer(text="Textes et illustrations © 2022 Quote-Unquote LLC – Tous droits réservés.")
        return embed


def get_a_card():
    card_id = random.randrange(1, cards_length + 1)
    card = emergency_cards.find_one({"card": card_id})

    card_object = Card(card['card'], card['title'], card['header'], card['content'], card['tips'], card['image_url'])
    return card_object


def fetch_events():
    response = requests.get("url_open_agenda_api")
    events = response.json()['events']
    return events


def life_time_message(time_left):
    return time_left.total_seconds() + 3600


def embed_event(event, toggle):
    color = discord.Colour.orange()
    if not toggle:
        color = discord.Colour.blue()

    embed = discord.Embed(
        title=event["title"]["fr"],
        description=event["description"]["fr"],
        colour=color
    )
    embed.set_author(
        name="L'agenda du scénario",
        url="https://openagenda.com/scenario?oaq%5Bpassed%5D=1&oaq%5Border%5D=latest&lang=fr",
        icon_url="https://i.postimg.cc/9F3gDJby/agenda84183454.jpg"
    )

    embed.set_image(url=f"{event['image']['base']}{event['image']['filename']}")
    embed.add_field(name='Lieu :', value=f"{event['location']['name']}\n{event['location']['address']}", inline=False)

    if toggle:
        embed.add_field(name='Date de début :', value=f"{datetime.datetime.fromisoformat(event['lastTiming']['begin']).strftime('%d %m %Y - %H:%M ')}", inline=True)
        embed.add_field(name='Date de fin :', value=f"{datetime.datetime.fromisoformat(event['lastTiming']['end']).strftime('%d %m %Y - %H:%M ')}", inline=True)
    else:
        embed.add_field(name='Date limite de dépot :', value=f"{datetime.datetime.fromisoformat(event['lastTiming']['end']).strftime('%d %m %Y - %H:%M ')}", inline=False)

    embed.add_field(name='Détails :', value=f"https://openagenda.com/agendas/84183454/events/{event['uid']}", inline=False)

    return embed


""" Bot Scheduler """
 
@client.event
async def on_ready():
    channel = client.get_channel(960145692918173736)
    money_event = [13, 11, 12, 19, 20]
    meeting_event = [10, 21, 30, 28, 31]

    @aiocron.crontab('00 8 * * *')
    async def week_left_event():
        events = fetch_events()
        current_date = utc.localize(datetime.datetime.today())
        for event in events:
            event_date = datetime.datetime.fromisoformat(event["lastTiming"]["end"])
            time_left = event_date - current_date
            if ((time_left.total_seconds() + 3600) // 86400) == 7.0:
                if any(item in money_event for item in event["categories"]):
                    await channel.send(embed=embed_event(event, False), delete_after=life_time_message(time_left))

    @aiocron.crontab('00 10 1 * *')
    async def in_month_event():
        events = fetch_events()
        current_date = utc.localize(datetime.datetime.today())
        for event in events:
            event_date_begin = datetime.datetime.fromisoformat(event["lastTiming"]["begin"])
            event_date_end = datetime.datetime.fromisoformat(event["lastTiming"]["end"])
            time_left = event_date_end - current_date
            if event_date_begin.month == current_date.month:
                if any(item in meeting_event for item in event["categories"]):
                    await channel.send(embed=embed_event(event, True), delete_after=life_time_message(time_left))

    print(f'ready {client.user}')

""" bot command  """
@client.event
async def on_message(msg):
    channel = client.get_channel(940531498354901080)
    if msg.author == client.user:
        return

    if msg.content.startswith('!SOS') and msg.channel == channel:
        await msg.channel.send(embed=get_a_card().print_card_content())

    """ if msg.content.startswith('!CLEAR') and msg.channel == channel:
        messages = await channel.history(limit=300).flatten()
        print(len(messages))
        for message in messages:
            to_del = await channel.fetch_message(message.id)
            await to_del.delete() """

client.run(discord_token)
asyncio.get_event_loop().run_forever()
