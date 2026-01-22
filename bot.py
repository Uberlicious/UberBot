import random
import re
import requests
import json
import logging
import time
import os
from datetime import datetime
from dotenv import load_dotenv

import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

intents = nextcord.Intents.all()
client = commands.Bot(command_prefix="u!", intents=intents)


logger = logging.getLogger('nextcord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

random.seed(time.mktime(datetime.now().timetuple()))

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("---------")


def getSuperStats():
    URL = "https://www.superheroapi.com/ids.html"
    page = requests.get(URL)
    page_split = page.content.splitlines()
    max_num = 0
    for i, p in enumerate(page_split):
        if p == b"        </table>":
            num = str(page_split[i - 4])
            max_num = int(num.split(">")[1].split("<")[0])

    rand_hero = random.randint(0, max_num)

    HeroURL = f"https://www.superheroapi.com/api/10158934816710166/{rand_hero}"
    hero_page = requests.get(HeroURL)
    hero_json = hero_page.json()
    hero = {}
    hero["name"] = hero_json["name"]
    hero["stats"] = hero_json["powerstats"]
    hero["portrait"] = hero_json["image"]["url"]
    hero_overall_stats = 0
    for k, v in hero["stats"].items():
        if v != "null":
            hero_overall_stats = hero_overall_stats + int(v)
        else:
            hero["stats"][k] = 0
    hero["stats"]["overall"] = hero_overall_stats
    return hero


def heroembed(player, hero):
    embed = nextcord.Embed(title=f"{player}", color=0x0084FF)
    embed.add_field(name="Hero", value=f'{hero["name"]}', inline=True)
    embed.add_field(
        name="Intelligence", value=f'{hero["stats"]["intelligence"]}', inline=True
    )
    embed.add_field(name="Strength",
                    value=f'{hero["stats"]["strength"]}', inline=True)
    embed.add_field(
        name="Speed", value=f'{hero["stats"]["speed"]}', inline=True)
    embed.add_field(
        name="Durability", value=f'{hero["stats"]["durability"]}', inline=True
    )
    embed.add_field(
        name="Power", value=f'{hero["stats"]["power"]}', inline=True)
    embed.add_field(
        name="Combat", value=f'{hero["stats"]["combat"]}', inline=True)
    embed.add_field(
        name="Overall", value=f'{hero["stats"]["overall"]}', inline=True)
    embed.set_image(url=hero["portrait"])
    return embed


def sortteams(members):
    random.shuffle(members)
    i = 0
    half = int(len(members) / 2)
    team1 = ""
    team2 = ""
    for m in members:
        if i < half:
            team1 += f"<@{m.id}>\n"
        else:
            team2 += f"<@{m.id}>\n"
        i += 1
    if team1 == "":
        team1 = "null"
    if team2 == "":
        team2 = "null"
    return team1, team2


@client.slash_command(
    name="random_teams",
    description="Split members in current voice chat into two random teams",
)
async def randteams(interaction: Interaction):
    cid = interaction.user.voice.channel.id
    channel = client.get_channel(cid)
    members = channel.members
    team1, team2 = sortteams(members)
    embed_send = nextcord.Embed(title=f"Random Teams", color=0x1777BF)
    embed_send.add_field(name="Team 1", value=f"{team1}")
    embed_send.add_field(name=chr(173), value=chr(173))
    embed_send.add_field(name="Team 2", value=f"{team2}")
    await interaction.response.send_message(embed=embed_send)


d2_definition_data = {}
pvpPlaylists = {}


@client.slash_command(
    name="destiny_2_private_random", description="Get Random map / teams."
)
async def d2random(
    interaction: Interaction,
    teams: bool = SlashOption(
        name="sort_teams",
        description="Do you want to sort people in your channel into teams?",
    ),
    data_refresh: bool = SlashOption(
        name="refresh_maps",
        description="Do you want to force a map list refresh?",
        default=False,
        required=False,
    ),
):
    global d2_definition_data
    global pvpPlaylists
    if teams == True:
        cid = interaction.user.voice.channel.id
        channel = client.get_channel(cid)
        members = channel.members
        team1, team2 = sortteams(members)

    if data_refresh or len(d2_definition_data) == 0:
        await interaction.response.send_message(
            "Refreshing backend data... This may take a few minutes..."
        )

        url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
        payload = {}
        headers = {
            "Cookie": "bungled=5819630653482468767; bungledid=Bxn8WG4NpoFBpS5v7DR0WChKgccdpqHZCAAA; bungleanon=sv=BAAAAABDGgAAAAAAAKcWFwIAAAAAAAAAAAAAAABKgccdpqHZCEAAAACmYP4RsAypYdPJMlasDO8RnFBG2c9tpGNXGdzxs9iTVkBvir8lm48i4yFZoPOPnxMQEalsLkQIwzu2kmDeb90r&cl=MC42NzIzLjM1MDY3NTU5; Q6dA7j3mn3WPBQVV6Vru5CbQXv0q+I9ddZfGro+PognXQwjW=v1rdlRgw__wPX; __cflb=0H28vP5GxS7vgVH4MZT6rB7QcDNQ8jpmVdwafMSEvVy"
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        manifest_data = json.loads(response.text)
        activity_url = manifest_data["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyActivityDefinition"]

        url = f"https://www.bungie.net{activity_url}"
        response = requests.request("GET", url, headers=headers, data=payload)
        d2_definition_data = json.loads(response.text)
        for activity_id, prop in d2_definition_data.items():
            if prop["isPvP"] == True and prop["isPlaylist"] == True:
                name = prop["displayProperties"]["name"].lower()
                if name not in pvpPlaylists.keys():
                    pvpPlaylists[prop["displayProperties"]
                                 ["name"].lower()] = activity_id
        await interaction.edit_original_message(content="Refreshing complete...")

    selected_playlist = pvpPlaylists["rumble"]
    rand_map_id = random.choice(
        d2_definition_data[selected_playlist]["playlistItems"])["activityHash"]
    rand_map = [
        d2_definition_data[str(rand_map_id)]["displayProperties"]["name"],
        d2_definition_data[str(rand_map_id)]["pgcrImage"],
    ]
    embed_send = nextcord.Embed(title=f"{rand_map[0]}", color=0x0084FF)
    if teams:
        embed_send.add_field(name="Team 1", value=f"{team1}")
        embed_send.add_field(name=chr(173), value=chr(173))
        embed_send.add_field(name="Team 2", value=f"{team2}")
    embed_send.set_image(url=f"https://www.bungie.net{rand_map[1]}")

    if interaction.response.is_done():
        await interaction.edit_original_message(embed=embed_send)
    else:
        await interaction.response.send_message(embed=embed_send)


# @client.slash_command(guild_ids=[649350732394528768])
# async def your_favorite_dog(
#     interaction: Interaction,
#     dog: str = SlashOption(
#         name="dog",
#         description="Choose the best dog from this autocompleted list!",
#     ),
# ):
#     # sends the autocompleted result
#     await interaction.response.send_message(f"Your favorite dog is {dog}!")


# @your_favorite_dog.on_autocomplete("dog")
# async def favorite_dog(interaction: Interaction, dog: str):
#     if not dog:
#         # send the full autocomplete list
#         await interaction.response.send_autocomplete(list_of_dog_breeds)
#         return
#     # send a list of nearest matches from the list of dog breeds
#     get_near_dog = [
#         breed for breed in list_of_dog_breeds if breed.lower().startswith(dog.lower())
#     ]
#     await interaction.response.send_autocomplete(get_near_dog)


@ client.slash_command(
    description="Simulates rolling dice.",
)
async def roll_dice(
    interaction: Interaction,
    number_of_dice: int = SlashOption(
        name="dice",
        description="The number of dice you want",
    ),
    number_of_sides: int = SlashOption(
        name="sides",
        description="The number of sides for each die",
    ),
):
    dice = [
        str(random.choice(range(1, number_of_sides + 1))) for _ in range(number_of_dice)
    ]
    await interaction.response.send_message(", ".join(dice))


@ client.slash_command(
    description="50/50 chance for yes or no answer.",
)
async def frank(interaction: Interaction):
    if interaction:
        rand = random.randint(0, 100)
        if rand >= 51:
            url = "https://api.giphy.com/v1/gifs/search?api_key=WlUS2Sd7uP61mfO02n3SUS8oUISZOF2b&q=Yes&limit=25"
            res = requests.request("GET", url)
            json_res = res.json()
            response = json_res["data"][random.randint(0, 24)]["url"]
            await interaction.response.send_message(
                f"A coin flips through the air... {response}"
            )
        if rand == 50:
            url = "https://api.giphy.com/v1/gifs/search?api_key=WlUS2Sd7uP61mfO02n3SUS8oUISZOF2b&q=Maybe&limit=25"
            res = requests.request("GET", url)
            json_res = res.json()
            response = json_res["data"][random.randint(0, 24)]["url"]
            await interaction.response.send_message(
                f"A coin flips through the air... {response}"
            )
        if rand < 50:
            url = "https://api.giphy.com/v1/gifs/search?api_key=WlUS2Sd7uP61mfO02n3SUS8oUISZOF2b&q=No&limit=25"
            res = requests.request("GET", url)
            json_res = res.json()
            response = json_res["data"][random.randint(0, 24)]["url"]
            await interaction.response.send_message(
                f"A coin flips through the air... {response}"
            )


@ client.slash_command(
    description="Get a Superhero.",
)
async def my_super(interaction: Interaction):
    queryUser = getSuperStats()
    await interaction.response.send_message(
        embed=heroembed(interaction.user.name, queryUser)
    )


@ client.slash_command(
    name="super_duel", description="Who is stronger?"
)
async def super_duel(interaction: Interaction, competitor: nextcord.User):
    guild = interaction.guild
    messageText = f"{interaction.user.name} challenges {competitor.mention} do a superduel, hit reaction to play compete."
    await interaction.response.send_message(messageText)
    async for message in interaction.channel.history():
        if not message.content == messageText:
            continue
        if message.content == messageText:
            accept_decline = message
            break
    emoji = nextcord.utils.get(guild.emojis, name="GAME")
    if accept_decline != None:
        if emoji != None:
            await accept_decline.add_reaction(emoji)
        else:
            await accept_decline.add_reaction("👍")

    reaction = await client.wait_for(
        "reaction_add",
        timeout=60,
        check=lambda reaction, user: user.id == competitor.id,
    )

    author = getSuperStats()
    comp = getSuperStats()

    await interaction.followup.send(embed=heroembed(interaction.user.name, author))
    await interaction.followup.send(embed=heroembed(competitor.name, comp))


@ client.slash_command(
    description="Create Game Channel.",
)
async def create_channel(
    interaction: Interaction,
    channel_name: str = SlashOption(
        name="channel_name", description="What do you want this new channel to be named"
    ),
    icon: str = SlashOption(
        name="emoji", description="What emoji do you want set for the icon?"
    ),
):
    guild = interaction.guild

    existing_channel = nextcord.utils.get(guild.channels, name=channel_name)
    existing_category = nextcord.utils.get(guild.categories, name=channel_name)
    existing_role = nextcord.utils.get(guild.roles, name=channel_name)

    role_perms = nextcord.Permissions()
    role_perms.update(
        manage_roles=True,
        create_invite=True,
        change_nickname=True,
        create_instant_invite=True,
        read_messages=True,
        send_messages=True,
        stream=True,
        send_tts_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        mention_everyone=True,
        external_emojis=True,
        connect=True,
        speak=True,
        use_voice_activation=True,
    )

    if not existing_channel and not existing_category and not existing_role:

        new_role = await guild.create_role(
            name=channel_name, permissions=role_perms, mentionable=True
        )

        bots_role = nextcord.utils.get(guild.roles, name="Bots")

        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
            new_role: nextcord.PermissionOverwrite(read_messages=True),
            bots_role: nextcord.PermissionOverwrite(read_messages=True),
        }

        new_cat = await guild.create_category(channel_name)
        lower_cn = channel_name.lower()
        await guild.create_text_channel(f"general-chat-{lower_cn}", category=new_cat)
        await guild.create_voice_channel(f"General-{lower_cn}", category=new_cat)

        await interaction.response.send_message(
            f"j!roleReaction set {icon} {new_role.mention}"
        )

    else:
        if existing_channel:
            await interaction.response.send_message(
                f'Channel "{channel_name}" already exists'
            )
        elif existing_category:
            await interaction.response.send_message(
                f'Category "{channel_name}" already exists'
            )
        elif existing_role:
            await interaction.response.send_message(
                f'Role "{channel_name}" already exists'
            )


@ client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You do not have the correct role for this command.")


@ client.event
async def on_message(message):
    if message.author == client.user:
        return

    brooklyn_99_quotes = [
        "I'm the human form of the 💯 emoji.",
        "Bingpot!",
        (
            "Cool. Cool cool cool cool cool cool cool, "
            "no doubt no doubt no doubt no doubt."
        ),
    ]

    neat_gif = "https://media.giphy.com/media/8vtm3YCdxtUvjTn0U3/giphy.gif"
    what_boom = "https://media2.giphy.com/media/xuDHhHcCR0rew/source.gif"
    raid = [
        "https://static-cdn.jtvnw.net/ttv-boxart/Raid%3A%20Shadow%20Legends.jpg",
        "https://tenor.com/view/sandoz-sandozprod-sandoz-ytb-canu-raid-gif-15527040",
        "https://www.youtube.com/watch?v=EHnkV2zhsN8&feature=emb_logo",
        "https://preview.redd.it/5bejvua0wjr31.png?width=640&crop=smart&auto=webp&s=764f9d8cf6879a1d3707f66cb1d780f6711eb4d9",
        "https://images7.memedroid.com/images/UPLOADED313/5d7bf7bdd1d1f.jpeg",
    ]

    gardy = ["gardy.?time", "tobey.?time", "grady.?time"]

    luxe = ["luxe.?time"]

    shapes = ["shapes", "shape"]

    luxe_gif = [
        "https://gph.is/g/Z7dOq30",
        "https://gph.is/1jEmOk3",
        "https://gph.is/1MVJf13",
        "https://gph.is/2uUD0dq",
        "http://gph.is/2lw2qWw",
        "https://media.tenor.com/images/6d37431ebd0ae9e3742f93094df0619e/tenor.gif",
    ]

    if re.search("99!", message.content):
        response = random.choice(brooklyn_99_quotes)
        await message.channel.send(response)

    if re.search("antiquing", message.content):
        response = what_boom
        await message.channel.send(response)

    if re.findall(r"(?=(" + "|".join(gardy) + r"))", message.content.lower()):
        rand = random.randint(0, 100)
        if rand >= 75:
            url = "https://api.giphy.com/v1/gifs/search?api_key=WlUS2Sd7uP61mfO02n3SUS8oUISZOF2b&q=Time&limit=25"
            res = requests.request("GET", url)
            json_res = res.json()
            response = json_res["data"][random.randint(0, 24)]["url"]
            await message.channel.send(response)

    if re.findall(r"(?=(" + "|".join(luxe) + r"))", message.content.lower()):
        rand = random.randint(0, 100)
        if rand >= 95:
            response = random.choice(luxe_gif)
            await message.channel.send(response)
        elif rand >= 75:
            url = "https://api.giphy.com/v1/gifs/search?api_key=WlUS2Sd7uP61mfO02n3SUS8oUISZOF2b&q=Shower&limit=25"
            res = requests.request("GET", url)
            json_res = res.json()
            response = json_res["data"][random.randint(0, 24)]["url"]
            await message.channel.send(response)
    
    if re.findall(r"(?=(" + "|".join(shapes) + r"))", message.content.lower()):
        rand = random.randint(0, 100)
        if rand >= 99:
            response = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHNjbm13c3kwc2s4M3hkOWRxanQzZWhwY2MzbGhvNjA0Yzc1YWd0MCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/P3ataVxTgFOimQeC0S/giphy.gif"
            await message.channel.send(response)
        elif rand >= 90:
            url = "https://api.giphy.com/v1/gifs/search?api_key=WlUS2Sd7uP61mfO02n3SUS8oUISZOF2b&q=shape-math-confused&limit=25"
            res = requests.request("GET", url)
            json_res = res.json()
            response = json_res["data"][random.randint(0, 24)]["url"]
            await message.channel.send(response)

    if re.search("i missed the part where that's my problem", message.content.lower()):
        await message.channel.send(file=nextcord.File("resources/my_problem.mp4"))

    if re.search("get these cranberries", message.content.lower()):
        await message.channel.send(file=nextcord.File("resources/cranberries.mp4"))

#    if re.search('RAID', message.content):
#        quote = random.choice(raid)
#        response = f'Did somebody say...\n{quote}'
#        await message.channel.send(response)
#        await bot.process_commands(message)

load_dotenv()
discordToken = os.getenv("DISCORD_TOKEN")

client.run(discordToken)
