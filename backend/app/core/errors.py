class NotFoundError(Exception):
    """The requested item does not exist (API: 404)."""


class InvalidStateError(Exception):
    """The action is not allowed in the item's current state (API: 409)."""


class InvalidInputError(Exception):
    """The input is not acceptable, e.g. too large or the wrong file type (API: 422)."""
