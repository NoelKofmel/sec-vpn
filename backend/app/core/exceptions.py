class SecVPNError(Exception):
    pass


class EmailAlreadyExistsError(SecVPNError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email already registered: {email}")
        self.email = email


class InvalidCredentialsError(SecVPNError):
    pass


class InvalidTokenError(SecVPNError):
    pass
