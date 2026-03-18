"""Custom exception hierarchy for the Menu Planner application.

All application-specific exceptions inherit from AppError so that
controllers can catch a single base type instead of bare Exception.
"""


class AppError(Exception):
    """Base class for all application errors."""


# --- Domain-layer errors ---


class DomainError(AppError):
    """Violation of a domain rule (e.g. invalid entity state)."""


class InvalidEntityError(DomainError):
    """Entity invariant violated (e.g. MenuSlot with both recipe and product)."""


class UnitConversionError(DomainError):
    """Incompatible or unknown measurement units."""


class CurrencyMismatchError(DomainError):
    """Attempt to combine Money values with different currencies."""


# --- Application-layer errors ---


class EntityNotFoundError(AppError):
    """Requested entity does not exist."""


# --- Authentication errors ---


class AuthenticationError(AppError):
    """Invalid credentials or token."""


class UserAlreadyExistsError(AppError):
    """Attempt to register with an already-used email."""


class ImportValidationError(AppError):
    """Uploaded file has invalid format or data."""


class CircularDependencyError(DomainError):
    """Adding this sub-recipe would create a circular dependency."""


class NestingDepthExceededError(DomainError):
    """Recipe nesting exceeds the maximum allowed depth."""


class SubRecipeWeightError(DomainError):
    """Sub-recipe used with a weight unit but the recipe has zero weight."""


# --- Infrastructure-layer errors ---


class RepositoryError(AppError):
    """Failure in the persistence layer."""
