class BaseError(Exception):
    """Base error."""
    message: str

    def __init__(self, *, client_message: str = None,
                 support_details: dict | None = None,):
        """Base error initialization."""
        self.client_message = client_message or ("No additional information provided. "
                                                 "Contact @megaplov")
        self.support_details = support_details or {}
        super().__init__(self.message)
