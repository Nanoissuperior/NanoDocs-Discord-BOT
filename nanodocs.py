#!/usr/bin/env python3


import datetime
import os
import random
import sys

import discord
import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN', None)
if TOKEN is None:
    print('Set TOKEN="YOUR_TOKEN" in the .env file')
    sys.exit(1)

game = discord.Game("RPC COMMANDS")

description = '''NanoDocs BOT - Will send info upon request'''
bot = commands.Bot(command_prefix='#', description=description)
bot.remove_command("help")
datenow = datetime.datetime.now()

# 1 hour cache for RPC
cache = TTLCache(maxsize=1, ttl=3600)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print('NanoDocs Online')
    print(datenow)
    await bot.change_presence(status=discord.Status.online, activity=game)


def loadRPCdescr():
    try:
        return cache['rpc']
    except KeyError:
        pass
    print('NO CACHE')
    url = "https://docs.nano.org/commands/rpc-protocol/"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, features='lxml')

    rpc_list = dict({})

    for irrelevant in soup.find_all('div', attrs={'class': 'codehilite'}):
        irrelevant.extract()

    for strong in soup.find_all('strong'):
        strong.replaceWith('**' + strong.get_text() + '**')

    for italic in soup.find_all('em'):
        italic.replaceWith('*' + italic.get_text() + '*')

    for code in soup.find_all('code'):
        code.replaceWith('`' + code.get_text() + '`')

    for h3 in soup.find_all('h3'):
        # Command name is the id of the h3
        command = h3.get('id')

        # The description is after the h3
        next_p = h3.find_next_sibling()
        fields = []
        descr = ''
        while next_p is not None and next_p.name != 'h3':
            if next_p.has_attr('class'):
                cl = next_p.get('class')
            else:
                cl = ''
            text = next_p.get_text()
            if len(text) > 1 and text[:2] == '**':
                break

            if 'admonition' in cl:
                fields += [(cl[1].upper(), next_p.get_text().strip().replace('  ', ' '))]
            else:
                descr += next_p.get_text().strip().replace('  ', ' ') + '\n'
            next_p = next_p.find_next_sibling()

        descr = descr.rstrip('\n\r')
        # Adding the command description to the list
        e = discord.Embed(title=command, description=descr, url=url+'#'+command, color=0x00a0ea)
        e.set_author(name="Nano RPC docs", url=url,
                     icon_url='https://docs.nano.org/images/favicon.png')
        e.set_thumbnail(url='https://cdn.discordapp.com/avatars/636508303031271444/8a0cc1a53cdc48b726dcb999f707a90d.png?size=1024')

        for (n, v) in fields:
            e.add_field(name=n, value=v)
        rpc_list[command] = e
    cache['rpc'] = rpc_list
    return rpc_list


@bot.group()
async def rpc(ctx):
    try:
        rpc_list = loadRPCdescr()
    except Exception as e:
        print('Error when getting RPCs: ', e)

    print(ctx.subcommand_passed)
    if ctx.subcommand_passed is None:
        await ctx.send("Please specify the command you're looking for.")

    else:
        try:
            await ctx.send(embed=rpc_list[ctx.subcommand_passed])
        except:
            await ctx.send("Hmm, I can't find that, maybe look at https://docs.nano.org/commands/rpc-protocol/")


@bot.event
async def on_message(message):
    try:
        rpc_list = loadRPCdescr()
    except Exception as e:
        print('Error when getting RPCs: ', e)

    base_url = "https://docs.nano.org/commands/rpc-protocol/"
    chunks = message.content.split('#')
    if chunks[0] == base_url:
        await message.channel.send(embed=rpc_list[chunks[1]])

    await  bot.process_commands(message)

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
