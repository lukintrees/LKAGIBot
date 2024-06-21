# LKAGIBot, Cross-platform chatbot with extensive customization features.
# Copyright (c) 2024 lukintrees and contributors
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import asyncio
import logging
from typing import List, AsyncIterable

import discord

from config import get_config
from platforms import Message, Provider


class DiscordMessage(Message):
    def __init__(self, message: discord.Message):
        super().__init__(message.content)
        self.message = message

    async def get_context(self, limit: int = 5) -> List["DiscordMessage"]:
        context = []
        async for msg in self.message.channel.history(limit=limit, before=self.message):
            context.append(DiscordMessage(msg))
        return context


class DiscordProvider(Provider):
    def __init__(self):
        self.config = get_config()["bot"]["discord"]
        self.token = self.config["token"]
        self.bot = discord.Client(intents=discord.Intents.all())
        self.message_queue = asyncio.Queue()

    async def send_message(self, message: str, reply_to: Message):
        if isinstance(reply_to, DiscordMessage):
            await reply_to.message.channel.send(
                message, reference=reply_to.message, allow_mentions=False
            )
        else:
            raise ValueError("reply_to must be an instance of DiscordMessage")

    async def get_message_generator(self) -> AsyncIterable[DiscordMessage]:
        while True:
            message = await self.message_queue.get()
            yield DiscordMessage(message)

    async def get_message_context(self, message: Message) -> List[DiscordMessage]:
        if isinstance(message, DiscordMessage):
            return await message.get_context()
        else:
            raise ValueError("message must be an instance of DiscordMessage")

    async def start(self):
        @self.bot.event
        async def on_ready():
            logging.info(f"Logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(message):
            if message.author != self.bot.user:
                await self.message_queue.put(message)

        await self.bot.start(self.token)

    async def stop(self):
        await self.bot.close()
