from typing import AsyncGenerator

from app.domain.chat.chat import Chat
from app.infrastructure.mongodb.repositories.chat import ChatRepository


class ChatService:
    """Chats service."""

    def __init__(self, repo: ChatRepository | None):
        """Initialize Chat Service."""

        # Params check
        if not all([repo]):
            raise ValueError("Chat Repository is required")

        self.repo = repo

    async def get_all(self) -> AsyncGenerator[Chat]:
        """Get all chats."""
        cursor = self.repo.get_all()

        async for document in cursor:
            if document:
                chat = Chat(**document)
                yield chat

    async def get_all_public(self) -> AsyncGenerator[Chat]:
        """Get all chats."""
        cursor = self.repo.get_all_public()

        async for document in cursor:
            if document:
                chat = Chat(**document)
                yield chat

    async def get_by_telegram_id(self, chat_id: int) -> Chat | None:
        """Get chat by its Telegram's chat id."""
        document = await self.repo.get_by_telegram_id(chat_id)

        chat = None
        if document:
            chat = Chat(**document)

        return chat

    async def upsert(self, chat: Chat) -> None:
        """Get chat by its Telegram's chat id."""
        chat_data = chat.model_dump()

        await self.repo.upsert(chat_data, chat.chat_id)

    async def update_topic_id(self, chat_id: int, topic_id: int) -> bool:
        """Update topic id of a chat."""
        res = await self.repo.update(chat_id,
                                     update={"$set": {"id_topic_id": topic_id}})

        if res.modified_count == 1:
            return True
        return False

    async def set_allow_intensive(self, chat_id: int, result: bool) -> bool:
        """Setting if chat may allow intensive students."""
        res = await self.repo.update(chat_id,
                                     update={"$set": {"intensive_allowed": result}})

        if res.modified_count == 1:
            return True
        return False

    async def set_allow_core(self, chat_id: int, result: bool) -> bool:
        """Setting if chat may allow core education students."""
        res = await self.repo.update(chat_id, update={"$set": {"core_allowed": result}})

        if res.modified_count == 1:
            return True
        return False

    async def set_join_desc(self, chat_id: int, text: str | None = None) -> bool:
        """Setting description of a chat, which is sent on user join."""
        res = await self.repo.update(chat_id, update={"$set": {"desc_on_join": text}})

        if res.modified_count == 1:
            return True
        return False

    async def set_desc(self, chat_id: int, text: str | None = None) -> bool:
        """Setting description of a chat."""
        res = await self.repo.update(chat_id, update={"$set": {"description": text}})

        if res.modified_count == 1:
            return True
        return False

    async def set_title(self, chat_id: int, text: str | None = None) -> bool:
        """Setting title of a chat."""
        res = await self.repo.update(chat_id, update={"$set": {"title": text}})

        if res.modified_count == 1:
            return True
        return False

    async def set_join_link(self, chat_id: int, link: str) -> bool:
        """Setting join link."""
        res = await self.repo.update(chat_id,
                                     update={"$set": {"join_link": link}})

        if res.modified_count == 1:
            return True
        return False
