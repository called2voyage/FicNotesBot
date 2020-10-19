# Copyright 2020 called2voyage
#
# This file is part of FicNotesBot.
#
# FicNotesBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# FicNotesBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with FicNotesBot.  If not, see <https://www.gnu.org/licenses/>.

from django.db import models

class DiscordUser(models.Model):
    user_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=32)

class Story(models.Model):
    owner = models.ForeignKey(DiscordUser, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ['owner', 'name']

class StoryElement(models.Model):
    CHARACTER = 'CHAR'
    OBJECT = 'OBJ'
    EVENT = 'EVNT'
    PLACE = 'PLCE'
    # For elements like a relationship that aren't really objects
    CONCEPT = 'CNCP'
    PLOTPOINT = 'PLOT'
    ELEMENT_TYPE_CHOICES = [
        (CHARACTER, 'Character'),
        (OBJECT, 'Object'),
        (EVENT, 'Event'),
        (PLACE, 'Place'),
        (CONCEPT, 'Concept'),
        (PLOTPOINT, 'Plot Point')
    ]
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    type = models.CharField(max_length=4, choices=ELEMENT_TYPE_CHOICES)
    # For plot points, holds the user's custom index
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ['story', 'type', 'name']

class PlotPoint(models.Model):
    index = models.OneToOneField(StoryElement, on_delete=models.CASCADE, primary_key=True)
    header = models.TextField()

class Note(models.Model):
    element = models.ForeignKey(StoryElement, on_delete=models.CASCADE)
    note = models.TextField()
