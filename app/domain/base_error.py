class BaseError(Exception):
    """Base error."""
    message: str

    def __init__(self, *, client_message: dict | str | None = None,
                 support_details: dict | str | None = None,
                 notify_user: bool = True):
        """Base error initialization."""
        # Text for user
        self.client_message = client_message or ("No additional information provided. "
                                                 "Contact @megaplov")
        # Text for admin
        self.support_details = support_details or self.message
        # Setting if user should be notified, or only admin
        self.notify_user = notify_user

        super().__init__(self.message)
