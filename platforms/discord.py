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

from config import get_config
from platforms import Message, Provider

if get_config()["bot"]["discord"]["self_bot"]:
    import selfcord as discord
    from selfcord.context_managers import Typing
else:
    import discord
    from discord.context_managers import Typing


class DiscordMessage(Message):
    def __init__(self, message: discord.Message, bot: discord.Client, text: str = None):
        super().__init__(
            text or message.clean_content,
            message.author.display_name,
            message.author == bot.user,
        )
        self.message = message

    async def get_context(self, bot: discord.Client) -> List["DiscordMessage"]:
        messages = []
        async for msg in self.message.channel.history(limit=25, before=self.message):
            messages.append(msg)
        messages.reverse()

        context = []
        current_message = None
        current_text = []
        count = 0

        for msg in messages:
            if (
                current_message is None
                or msg.author != current_message.author
                or count >= 5
            ):
                if current_message:
                    context.append(
                        DiscordMessage(current_message, bot, "=<|>=".join(current_text))
                    )
                current_message = msg
                current_text = [current_message.content]
                count = 1
            else:
                current_text.append(msg.content)
                count += 1

        if current_message:
            context.append(
                DiscordMessage(current_message, bot, "=<|>=".join(current_text))
            )

        return context[-10:]


class DiscordProvider(Provider):
    def __init__(self):
        self.config = get_config()["bot"]["discord"]
        self.token = self.config["token"]
        if get_config()["bot"]["discord"]["self_bot"]:
            self.bot = discord.Client()
        else:
            self.bot = discord.Client(intents=discord.Intents.all())
        self.message_queue = asyncio.Queue()

    async def send_message(self, message: str, reply_to: Message, reply: bool):
        if isinstance(reply_to, DiscordMessage):
            await reply_to.message.channel.send(
                message,
                allowed_mentions=discord.AllowedMentions(
                    roles=False, users=False, everyone=False, replied_user=False
                ),
                reference=reply_to.message if reply else None,
            )
        else:
            raise ValueError("reply_to must be an instance of DiscordMessage")

    async def get_message_generator(self) -> AsyncIterable[DiscordMessage]:
        while True:
            message = await self.message_queue.get()
            yield DiscordMessage(message, self.bot)

    async def get_message_context(self, message: Message) -> List[DiscordMessage]:
        if isinstance(message, DiscordMessage):
            return await message.get_context(self.bot)
        else:
            raise ValueError("message must be an instance of DiscordMessage")

    def typing(self, message: Message):
        if isinstance(message, DiscordMessage):
            return Typing(message.message.channel)
        else:
            raise ValueError("message must be an instance of DiscordMessage")

    async def start(self):
        @self.bot.event
        async def on_ready():
            logging.info(f"Logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(message):
            if message.author != self.bot.user and self.bot.user in message.mentions:
                await self.message_queue.put(message)

        await self.bot.start(self.token)

    async def stop(self):
        await self.bot.close()
