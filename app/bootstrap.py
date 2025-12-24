from dataclasses import dataclass

from app.domain.chat.service import ChatService
from app.infrastructure.database.client import MongoClient
from app.infrastructure.database.repositories.chat import ChatRepository
from app.infrastructure.mailer.client import MailerClient
from app.infrastructure.mailer.renderer import TemplateRenderer
from app.infrastructure.s21.v1.models.auth.credentials import Credentials
from app.infrastructure.s21.v1.client import S21APIClient
from app.infrastructure.database.repositories.user import UserRepository
from app.domain.user.service import UserService

from redis.asyncio import Redis


@dataclass
class Container:
    """Services of 21ID app."""
    user_service: UserService
    chat_service: ChatService
    s21api_client: S21APIClient
    mail_client: MailerClient
    redis: Redis

async def bootstrap(
    *,
    mongo_uri: str,
    mongo_dbname: str,
    s21api_base_url: str,
    s21api_auth_url: str,
    s21api_auth_realm: str,
    s21api_login: str,
    s21api_password: str,
    templates_basedir: str,
    smtp_host: str,
    smtp_port: int,
    smtp_login: str,
    smtp_password: str,
    smtp_sender: str,
    redis_host: str,
    redis_password: str
) -> Container:
    """Initialization of infra (database) -> repos (db mappers) -> services
    (providers)."""

    # - - - Infrastructure - - -
    redis = Redis(
        host=redis_host, password=redis_password, socket_connect_timeout=2,
        decode_responses=True,
    )
    # Checking Redis connection
    await redis.ping()

    mongo = MongoClient(uri=mongo_uri, db_name=mongo_dbname)

    if not mongo.client.admin.command('ping'):
        raise Exception("Mongo connection failed")

    s21api_client = await S21APIClient.from_credentials(
        base_url=s21api_base_url,
        auth_url=s21api_auth_url,
        auth_realm=s21api_auth_realm,
        credentials=Credentials(
            login=s21api_login,
            password=s21api_password,
        ),
    )

    template_renderer = TemplateRenderer(
        templates_dir=templates_basedir
    )

    mailer = await MailerClient.initialize(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        login=smtp_login,
        password=smtp_password,
        sender=smtp_sender,
        template_renderer=template_renderer,
    )

    # - - - Repositories - - -
    user_repo = UserRepository(client=mongo)
    chat_repo = ChatRepository(client=mongo)

    # - - - - Services - - - -
    user_service = UserService(repo=user_repo)
    chat_service = ChatService(repo=chat_repo)
    
    return Container(
        user_service=user_service,
        chat_service=chat_service,
        s21api_client=s21api_client,
        mail_client=mailer,
        redis=redis
    )
