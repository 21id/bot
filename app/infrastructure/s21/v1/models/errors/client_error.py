from app.domain.base_error import BaseError


class S21ClientError(BaseError):
    """School 21 API Client Error"""
    message = "Error occurred when working with School 21 API"
