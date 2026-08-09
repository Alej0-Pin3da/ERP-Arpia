"""Shared response schemas — the ``{items, total}`` list contract (API-1)."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    """Page of items plus the total count of the FILTERED set.

    ``total`` ignores ``limit``/``offset`` — it is the count of the complete
    query the page was sliced from (design D1/D2, spec API-1).
    """

    items: list[T]
    total: int
