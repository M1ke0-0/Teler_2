from typing import List, Optional

from source.Logging import Logger
from source.Database.database import DatabaseManager, User, Channel
from source.Database.crud import CRUD
from source.TelegramMessageScrapper.PyroClient import PyroClient


class DataBaseHelper:
    """
    Обёртка над PostgreSQL для работы с БД.
    Интерфейс остаётся тот же, что и с MongoDB.
    Меняется только внутренняя реализация на SQLAlchemy + PostgreSQL.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        scrapper: Optional[PyroClient]
    ):
        self.logger = Logger("PostgreSQL", "network.log")
        self.db_manager = db_manager
        self.scrapper = scrapper
        self.crud = None

    @classmethod
    async def create(
        cls,
        db_url: str = "",
        scrapper: PyroClient = None
    ) -> "DataBaseHelper":
        """
        Фабричный метод для создания DataBaseHelper.
        
        Args:
            db_url: PostgreSQL connection string (postgresql+asyncpg://user:password@host/db)
            scrapper: PyroClient для скрейпинга сообщений
        
        Returns:
            Инициализированный DataBaseHelper
        """
        db_manager = DatabaseManager(db_url)
        await db_manager.init()
        self = cls(db_manager, scrapper)
        await self._setup()
        await self.logger.info("PostgreSQL connected")
        return self

    async def _setup(self):
        """Инициализация базы данных"""
        # Для проверки подключения просто пытаемся получить сессию
        async with self.db_manager.get_session() as session:
            # Просто проверка что подключение работает
            pass
        await self.logger.info("PostgreSQL connection established successfully")

    # ============= USER METHODS =============

    async def create_user(self, user_id: int, name: str) -> None:
        """
        Создать пользователя.
        Интерфейс совпадает с MongoDB версией.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            await crud.create_user(user_id, name)

    async def get_user(self, user_id: int):
        """Получить пользователя"""
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            user = await crud.get_user(user_id)
            
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            # crud.get_user() уже возвращает dict, просто возвращаем его
            return user

    async def delete_user(self, user_id: int) -> List[int]:
        """
        Удалить пользователя.
        Возвращает список ID каналов без подписчиков.
        Интерфейс совпадает с MongoDB версией.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            return await crud.delete_user(user_id)

    async def update_user_channels(
        self,
        user_id: int,
        add: Optional[List[int]] = None,
        remove: Optional[List[int]] = None
    ) -> List[int]:
        """
        Обновить каналы пользователя.
        Интерфейс совпадает с MongoDB версией.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            return await crud.update_user_channels(user_id, add, remove)

    # ============= CHANNEL METHODS =============

    async def create_channel(self, channel_id: int, name: str) -> None:
        """
        Создать канал.
        Интерфейс совпадает с MongoDB версией.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            await crud.create_channel(channel_id, name)

    async def get_channel(self, channel_id: int) -> dict:
        """
        Получить канал.
        Возвращаем в формате совместимом с Pydantic моделью.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            channel = await crud.get_channel(channel_id)
            return {
                "id": channel.id,
                "name": channel.name,
                "subscribers": channel.subscribers
            }

    async def delete_channel(self, channel_id: int) -> None:
        """
        Удалить канал.
        Интерфейс совпадает с MongoDB версией.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            await crud.delete_channel(channel_id)

    # ============= SUBSCRIPTION METHODS =============

    async def subscribe(self, user_id: int, channel_id: int) -> None:
        """Подписать пользователя на канал"""
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            await crud.subscribe(user_id, channel_id)

    async def unsubscribe(self, user_id: int, channel_id: int) -> bool:
        """
        Отписать пользователя от канала.
        Возвращает True если канал остался без подписчиков.
        """
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            return await crud.unsubscribe(user_id, channel_id)

    # ============= UTILITY METHODS =============

    async def get_all_users_for_channel(self, channel_id: int) -> List[int]:
        """Получить все ID пользователей подписанных на канал"""
        async with self.db_manager.get_session() as session:
            crud = CRUD(session, self.logger)
            users = await crud.get_all_users_for_channel(channel_id)
            return [u.id for u in users]

    async def close(self):
        """Закрыть подключение к БД"""
        await self.db_manager.close()
