import asyncio
from os import getenv

from app.bootstrap import bootstrap
from app.bot.bot import main as start_bot


async def main(
    s21api_base_url: str,
    s21api_auth_url: str,
    s21api_auth_realm: str,
    s21api_login: str,
    s21api_password: str,
    botapi_token: str,
    admin_id: int,
    mongo_uri: str,
    mongo_dbname: str,
    templates_basedir: str,
    smtp_host: str,
    smtp_port: int,
    smtp_login: str,
    smtp_password: str,
    smtp_sender: str,
    redis_host: str,
    redis_password: str,
) -> None:
    """Logging in School 21 API and starting the Telegram bot."""
    # Parameters check
    if not all([s21api_base_url, s21api_auth_url, s21api_login, s21api_password,
                s21api_auth_realm]):
        raise Exception("Base and Auth URLs, credentials and auth realm are required")
    if not all([botapi_token, admin_id]):
        raise Exception("Bot API token and Admin TG ID are required")
    if not all([mongo_uri, mongo_dbname]):
        raise Exception("Mongo URI and DB name are required")
    if not all([redis_host, redis_password]):
        raise Exception("Redis host and password are required")
    if not all([templates_basedir]):
        raise Exception("Templates base directory is required")
    if not all([smtp_host, smtp_port, smtp_login, smtp_password, smtp_sender]):
        raise Exception("SMTP params is required")

    container = await bootstrap(
        mongo_uri=mongo_uri,
        mongo_dbname=mongo_dbname,
        s21api_base_url=s21api_base_url,
        s21api_auth_url=s21api_auth_url,
        s21api_auth_realm=s21api_auth_realm,
        s21api_login=s21api_login,
        s21api_password=s21api_password,
        templates_basedir=templates_basedir,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_login=smtp_login,
        smtp_password=smtp_password,
        smtp_sender=smtp_sender,
        redis_host=redis_host,
        redis_password=redis_password
    )

    await start_bot(
        botapi_token=botapi_token,
        container=container
    )


if __name__ == "__main__":
    s21api_base_url_ = getenv("S21API_BASE_URL")
    s21api_auth_url_ = getenv("S21API_AUTH_URL")
    s21api_auth_realm_ = getenv("S21API_AUTH_REALM")
    s21api_login_ = getenv("S21API_LOGIN")
    s21api_password_ = getenv("S21API_PASSWORD")
    botapi_token_ = getenv("BOTAPI_TOKEN")
    admin_id_ = int(getenv("ADMIN_ID"))
    mongo_uri_ = getenv("MONGO_URI")
    mongo_dbname_ = getenv("MONGO_DB_NAME")
    templates_basedir_ = getenv("TEMPLATES_BASEDIR")
    smtp_host_ = getenv("SMTP_HOST")
    smtp_port_ = int(getenv("SMTP_PORT"))
    smtp_login_ = getenv("SMTP_LOGIN")
    smtp_password_ = getenv("SMTP_PASSWORD")
    smtp_sender_ = getenv("SMTP_SENDER")
    redis_host_ = getenv("REDIS_HOST")
    redis_password_ = getenv("REDIS_PASSWORD")

    asyncio.run(
        main(
            s21api_base_url=s21api_base_url_, s21api_auth_url=s21api_auth_url_,
            s21api_auth_realm=s21api_auth_realm_, s21api_login=s21api_login_,
            s21api_password=s21api_password_, botapi_token=botapi_token_,
            admin_id=admin_id_, mongo_uri=mongo_uri_, mongo_dbname=mongo_dbname_,
            templates_basedir=templates_basedir_, smtp_host=smtp_host_,
            smtp_port=smtp_port_, smtp_login=smtp_login_,
            smtp_password=smtp_password_, smtp_sender=smtp_sender_,
            redis_host=redis_host_, redis_password=redis_password_
        )
    )
