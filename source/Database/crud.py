from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from source.Database.database import User, Channel, user_channel_association
from source.Logging import Logger


class CRUD:
    """CRUD операции для работы с БД PostgreSQL"""
    
    def __init__(self, session: AsyncSession, logger: Logger):
        self.session = session
        self.logger = logger
    
    # ============= USER OPERATIONS =============
    
    async def create_user(self, user_id: int, name: str) -> None:
        """Создать пользователя"""
        existing_user = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        if existing_user.scalar_one_or_none():
            await self.logger.warning(f"User '{user_id}' already exists")
            raise ValueError("User already exists")
        
        user = User(id=user_id, name=name)
        self.session.add(user)
        await self.session.commit()
    
    async def get_user(self, user_id: int):
        """Получить пользователя с его каналами"""
        from sqlalchemy.orm import selectinload
        
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.channels))  # ← Подгружаем channels
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
    
        # Возвращаем dict с нужными полями
        return {
            'id': user.id,
            'name': user.name,
            'channels': [channel.id for channel in user.channels]  # ← Список ID каналов
        }

    
    async def delete_user(self, user_id: int) -> List[int]:
        """
        Удалить пользователя и вернуть список каналов,
        которые остались без подписчиков
        """
        user = await self.get_user(user_id)
        channels_to_unsubscribe = []
        
        # Получаем каналы пользователя
        channels = user.channels.copy()
        
        # Удаляем пользователя (каскадное удаление связей)
        await self.session.delete(user)
        await self.session.commit()
        
        # Проверяем какие каналы остались без подписчиков
        for channel in channels:
            # Обновляем БД перед проверкой
            refreshed_channel = await self.session.execute(
                select(Channel).where(Channel.id == channel.id).options(
                    selectinload(Channel.users)
                )
            )
            ch = refreshed_channel.scalar_one_or_none()
            
            if ch and ch.subscribers == 0:
                await self.delete_channel(ch.id)
                channels_to_unsubscribe.append(ch.id)
        
        return channels_to_unsubscribe
    
    # ============= CHANNEL OPERATIONS =============
    
    async def create_channel(self, channel_id: int, name: str) -> None:
        """Создать канал"""
        existing_channel = await self.session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        if existing_channel.scalar_one_or_none():
            await self.logger.warning(f"Channel '{channel_id}' already exists")
            raise ValueError("Channel already exists")
        
        channel = Channel(id=channel_id, name=name)
        self.session.add(channel)
        await self.session.commit()
    
    async def get_channel(self, channel_id: int) -> Channel:
        """Получить канал с его подписчиками"""
        stmt = select(Channel).where(Channel.id == channel_id).options(
            selectinload(Channel.users)
        )
        result = await self.session.execute(stmt)
        channel = result.scalar_one_or_none()
        
        if not channel:
            await self.logger.warning(f"Channel '{channel_id}' not found")
            raise ValueError("Channel not found")
        
        return channel
    
    async def delete_channel(self, channel_id: int) -> None:
        """Удалить канал (только если нет подписчиков)"""
        channel = await self.get_channel(channel_id)
        
        if channel.subscribers > 0:
            await self.logger.warning(
                f"Cannot delete channel '{channel_id}' - has {channel.subscribers} subscribers"
            )
            raise ValueError("Channel has subscribers")
        
        await self.session.delete(channel)
        await self.session.commit()
    
    # ============= SUBSCRIPTION OPERATIONS =============
    
    async def update_user_channels(self, user_id: int, add: list[int] = None, remove: list[int] = None):
        """Обновить список каналов пользователя"""
        from sqlalchemy.orm import selectinload
        
        # Получаем пользователя с подгруженными каналами
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.channels))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Текущие ID каналов
        current_channel_ids = {ch.id for ch in user.channels}
        
        # Добавляем новые каналы
        if add:
            for channel_id in add:
                if channel_id not in current_channel_ids:
                    channel_result = await self.session.execute(
                        select(Channel).where(Channel.id == channel_id)
                    )
                    channel = channel_result.scalar_one_or_none()
                    if channel:
                        user.channels.append(channel)
                        current_channel_ids.add(channel_id)
        
        # Удаляем каналы
        channels_to_remove = []
        if remove:
            for channel_id in remove:
                if channel_id in current_channel_ids:
                    channel_result = await self.session.execute(
                        select(Channel).where(Channel.id == channel_id)
                    )
                    channel = channel_result.scalar_one_or_none()
                    if channel:
                        user.channels.remove(channel)
                        current_channel_ids.discard(channel_id)
                        channels_to_remove.append(channel_id)
        
        await self.session.commit()
        
        # Возвращаем список удалённых каналов для отписки от Pyrogram
        return channels_to_remove

    
    async def subscribe(self, user_id: int, channel_id: int) -> None:
        """Подписать пользователя на канал"""
        user = await self.get_user(user_id)
        channel = await self.get_channel(channel_id)
        
        if channel not in user.channels:
            user.channels.append(channel)
            await self.session.commit()
    
    async def unsubscribe(self, user_id: int, channel_id: int) -> bool:
        """
        Отписать пользователя от канала
        Возвращает True если канал остался без подписчиков
        """
        user = await self.get_user(user_id)
        channel = await self.get_channel(channel_id)
        
        if channel in user.channels:
            user.channels.remove(channel)
            await self.session.commit()
            
            # Проверяем есть ли подписчики
            refreshed = await self.get_channel(channel_id)
            if refreshed.subscribers == 0:
                await self.delete_channel(channel_id)
                return True
        
        return False
    
    async def get_all_users_for_channel(self, channel_id: int) -> List[User]:
        """Получить всех пользователей подписанных на канал"""
        channel = await self.get_channel(channel_id)
        return channel.users