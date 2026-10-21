from app.domain.base_error import BaseError


class DuplicateUserError(BaseError):
    """Raised when user data conflicts with another 21ID user."""

    message = "Duplicate user"

    def __init__(  # noqa: B042
        self, *, support_details: dict | str | None = None
    ) -> None:
        """Initialize duplicate user error."""
        super().__init__(
            client_message=(
                "This account is already linked to another 21ID user. "
                "Contact @megaplov"
            ),
            support_details=support_details,
        )
