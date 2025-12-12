from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from contextlib import asynccontextmanager

# DeclarativeBase для всех моделей
Base = declarative_base()

# Many-to-Many таблица связи
user_channel_association = Table(
    'user_channels',
    Base.metadata,
    Column('user_id', BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('channel_id', BigInteger, ForeignKey('channels.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    """SQLAlchemy модель пользователя"""
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    
    # Связь many-to-many с каналами
    channels = relationship(
        'Channel',
        secondary=user_channel_association,
        back_populates='users',
        cascade='all, delete'
    )


class Channel(Base):
    """SQLAlchemy модель канала"""
    __tablename__ = 'channels'

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    
    # Связь many-to-many с пользователями
    users = relationship(
        'User',
        secondary=user_channel_association,
        back_populates='channels',
        cascade='all, delete'
    )

    @property
    def subscribers(self) -> int:
        """Количество подписчиков канала"""
        return len(self.users)


class DatabaseManager:
    """Менеджер для работы с подключением к БД"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.async_session_maker = None
    
    async def init(self):
        """Инициализация асинхронного движка и сессий"""
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Создание таблиц (используется Alembic)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Удаление таблиц (осторожно!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def get_session(self):
        """Async context manager для получения сессии БД"""
        session = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    
    async def close(self):
        """Закрыть подключение"""
        if self.engine:
            await self.engine.dispose()