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

from abc import ABC, abstractmethod
from typing import Iterable, List


class Message:
    def __init__(self, text: str, author: str, is_our: bool):
        self.text: str = text
        self.author: str = author
        self.is_our: bool = is_our


class Provider(ABC):
    @abstractmethod
    async def send_message(self, message: str, reply_to: Message):
        pass

    @abstractmethod
    async def get_message_generator(self) -> Iterable[Message]:
        pass

    @abstractmethod
    async def get_message_context(self, message: Message) -> List[Message]:
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
