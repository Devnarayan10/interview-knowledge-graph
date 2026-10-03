class NotFoundError(Exception):
    """Requested entity does not exist."""


class ConflictError(Exception):
    """Entity already exists."""


class BadRequestError(Exception):
    """Invalid request."""