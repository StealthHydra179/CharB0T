# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2021 Bluesy1 <68259537+Bluesy1@users.noreply.github.com>
# SPDX-License-Identifier: MIT
"""Banner approval flow."""
import discord
from discord import ui

from .._types import BannerStatus
from ... import GuildComponentInteraction as Interaction, CBot


class ApprovalView(ui.View):
    """Approve or deny a banner.

    Parameters
    ----------
    banner: BannerStatus
        The banner to approve or deny.
    mod: int
        The ID of the moderator who requested teh approval session.
    """

    def __init__(self, banner: BannerStatus, mod: int):
        super().__init__()
        self.requester = banner["user_id"]
        self.mod = mod

    async def interaction_check(self, interaction: Interaction[CBot]) -> bool:
        """Check if the interaction is valid."""
        return interaction.user.id == self.mod

    @ui.button(label="Approve", style=discord.ButtonStyle.green)  # pyright: ignore[reportGeneralTypeIssues]
    async def approve(self, interaction: Interaction[CBot], _: ui.Button):
        """Approve the banner."""
        await interaction.response.defer(ephemeral=True)
        await interaction.client.pool.execute(
            "UPDATE banners SET approved = TRUE, cooldown = now() WHERE user_id = $1", self.requester
        )
        await interaction.edit_original_response(content="Banner approved.", attachments=[], view=None)
        self.stop()

    @ui.button(label="Deny", style=discord.ButtonStyle.red)  # pyright: ignore[reportGeneralTypeIssues]
    async def deny(self, interaction: Interaction[CBot], _: ui.Button):
        """Deny the banner."""
        await interaction.response.defer(ephemeral=True)
        await interaction.client.pool.execute("DELETE FROM banners WHERE user_id = $1", self.requester)
        await interaction.edit_original_response(content="Banner denied.", attachments=[], view=None)
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.blurple)  # pyright: ignore[reportGeneralTypeIssues]
    async def cancel(self, interaction: Interaction[CBot], _: ui.Button):
        """Cancel the banner."""
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="Banner approval session cancelled.", attachments=[], view=None
        )
        self.stop()
