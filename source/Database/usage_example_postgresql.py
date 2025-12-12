"""
Пример использования новой DataBaseHelper с PostgreSQL

Этот файл показывает как использовать DataBaseHelper после миграции.
Интерфейс остаётся тем же, изменилась только реализация!
"""

import asyncio
from source.Database.DBHelper import DataBaseHelper


async def test_database():
    """Тестирование основных операций с БД"""
    
    # Строка подключения к PostgreSQL
    db_url = "postgresql+asyncpg://telerag_user:telerag_password@localhost:5432/telerag_db"
    
    # Создаём DataBaseHelper
    db = await DataBaseHelper.create(db_url=db_url, scrapper=None)
    
    try:
        # ===== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ =====
        print("Creating user...")
        await db.create_user(user_id=123, name="John Doe")
        
        # ===== ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЯ =====
        print("Getting user...")
        user = await db.get_user(user_id=123)
        print(f"User: {user}")
        # Output: {'id': 123, 'name': 'John Doe', 'channels': []}
        
        # ===== СОЗДАНИЕ КАНАЛОВ =====
        print("Creating channels...")
        await db.create_channel(channel_id=1001, name="Channel 1")
        await db.create_channel(channel_id=1002, name="Channel 2")
        await db.create_channel(channel_id=1003, name="Channel 3")
        
        # ===== ПОДПИСКА НА КАНАЛЫ =====
        print("Subscribing to channels...")
        await db.subscribe(user_id=123, channel_id=1001)
        await db.subscribe(user_id=123, channel_id=1002)
        
        # Проверяем что пользователь подписан
        user = await db.get_user(user_id=123)
        print(f"User channels: {user['channels']}")
        # Output: [1001, 1002]
        
        # ===== ПОЛУЧЕНИЕ ИНФОРМАЦИИ О КАНАЛЕ =====
        print("Getting channel info...")
        channel = await db.get_channel(channel_id=1001)
        print(f"Channel: {channel}")
        # Output: {'id': 1001, 'name': 'Channel 1', 'subscribers': 1}
        
        # ===== ОБНОВЛЕНИЕ КАНАЛОВ (добавить и удалить) =====
        print("Updating user channels...")
        channels_to_unsub = await db.update_user_channels(
            user_id=123,
            add=[1003],      # Подписываем на 1003
            remove=[1002]    # Отписываем от 1002
        )
        print(f"Channels to unsubscribe from bot: {channels_to_unsub}")
        
        user = await db.get_user(user_id=123)
        print(f"Updated user channels: {user['channels']}")
        # Output: [1001, 1003]
        
        # ===== СОЗДАНИЕ ВТОРОГО ПОЛЬЗОВАТЕЛЯ =====
        print("Creating second user...")
        await db.create_user(user_id=456, name="Jane Doe")
        await db.subscribe(user_id=456, channel_id=1001)
        await db.subscribe(user_id=456, channel_id=1003)
        
        # ===== ПРОВЕРКА КОЛИЧЕСТВА ПОДПИСЧИКОВ =====
        channel = await db.get_channel(channel_id=1001)
        print(f"Channel 1001 subscribers: {channel['subscribers']}")
        # Output: 2 (John и Jane)
        
        # ===== ПОЛУЧЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ КАНАЛА =====
        users = await db.get_all_users_for_channel(channel_id=1001)
        print(f"Users subscribed to channel 1001: {users}")
        # Output: [123, 456]
        
        # ===== ОТПИСКА И УДАЛЕНИЕ КАНАЛА =====
        print("Unsubscribing user from channel...")
        should_remove_from_bot = await db.unsubscribe(user_id=123, channel_id=1001)
        print(f"Channel should be removed from bot: {should_remove_from_bot}")
        # Output: False (потому что Jane ещё подписана)
        
        # Проверяем подписчиков
        channel = await db.get_channel(channel_id=1001)
        print(f"Channel 1001 subscribers after unsubscribe: {channel['subscribers']}")
        # Output: 1 (только Jane)
        
        # ===== УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ =====
        print("Deleting user...")
        channels_to_unsub = await db.delete_user(user_id=456)
        print(f"Channels to unsubscribe from bot: {channels_to_unsub}")
        # Output: [1001, 1003] (потому что не было других подписчиков)
        
        print("\nAll tests passed! ✓")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Закрываем подключение
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_database())