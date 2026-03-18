from __future__ import annotations

from dataclasses import dataclass

from .errors import ValidationError

MAX_PAGE = 15
MAX_SIZE = 30
VALID_SORTS = {"accuracy", "recency"}


def _validate_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        raise ValidationError("query must not be empty")
    return normalized


def _validate_sort(sort: str) -> str:
    normalized = sort.strip()
    if normalized not in VALID_SORTS:
        raise ValidationError("sort must be one of: accuracy, recency")
    return normalized


def _validate_page(page: int) -> int:
    if not 1 <= page <= MAX_PAGE:
        raise ValidationError("page must be between 1 and 15")
    return page


def _validate_size(size: int) -> int:
    if not 1 <= size <= MAX_SIZE:
        raise ValidationError("size must be between 1 and 30")
    return size


@dataclass(frozen=True)
class VideoSearchRequest:
    query: str
    sort: str = "accuracy"
    page: int = 1
    size: int = 10

    def __post_init__(self) -> None:
        object.__setattr__(self, "query", _validate_query(self.query))
        object.__setattr__(self, "sort", _validate_sort(self.sort))
        object.__setattr__(self, "page", _validate_page(self.page))
        object.__setattr__(self, "size", _validate_size(self.size))

    def to_params(self) -> dict[str, object]:
        return {
            "query": self.query,
            "sort": self.sort,
            "page": self.page,
            "size": self.size,
        }


@dataclass(frozen=True)
class VideoSearchAutoRequest:
    query: str
    size: int = 5

    def __post_init__(self) -> None:
        object.__setattr__(self, "query", _validate_query(self.query))
        object.__setattr__(self, "size", _validate_size(self.size))

