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


class ServerNotFoundError(SecVPNError):
    def __init__(self, server_id: int) -> None:
        super().__init__(f"Server not found: {server_id}")
        self.server_id = server_id
