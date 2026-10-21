import asyncio
from typing import Callable
from urllib.parse import quote

from app.infrastructure.s21.v1.models.auth.credentials import Credentials
from app.infrastructure.s21.v1.models.auth.session import Session
from app.infrastructure.s21.v1.models.errors.client_error import S21ClientError
from app.infrastructure.s21.v1.models.responses.error import ErrorResponseDTO
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO
from app.infrastructure.s21.v1.models.responses.student_workstation import (
    ParticipantWorkstationV1DTO,
)

import sentry_sdk
from aiohttp import ClientSession, ClientResponse, ClientTimeout
from pydantic import ValidationError

RETRYABLE_STATUSES = (500, 502, 503, 504)


class S21APIClient:
    """School 21 Platform API interface."""

    def __init__(
        self,
        base_url: str,
        auth_url: str,
        auth_realm: str,
        credentials: Credentials | None,
        session: Session | None = None,
    ) -> None:
        """Initialize S21 API class."""
        # Parameters check
        if not all([base_url, auth_url]):
            raise ValueError("base_url and auth_url of API is required")

        # API urls security check
        if not base_url.startswith("https://") or not auth_url.startswith("https://"):
            raise ValueError(
                "base_url and auth_url should be secure (use https protocol)"
            )

        # Setting API params
        self.base_url = base_url

        # Setting auth params
        self.auth_url = auth_url
        self.auth_realm = auth_realm
        self.credentials = credentials
        self.session = session

        # Shared HTTP session (created lazily inside running event loop)
        self._http: ClientSession | None = None
        self._login_lock = asyncio.Lock()

    # ------ INITIALIZATION ------

    @classmethod
    async def from_credentials(
        cls,
        base_url: str,
        auth_url: str,
        auth_realm: str,
        credentials: Credentials | None = None,
    ) -> "S21APIClient":
        """Initializing S21 API via user credentials.

        This function assumptions that provided credentials are valid, otherwise -
        raises an error
        """
        if not credentials:
            raise ValueError("Credentials are required, when using from_credentials")

        client = cls(
            base_url=base_url,
            auth_url=auth_url,
            auth_realm=auth_realm,
            credentials=credentials,
        )
        client.session = await client.login(
            login=credentials.login, password=credentials.password
        )
        return client

    @classmethod
    async def from_session(
        cls,
        base_url: str,
        auth_url: str,
        auth_realm: str,
        session: Session | None = None,
    ) -> "S21APIClient":
        """Initializing S21 API via provided session."""
        if not session:
            raise ValueError("Session info is required, when using from_session")

        return cls(
            base_url=base_url,
            auth_url=auth_url,
            auth_realm=auth_realm,
            credentials=None,
            session=session,
        )

    def _get_http(self) -> ClientSession:
        """Return shared aiohttp session, creating it if needed."""
        if self._http is None or self._http.closed:
            self._http = ClientSession(timeout=ClientTimeout(total=10))
        return self._http

    async def close(self) -> None:
        """Close shared aiohttp session."""
        if self._http is not None and not self._http.closed:
            await self._http.close()

    # ------ REQUESTS ------

    async def request(  # noqa: C901
        self,
        func: Callable,
        url: str,
        body: dict | None,
        base_url: str | None = None,
        retryable: bool = True,
        retry_5xx: bool = True,
    ) -> ClientResponse:
        """Make request, re-login on 401 and retry once on 5xx.

        Response body is buffered before return, so it can be read after the
        connection is released.
        """
        if base_url is None:
            base_url = self.base_url

        # Validation of URL
        if not url:
            raise ValueError("url is required")

        # Add base URL, if url doesn't start with base_url
        if not url.startswith(base_url):
            if not url[0] == "/":
                url = "/" + url
            url = f"{base_url}{url}"

        access_token = self.session.access_token
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {access_token}",
        }

        kwargs = {"url": url, "headers": headers}
        if body is not None:
            kwargs["data"] = body

        async with func(**kwargs) as response:
            await response.read()

        # Catching Unauthorized error
        if response.status == 401:
            if not retryable:
                raise S21ClientError(
                    client_message="Error with School 21 server authorization",
                    support_details={"message": "Unauthorized to School 21 API"},
                )
            await self.relogin(expired_token=access_token)
            return await self.request(
                func, url, body, base_url=base_url, retryable=False, retry_5xx=retry_5xx
            )

        # Catching Forbidden error
        if response.status == 403:
            self.handle_error(await self._json_or_text(response), response)

        # Retrying request once after 5xx error
        if response.status in RETRYABLE_STATUSES and retry_5xx:
            sentry_sdk.add_breadcrumb(
                category="s21api",
                level="warning",
                message=f"Retrying {response.status} request",
                data={"url": url},
            )
            await asyncio.sleep(0.5)
            return await self.request(
                func, url, body, base_url=base_url, retryable=retryable, retry_5xx=False
            )

        return response

    async def get(
        self, url: str, retryable: bool = True, base_url: str | None = None
    ) -> ClientResponse:
        """Make GET request to API via shared session."""
        return await self.request(
            func=self._get_http().get,
            url=url,
            body=None,
            base_url=base_url,
            retryable=retryable,
        )

    async def post(
        self,
        url: str,
        body: dict | None,
        retryable: bool = True,
        base_url: str | None = None,
    ) -> ClientResponse:
        """Make POST request to API via shared session."""
        return await self.request(
            func=self._get_http().post,
            url=url,
            body=body or {},
            base_url=base_url,
            retryable=retryable,
        )

    @staticmethod
    async def _json_or_text(response: ClientResponse) -> dict | str:
        """Parse response body as JSON, falling back to raw text."""
        try:
            return await response.json(content_type=None)
        except ValueError:
            return await response.text()

    @staticmethod
    def handle_error(data: dict | str, response: ClientResponse) -> None:
        """Raising an exception, if ErrorResponseDTO or other has been returned."""
        # Try to cast data into error response DTO, otherwise - just string data
        try:
            error = ErrorResponseDTO(**data)
            error_msg = (
                f"\nS21API Exception UUID: {error.exceptionUUID}, Status:"
                f" {error.status}, Message: {error.message}"
            )
        except TypeError, ValidationError:
            error_msg = str(data)

        status = response.status
        if status == 429:
            message = (
                "❗️Our service hit School 21 API limitation (429, Too Many "
                "Requests)!\n⏳ Please, try again in about 1 minute\nWe are very sorry "
                "for the inconvenience"
            )
        elif status in RETRYABLE_STATUSES:
            message = (
                "❗️Error has occurred on School 21 API side. Please try again, "
                "it may be one-time error.\n\nIf error persists - contact @megaplov"
            )
        else:
            message = f"❗️Error response code: {status}\nError message: {error_msg}"

        raise S21ClientError(
            client_message=message,
            support_details={"data": data, "status": status, "url": str(response.url)},
        )

    # -------- AUTH --------

    async def relogin(self, expired_token: str) -> None:
        """Refresh session (refresh token first, then password), once per expiry."""
        async with self._login_lock:
            # Another coroutine has already refreshed the session
            if self.session.access_token != expired_token:
                return

            try:
                self.session = await self.login(
                    refresh_token=self.session.refresh_token
                )
                return
            except S21ClientError as e:
                if not self.credentials:
                    raise
                sentry_sdk.add_breadcrumb(
                    category="s21api",
                    level="warning",
                    message="Refresh token grant failed, using password",
                    data={"details": str(e.support_details)},
                )

            self.session = await self.login(
                login=self.credentials.login,
                password=self.credentials.password,
            )

    async def login(
        self,
        login: str | None = None,
        password: str | None = None,
        refresh_token: str | None = None,
    ) -> Session:
        """Using OIDC protocol to login into School 21 account, to use API."""
        # Parameters check
        if not all([self.auth_url, self.auth_realm]):
            raise S21ClientError(
                support_details="auth url and realm are required to login",
                notify_user=False,
            )

        url = (
            f"{self.auth_url}/auth/realms/{self.auth_realm}"
            "/protocol/openid-connect/token"
        )

        # Request body, regarding OIDC protocol
        body = {"client_id": "s21-open-api"}
        if refresh_token:
            body["grant_type"] = "refresh_token"
            body["refresh_token"] = refresh_token
        elif login and password:
            body["grant_type"] = "password"
            body["username"] = login
            body["password"] = password
        else:
            # Raise an error if none of login (re-login) methods were provided
            raise S21ClientError(
                support_details="Either refresh token or login and password are "
                "required",
                notify_user=False,
            )

        async with self._get_http().post(url=url, data=body) as response:
            # We're not using ErrorResponseDTO because it's separate service (built
            # on OIDC, not S21 API)
            if response.status == 401:
                raise S21ClientError(
                    support_details="Invalid credentials (login and password)",
                    notify_user=False,
                )
            elif response.status != 200:
                raise S21ClientError(
                    support_details=f"Unknown auth error (code {response.status}): "
                    f"{await response.text()}",
                    notify_user=False,
                )
            data = await response.json()

        access_token = data.get("access_token")
        new_refresh_token = data.get("refresh_token")

        # Checking if both access and refresh token are present in response
        if not all([access_token, new_refresh_token]):
            raise S21ClientError(
                support_details="Couldn't retrieve access_token, "
                "refresh_token from response",
                notify_user=False,
            )

        return Session(access_token=access_token, refresh_token=new_refresh_token)

    # ----- API CALLS ------

    async def get_student_by_nickname(self, nickname: str) -> ParticipantV1DTO | None:
        """Get student by his nickname."""
        # API requires nickname to be lowercase
        nickname = quote(nickname.lower(), safe="")

        response = await self.get(f"/v1/participants/{nickname}")

        # If result is okay - returning DTO of student data (or None, if not exists)
        if response.status == 200:
            data = await response.json()
            return ParticipantV1DTO(**data)
        elif response.status == 404:
            return None

        # And if it's not "Not found" - raising an error
        return self.handle_error(await self._json_or_text(response), response)

    async def get_student_workplace_by_nickname(
        self, nickname: str
    ) -> ParticipantWorkstationV1DTO | None:
        """Get student's workplace by his nickname."""
        # API requires nickname to be lowercase
        nickname = quote(nickname.lower(), safe="")

        response = await self.get(f"/v1/participants/{nickname}/workstation")

        # If result is okay - returning DTO of student data (or None, if not exists)
        if response.status == 200:
            text = await response.text()
            # Checking if there is a response
            if text.strip():
                data = await response.json()
                return ParticipantWorkstationV1DTO(**data)
            return None
        elif response.status == 404:
            return None

        # And if it's not "Not found" - raising an error
        return self.handle_error(await self._json_or_text(response), response)
