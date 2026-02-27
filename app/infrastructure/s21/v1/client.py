from typing import Callable

from app.infrastructure.s21.v1.models.auth.credentials import Credentials
from app.infrastructure.s21.v1.models.auth.session import Session
from app.infrastructure.s21.v1.models.responses.error import ErrorResponseDTO
from app.infrastructure.s21.v1.models.responses.student import ParticipantV1DTO

from aiohttp import ClientSession, ClientResponse

from app.infrastructure.s21.v1.models.responses.student_workstation import \
    ParticipantWorkstationV1DTO


class S21APIClient:
    """School 21 Platform API interface."""
    session: Session | None

    def __init__(self, base_url: str, auth_url: str, auth_realm: str,
                 credentials: Credentials | None) -> None:
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
        if credentials:
            cls.session = await cls.login(
                auth_url=auth_url,
                auth_realm=auth_realm,
                login=credentials.login,
                password=credentials.password,
            )
        else:
            raise ValueError("Credentials are required, when using from_credentials")

        return cls(base_url=base_url, auth_url=auth_url, auth_realm=auth_realm,
                   credentials=credentials)

    @classmethod
    async def from_session(
        cls, base_url: str, auth_url: str, auth_realm: str, session: Session | None = None
    ) -> "S21APIClient":
        """Initializing S21 API via provided session.

        This function try to check if session is valid - otherwise, try to refresh
        via refresh token
        """
        if session:
            cls.session = session
            # Checking if session is valid, otherwise trying to use refresh
            # TODO: autorefresh and /me check
        else:
            raise ValueError("Session info is required, when using from_session")

        return cls(base_url=base_url, auth_url=auth_url, auth_realm=auth_realm,
                   credentials=None)

    # ------ REQUESTS ------

    async def request(
            self, func: Callable, url: str, body: dict | None, base_url: str | None = None,
            expected_status: int = 200, retryable: bool = True
    ) -> ClientResponse | ErrorResponseDTO:
        """Middleware, to redo the request if there has been an auth problem."""

        # Params check
        if body is None:
            body = {}
        if base_url is None:
            base_url = self.base_url

        # Validation of URL
        if url is None:
            raise ValueError("url is required")
        if not url[0] == "/":
            url = "/" + url

        url = f"{base_url}{url}"

        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {self.session.access_token}",
        }

        response: ClientResponse = await func(url=url, data=body, headers=headers)

        # Catching Unauthorized error
        if response.status == 401:
            # If current request is retryable, try to refresh session
            if retryable:
                # Refreshing current session
                self.session = await self.login(
                    auth_url=self.auth_url, auth_realm=self.auth_realm,
                    password=self.credentials.password, login=self.credentials.login,
                )

                response = await self.request(func, url, body, base_url=base_url,
                                              retryable=False)
            else:
                raise Exception("Unauthorized to S21 API")

        # Catching Forbidden error
        if response.status == 403:
            data = await response.json()
            self.handle_error(data, response)

        return response

    async def get(
            self, url: str, body: dict | None = None,
            retryable: bool = True, base_url: str | None = None
    ) -> ClientResponse | ErrorResponseDTO:
        """Using aiohttp session & GET function to make secure request to API."""
        async with ClientSession() as session:
            return await self.request(
                func=session.get, url=url, body=body,
                base_url=base_url, retryable=retryable
            )

    async def post(
            self, url: str, body: dict | None,
            retryable: bool = True, base_url: str | None = None
    ) -> ClientResponse | ErrorResponseDTO:
        """Using aiohttp session & POST function to make secure request to API."""
        async with ClientSession() as session:
            return await self.request(
                func=session.post, url=url, body=body,
                base_url=base_url, retryable=retryable
            )

    @staticmethod
    def handle_error(data: dict, response: ClientResponse) -> None:
        """Raising an exception, if ErrorResponseDTO or other has been returned."""
        print("ERROR", data, response)

        # Try to cast data into error response DTO, otherwise - just string data
        try:
            error = ErrorResponseDTO(**data)
            error_msg = (
                f"\nS21API Exception UUID: {error.exceptionUUID}, Status:"
                f" {error.status}, Message: {error.message}"
            )
        except:
            error_msg = str(data)

        status = response.status
        if status == 429:
            message = (
                "❗️Our service hit School 21 API limitation (429, Too Many "
                "Requests)!\n⏳ Please, try again in about 1 minute\nWe are very sorry "
                "for the inconvenience"
            )
        elif status == 500:
            message = (
                "❗️Error has occurred on School 21 API side. Please try again, "
                "it may be one-time error.\n\nIf error persists - contact @megaplov"
            )
        else:
            message = f"❗️Error response code: {status}\nError message: {error_msg}"

        raise Exception(message)

    # -------- AUTH --------

    @staticmethod
    async def login(
            auth_url: str, auth_realm: str, login: str | None = None,
            password: str | None = None,
    ) -> Session:
        """Using OIDC protocol to login into School 21 account, to use API."""
        # Parameters check
        if not all([auth_url, auth_realm]):
            raise Exception("auth url and realm are required to login")

        url = f"{auth_url}/auth/realms/{auth_realm}/protocol/openid-connect/token"

        # Request body, regarding OIDC protocol
        body = {"client_id": "s21-open-api"}
        if login and password:
            body["grant_type"] = "password"
            body["username"] = login
            body["password"] = password
        else:
            # Raise an error if none of login (re-login) methods were provided
            raise Exception("Either login and password are required")

        async with ClientSession() as session:
            response = await session.post(url=url, data=body)
            data = await response.json()

            # We're not using ErrorResponseDTO because it's separate service (built
            # on OIDC, not S21 API)
            if response.status == 401:
                # Invalid credentials
                raise Exception(
                    "Invalid credentials (login and password)"
                )
            elif response.status != 200:
                raise Exception(
                    f"Unknown error (code {response.status}): {data}"
                )

            access_token = data["access_token"]
            refresh_token = data["refresh_token"]

            # Checking if both access and refresh token are present in response
            if not all([access_token, refresh_token]):
                raise Exception(
                    "Couldn't retrieve access_token, refresh_token from response"
                )
            else:
                new_session = Session(
                    access_token=access_token,
                    refresh_token=refresh_token,
                )

                return new_session


    # ----- API CALLS ------

    async def get_student_by_nickname(self, nickname: str) -> (
            ParticipantV1DTO | ErrorResponseDTO | None):
        """Get student by his nickname."""

        # API requires nickname to be lowercase
        nickname = nickname.lower()

        url = f"/v1/participants/{nickname}"

        response = await self.get(url)

        # If result is okay - returning DTO of student data (or None, if not exists)
        if response.status == 200:
            data = await response.json()
            return ParticipantV1DTO(**data)
        elif response.status == 404:
            return None

        # And if it's not "Not found" - raising an error
        data = await response.json()
        return self.handle_error(data, response)

    async def get_student_workplace_by_nickname(self, nickname: str) -> (
            ParticipantWorkstationV1DTO | ErrorResponseDTO | None):
        """Get student's workplace by his nickname."""

        # API requires nickname to be lowercase
        nickname = nickname.lower()

        url = f"/v1/participants/{nickname}/workstation"

        response = await self.get(url)

        # If result is okay - returning DTO of student data (or None, if not exists)

        if response.status == 200:
            text = await response.text()
            # Checking if there is a response
            if text.strip():
                data = await response.json()
                return ParticipantWorkstationV1DTO(**data)
            else:
                return None
        elif response.status == 404:
            return None

        # And if it's not "Not found" - raising an error
        data = await response.json()
        return self.handle_error(data, response)
