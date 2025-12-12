import asyncio

from source.Logging import Logger, LoggerComposer

from source.Database.DBHelper import DataBaseHelper
from source.TgUI.BotApp import BotApp
from source.ChromaАndRAG.Rag import RagClient

# from source.TelegramMessageScrapper.Base import Scrapper
from source.TelegramMessageScrapper.PyroClient import PyroClient

from source.DynamicConfigurationLoading import TGConfig


class TeleRagService:
    """
    The Tele rag Service class is responsible for managing the Telegram message scrapper and the RAG client.
    It handles the initialization, updating, and querying of channels and messages.
    """

    def __init__(self, settings: TGConfig):
        self.settings = settings

        self.logger_composer = LoggerComposer(
            loglevel=settings.LOG_LEVEL,
        )

        self.tele_rag_logger = Logger("TeleRag", "network.log")

        self.Scrapper = PyroClient(
            api_id=settings.PYRO_API_ID,
            api_hash=settings.PYRO_API_HASH,
            history_limit=settings.PYRO_HISTORY_LIMIT,
        )

        self.RagClient = RagClient(
            host=settings.RAG_HOST,
            port=settings.RAG_PORT,
            n_result=settings.RAG_N_RESULT,
            model=settings.SENTENCE_TRANSFORMER_MODEL,
            mistral_api_key=settings.MISTRAL_API_KEY,
            mistral_model=settings.MISTRAL_API_MODEL,
            scrapper=self.Scrapper,
        )

        self.DataBaseHelper = None

        self.BotApp = BotApp(
            token=settings.AIOGRAM_API_KEY,
            rag=self.RagClient,
            scrapper=self.Scrapper,
            db_helper=self.DataBaseHelper,
        )

        self.logger_composer.set_level_if_not_set()

        self.stop_event = asyncio.Event()
        self.register_stop_signal_handler()

    async def start(self):
        await self.__create_db(self.settings)
        await self.tele_rag_logger.info("Starting TeleRagService...")
        await self.RagClient.start_rag()
        await self.Scrapper.scrapper_start()
        await self.BotApp.start()

    async def idle(self):
        await self.tele_rag_logger.info(
            "Waiting for stop signal... Press Ctrl+C to stop.")
        await self.stop_event.wait()

        await self.tele_rag_logger.info(
            "Stop signal received. Stopping TeleRagService...")
        await self.Scrapper.scrapper_stop()
        await self.RagClient.stop()
        await self.BotApp.stop()

        self.stop_event.clear()

        await self.tele_rag_logger.info("TeleRagService stopped.")

    def __stop_signal_handler(self):
        self.stop_event.set()

    def register_stop_signal_handler(self):
        """
        Register a signal handler for stopping the service.
        """
        import signal

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self.__stop_signal_handler, )
        loop.add_signal_handler(signal.SIGINT, self.__stop_signal_handler, )

    async def __create_db(self, settings: TGConfig):
        """
        Create and initialize the database helper.
        Now uses PostgreSQL instead of MongoDB.
        """
        # Построение строки подключения к PostgreSQL
        db_url = self.construct_db_url(settings)

        self.DataBaseHelper = await DataBaseHelper.create(
            db_url=db_url,
            scrapper=self.Scrapper
        )

        self.BotApp.include_db(self.DataBaseHelper)

        # Удаляем settings для очистки памяти
        del self.settings

    @staticmethod
    def construct_db_url(settings: TGConfig) -> str:
        """
        Construct the PostgreSQL connection URL from settings.

        Format: postgresql+asyncpg://user:password@host:port/database
        """
        return (
            f"postgresql+asyncpg://"
            f"{settings.POSTGRES_USER}:"
            f"{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:"
            f"{settings.POSTGRES_PORT}/"
            f"{settings.POSTGRES_DB}"
        )