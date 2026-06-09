"""Domain registry — look up a domain by name."""

from __future__ import annotations

from csl.domain.base import Domain
from csl.domain.code_generation import CodeGenerationDomain

_FACTORIES = {
    CodeGenerationDomain.name: CodeGenerationDomain,
}


def get_domain(name: str, **kwargs) -> Domain:
    """Instantiate the registered domain ``name`` (kwargs forwarded to its constructor)."""
    try:
        factory = _FACTORIES[name]
    except KeyError:
        raise ValueError(f"unknown domain {name!r}; known: {sorted(_FACTORIES)}") from None
    return factory(**kwargs)


def available_domains() -> list[str]:
    return sorted(_FACTORIES)
