import uuid
from unittest.mock import AsyncMock, MagicMock

from app.bootstrap import Container
from app.domain.user.service import UserService
from app.domain.verification.service import VerificationService
from app.infrastructure.mongodb import migrations
from app.infrastructure.mongodb.client import MongoClient
from app.infrastructure.mongodb.repositories.user import UserRepository
from app.infrastructure.verification.email_otp import (
    EmailOtpProvider,
    MigrationOtpProvider,
)

import pytest
from redis.asyncio import Redis


def _docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_available() -> None:
    """Skip integration tests when Docker can't be reached."""
    if not _docker_available():
        pytest.skip("Docker is not available, skipping integration tests")


@pytest.fixture(scope="session")
def mongo_url(docker_available):
    from testcontainers.mongodb import MongoDbContainer

    with MongoDbContainer("mongo:7") as container:
        yield container.get_connection_url()


@pytest.fixture(scope="session")
def redis_address(docker_available):
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7") as container:
        yield (
            container.get_container_host_ip(),
            int(container.get_exposed_port(container.port)),
        )


@pytest.fixture
async def mongo(mongo_url):
    """Mongo client bound to a fresh database."""
    client = MongoClient(uri=mongo_url, db_name=f"test_{uuid.uuid4().hex[:12]}")
    yield client
    await client.client.drop_database(client.db.name)
    client.client.close()


@pytest.fixture
async def migrated_mongo(mongo):
    await migrations.run(mongo.db)
    return mongo


@pytest.fixture
async def redis(redis_address):
    host, port = redis_address
    r = Redis(host=host, port=port, decode_responses=True)
    await r.flushdb()
    yield r
    await r.flushdb()
    await r.aclose()


@pytest.fixture
def user_service(migrated_mongo) -> UserService:
    return UserService(repo=UserRepository(client=migrated_mongo))


@pytest.fixture
def mailer():
    m = MagicMock()
    m.send_from_template = AsyncMock(return_value=True)
    return m


@pytest.fixture
def verification_service(redis, mailer, user_service) -> VerificationService:
    return VerificationService(
        providers=[EmailOtpProvider(mail_client=mailer), MigrationOtpProvider()],
        redis=redis,
        user_service=user_service,
    )


@pytest.fixture
def container(
    user_service, verification_service, mailer, redis, migrated_mongo
) -> Container:
    """App container on real Mongo/Redis with mocked S21 API and mailer."""
    return Container(
        user_service=user_service,
        chat_service=MagicMock(),
        verification_service=verification_service,
        s21api_client=AsyncMock(),
        mail_client=mailer,
        redis=redis,
        mongo=migrated_mongo,
        admin_id=999,
    )
