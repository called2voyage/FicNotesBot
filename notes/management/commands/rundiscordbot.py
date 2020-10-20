# Copyright 2020 called2voyage
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import asyncio

import discord
from dotenv import load_dotenv

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from asgiref.sync import sync_to_async
from notes.models import DiscordUser, Story, StoryElement, PlotPoint, Note

class UserNotCreatedError(Exception):
    """Raised when requesting user has not been added"""
    pass

class StoryNotFoundError(Exception):
    """Raised when requested story does not exist"""
    pass

class ElementNotFoundError(Exception):
    """Raised when requested element does not exist"""
    pass

class Command(BaseCommand):
    help = 'Launches the Discord bot'

    def handle(self, *args, **options):
        active = True

        load_dotenv()
        TOKEN = os.getenv('DISCORD_TOKEN')

        client = discord.Client()

        @sync_to_async
        def save_story(message, name):
            story = None
            if DiscordUser.objects.filter(user_id=message.author.id).exists():
                user = DiscordUser.objects.get(user_id=message.author.id)
                story = Story(owner=user, name=name)
                story.save()
            else:
                user = DiscordUser(user_id=message.author.id, name=message.author.name)
                user.save()
                story = Story(owner=user, name=name)
                story.save()
            return story.name

        @sync_to_async
        def save_element(message, name, story, type):
            return save_element_sync(message, name, story, type)

        def save_element_sync(message, name, story, type):
            element = None
            if DiscordUser.objects.filter(user_id=message.author.id).exists():
                user = DiscordUser.objects.get(user_id=message.author.id)
                if Story.objects.filter(owner=user, name=story).exists():
                    story = Story.objects.get(owner=user, name=story)
                    element = StoryElement(story=story, type=type, name=name)
                    element.save()
                else:
                    raise StoryNotFoundError
            else:
                raise UserNotCreatedError
            return story.name, element.name

        @sync_to_async
        def save_plotpoint(message, index, header, story):
            story, index = save_element_sync(message, index, story, StoryElement.PLOTPOINT)
            user = DiscordUser.objects.get(user_id=message.author.id)
            story = Story.objects.get(owner=user, name=story)
            element = StoryElement.objects.get(story=story, name=index)
            plotpoint = PlotPoint(index=element, header=header)
            plotpoint.save()
            return story.name, index

        @sync_to_async
        def save_note(message, note, element, story):
            if DiscordUser.objects.filter(user_id=message.author.id).exists():
                user = DiscordUser.objects.get(user_id=message.author.id)
                if Story.objects.filter(owner=user, name=story).exists():
                    story = Story.objects.get(owner=user, name=story)
                    if StoryElement.objects.filter(story=story, name=element).exists():
                        try:
                            element = StoryElement.objects.get(story=story, name=element)
                            note = Note(element=element, note=note)
                            note.save()
                        except MultipleObjectsReturned:
                            elements = StoryElement.objects.filter(story=story, name=element)
                            type_list = [element.get_type_display() for element in elements]
                            raise MultipleObjectsReturned(type_list)
                    else:
                        raise ElementNotFoundError
                else:
                    raise StoryNotFoundError
            else:
                raise UserNotCreatedError
            return element.name

        @sync_to_async
        def save_note_by_type(message, note, element, type, story):
            if DiscordUser.objects.filter(user_id=message.author.id).exists():
                user = DiscordUser.objects.get(user_id=message.author.id)
                if Story.objects.filter(owner=user, name=story).exists():
                    story = Story.objects.get(owner=user, name=story)
                    if StoryElement.objects.filter(story=story, name=element, type=type).exists():
                        element = StoryElement.objects.get(story=story, name=element, type=type)
                        note = Note(element=element, note=note)
                        note.save()
                    else:
                        raise ElementNotFoundError
                else:
                    raise StoryNotFoundError
            else:
                raise UserNotCreatedError
            return element.name

        @sync_to_async
        def list_stories(user):
            if DiscordUser.objects.filter(user_id=user).exists():
                user = DiscordUser.objects.get(user_id=user)
                return [s.name for s in Story.objects.filter(owner=user)]
            else:
                raise UserNotCreatedError

        @client.event
        async def on_message(message):
            if message.content.startswith('!ficnotesbot add '):
                if message.content.startswith('!ficnotesbot add story '):
                    name = message.content.split('!ficnotesbot add story ')[1]
                    try:
                        story = await save_story(message, name)
                        await message.channel.send(message.author.mention+ ' ' + story + ' has been added to your stories.')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + name + ' already exists.')
                if message.content.startswith('!ficnotesbot add character '):
                    character_story = message.content.split('!ficnotesbot add character ')[1]
                    name = character_story.split(' > ')[0]
                    story = character_story.split(' > ')[1]
                    try:
                        story, character = await save_element(message, name, story, StoryElement.CHARACTER)
                        await message.channel.send(message.author.mention+ ' ' + character + ' has been added to ' + story + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + name + ' is already in ' + story + '.')
                if message.content.startswith('!ficnotesbot add object '):
                    object_story = message.content.split('!ficnotesbot add object ')[1]
                    name = object_story.split(' > ')[0]
                    story = object_story.split(' > ')[1]
                    try:
                        story, object = await save_element(message, name, story, StoryElement.OBJECT)
                        await message.channel.send(message.author.mention+ ' ' + object + ' has been added to ' + story + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + name + ' is already in ' + story + '.')
                if message.content.startswith('!ficnotesbot add event '):
                    event_story = message.content.split('!ficnotesbot add event ')[1]
                    name = event_story.split(' > ')[0]
                    story = event_story.split(' > ')[1]
                    try:
                        story, event = await save_element(message, name, story, StoryElement.EVENT)
                        await message.channel.send(message.author.mention+ ' ' + event + ' has been added to ' + story + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + name + ' is already in ' + story + '.')
                if message.content.startswith('!ficnotesbot add place '):
                    place_story = message.content.split('!ficnotesbot add place ')[1]
                    name = place_story.split(' > ')[0]
                    story = place_story.split(' > ')[1]
                    try:
                        story, place = await save_element(message, name, story, StoryElement.PLACE)
                        await message.channel.send(message.author.mention+ ' ' + place + ' has been added to ' + story + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + name + ' is already in ' + story + '.')
                if message.content.startswith('!ficnotesbot add concept '):
                    concept_story = message.content.split('!ficnotesbot add concept ')[1]
                    name = concept_story.split(' > ')[0]
                    story = concept_story.split(' > ')[1]
                    try:
                        story, concept = await save_element(message, name, story, StoryElement.CONCEPT)
                        await message.channel.send(message.author.mention+ ' ' + concept + ' has been added to ' + story + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + name + ' is already in ' + story + '.')
                if message.content.startswith('!ficnotesbot add plotpoint '):
                    plotpoint_story = message.content.split('!ficnotesbot add plotpoint ')[1]
                    index_header = plotpoint_story.split(' > ')[0]
                    story = plotpoint_story.split(' > ')[1]
                    index = index_header.split('"')[1]
                    header = index_header.split('" ')[1]
                    try:
                        story, index = await save_plotpoint(message, index, header, story)
                        await message.channel.send(message.author.mention+ ' ' + index + ' has been added to ' + story + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except IntegrityError:
                        await message.channel.send(message.author.mention+ ' ' + index + ' is already in ' + story + '.')
                if message.content.startswith('!ficnotesbot add note '):
                    note_element_story = message.content.split('!ficnotesbot add note ')[1]
                    note = note_element_story.split(' > ')[0]
                    element = note_element_story.split(' > ')[1]
                    story = note_element_story.split(' > ')[2]
                    try:
                        element = await save_note(message, note, element, story)
                        await message.channel.send(message.author.mention+ ' Added a note to ' + element + '.')
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')
                    except StoryNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + story + ' not found. Try adding it first with "!ficnotesbot add story ' + story + '".')
                    except ElementNotFoundError:
                        await message.channel.send(message.author.mention+ ' ' + element + ' not found in ' + story + '. Try adding it first with "!ficnotesbot add [type] ' + element + ' > ' + story + '".')
                    except MultipleObjectsReturned as e:
                        message_str = message.author.mention + ' Which ' + element + ' did you mean?\n'
                        emoji = ['6️⃣', '5️⃣', '4️⃣', '3️⃣', '2️⃣', '1️⃣']
                        sent_emoji = {}
                        for type in e.args[0]:
                            em = emoji.pop()
                            message_str = message_str + ' ' + em + ' - ' + type + '\n'
                            sent_emoji[em] = type
                        msg = await message.channel.send(message_str)
                        if '1️⃣' not in emoji:
                            await msg.add_reaction('1️⃣')
                        if '2️⃣' not in emoji:
                            await msg.add_reaction('2️⃣')
                        if '3️⃣' not in emoji:
                            await msg.add_reaction('3️⃣')
                        if '4️⃣' not in emoji:
                            await msg.add_reaction('4️⃣')
                        if '5️⃣' not in emoji:
                            await msg.add_reaction('5️⃣')
                        if '6️⃣' not in emoji:
                            await msg.add_reaction('6️⃣')

                        def check(reaction, user):
                            return user == message.author and str(reaction.emoji) in sent_emoji

                        try:
                            reaction, _ = await client.wait_for('reaction_add', timeout=60.0, check=check)
                            type = StoryElement.ELEMENT_TYPE_CHOICES[[i for i, t in enumerate(StoryElement.ELEMENT_TYPE_CHOICES) if sent_emoji[reaction.emoji] in t][0]][0]
                            element = await save_note_by_type(message, note, element, type, story)
                            await msg.delete()
                            await message.channel.send(message.author.mention+ ' Added a note to ' + element + '.')
                        except asyncio.TimeoutError:
                            await msg.delete()
                            await message.channel.send('Timeout. Try again.')
            if message.content.startswith('!ficnotesbot list '):
                if message.content.startswith('!ficnotesbot list stories'):
                    try:
                        list = await list_stories(message.author.id)
                        msg = "You have the following stories:\n"
                        for story in list:
                            msg = msg + '* ' + story + '\n'
                        await message.channel.send(message.author.mention+ ' ' + msg)
                    except UserNotCreatedError:
                        await message.channel.send(message.author.mention+ ' You have not created any stories yet.')

        @client.event
        async def on_connect():
            await client.change_presence(activity=discord.Game(name="!ficnotesbot help"))

        client.run(TOKEN)
