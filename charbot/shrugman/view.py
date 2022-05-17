# -*- coding: utf-8 -*-
#  ----------------------------------------------------------------------------
#  MIT License
#
# Copyright (c) 2022 Bluesy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#  ----------------------------------------------------------------------------
"""Shrugman view."""
import datetime
import random
from enum import Enum
from typing import Protocol

import discord
from discord import ui
from discord.utils import utcnow

from . import modal


__all__ = ("Shrugman", "words")

FailStates = Enum(
    "FailStates",
    r"<:KHattip:896043110717608009> `¯` `¯\` `¯\_` `¯\_(` `¯\_(ツ` `¯\_(ツ)` `¯\_(ツ)_` `¯\_(ツ)_/` `¯\_(ツ)_/¯`",
    start=0,
)

with open("charbot/media/shrugman/words.csv") as f:
    words = [word.replace("\n", "") for word in f.readlines()]


class CBot(Protocol):
    async def give_game_points(
        self, member: discord.Member | discord.User, game: str, points: int, bonus: int = 0
    ) -> int:
        ...


class Shrugman(ui.View):
    """View subclass that represents a game of shrugman.

    Parameters
    ----------
    bot : CBot
        The bot instance.
    word : str
        The word to guess.
    fail_enum : enum = FailStates
        The enum to use for the fail state.

    Attributes
    ----------
    bot : CBot
        The bot instance.
    word : str
        The word to guess.
    fail_enum : enum = FailStates
        The enum to use for the fail state.
    guess_count : int
        The number of guesses the player has made.
    guesses : list[str]
        The list of guesses the player has made.
    mistakes : int
        The number of mistakes the player has made.
    dead : bool
        Whether the player is dead.
    guess_word_list : list[str]
        The word to guess represented as a list of characters, with hyphens replacing unguessed letters.
    length : int
        The length of the word to guess.
    start_time : datetime.datetime
        The time the game started. Timzone aware.
    """

    def __init__(self, bot: CBot, word: str, *, fail_enum=FailStates):
        super().__init__(timeout=600)
        self.bot = bot
        self.word = word or random.choice(words)
        self.fail_enum = fail_enum
        self.guess_count = 0
        self.guesses: list[str] = []
        self.mistakes = 0
        self.dead = False
        self.guess_word_list = ["-" for _ in self.word]
        self.length = len(word)
        self.start_time = utcnow()

    # noinspection PyUnusedLocal
    @ui.button(label="Guess", style=discord.ButtonStyle.success)
    async def guess_button(self, interaction: discord.Interaction, button: ui.Button):  # skipcq: PYL-W0613
        """Guess a letter.

        If the letter is in the word, it will be added to the right spots in the guess word list.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        button : ui.Button
            The button that was pressed.
        """
        if self.dead:
            await interaction.response.send_message("You're dead, you can't guess anymore.", ephemeral=True)
            await self.disable()
            message = interaction.message
            assert isinstance(message, discord.Message)  # skipcq: BAN-B101
            await message.edit(view=self)
            return
        await interaction.response.send_modal(modal.GuessModal(self))

    # noinspection PyUnusedLocal,DuplicatedCode
    @ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: ui.Button):  # skipcq: PYL-W0613
        """Stop the game.

        This will also disable the buttons.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        button : ui.Button
            The button that was pressed.
        """
        await self.disable()
        embed = discord.Embed(
            title="**Cancelled** Shrugman",
            description=f"Guess the word: `{''.join(self.guess_word_list)}`",
            color=discord.Color.dark_purple(),
        )
        embed.set_footer(text="Type /shrugman to play")
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Shrugman", value=self.fail_enum(self.mistakes).name, inline=True)
        embed.add_field(name="Guesses", value=f"{self.guess_count}", inline=True)
        embed.add_field(name="Mistakes", value=f"{self.mistakes}", inline=True)
        embed.add_field(name="Word", value=f"{self.word}", inline=True)
        embed.add_field(name="Guesses", value=f"{', '.join(self.guesses) or 'None'}", inline=True)
        time_taken = utcnow().replace(microsecond=0) - self.start_time.replace(microsecond=0)
        embed.add_field(name="Time Taken", value=f"{time_taken}", inline=True)
        if (utcnow() - self.start_time) > datetime.timedelta(seconds=60) and self.guess_count > 5:
            embed.add_field(name="Time Taken", value=f"{time_taken}", inline=True)
            points = await self.bot.give_game_points(interaction.user, "shrugman", 2, 0)
            embed.add_field(
                name="Reputation gained",
                value="2 Reputation" if points == 2 else f"{points} Reputation (Daily Cap Hit)",
                inline=True,
            )
        else:
            embed.add_field(name="Reputation gained", value="0 Reputation", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    async def disable(self):
        """Disable the buttons and stop the view."""
        self.guess_button.disabled = True
        self.stop_button.disabled = True
        self.stop()
