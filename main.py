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
from typing import List

from openai import AsyncClient

from config import get_config
from platforms import Message, Provider
from platforms.discord import DiscordProvider

logging.basicConfig(level=logging.INFO)


async def main():
    config = get_config()
    logging.debug(config)
    client = AsyncClient(
        api_key=config["api"]["key"], base_url=config["api"]["base_url"]
    )
    provider: Provider = DiscordProvider()
    task = asyncio.create_task(provider.start())
    async for message in provider.get_message_generator():
        async with provider.typing(message):
            messages = [{"role": "system", "content": config["bot"]["system_prompt"]}]
            context = await provider.get_message_context(message)
            context.append(message)
            messages.extend(to_openai_messages(context))
            print(messages)
            response = await client.chat.completions.create(
                messages=messages,
                model=config["bot"]["model"],
            )
            await provider.send_message(response.choices[0].message.content, message)


def to_openai_messages(messages: List[Message]) -> List:
    result = []
    for msg in messages:
        result.append(
            {
                "role": "assistant" if msg.is_our else "user",
                "content": msg.text if msg.is_our else f"{msg.author}:{msg.text}",
            }
        )
    return result


if __name__ == "__main__":
    asyncio.run(main())
