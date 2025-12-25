# ai_agents/__init__.py
"""
ai_agents package – core utilities for the AI‑Agents Hub project.

The package currently provides:
* A global registry for agent classes (`AGENT_REGISTRY`).
* Helper functions to register and retrieve agents.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

# ----------------------------------------------------------------------
# Global registry
# ----------------------------------------------------------------------
AGENT_REGISTRY: Dict[str, Type["BaseAgent"]] = {}


def register_agent(cls: Type["BaseAgent"]) -> Type["BaseAgent"]:
    """
    Class decorator that registers an ``Agent`` subclass in ``AGENT_REGISTRY``.
    The key used is the class name (e.g., ``EchoAgent``).

    Example
    -------
    >>> @register_agent
    ... class MyAgent(BaseAgent):
    ...     ...

    The function returns the original class so it can be used normally.
    """
    AGENT_REGISTRY[cls.__name__] = cls
    return cls


def get_agent_class(name: str) -> Type["BaseAgent"]:
    """
    Retrieve an agent class by name from the registry.
    Raises ``KeyError`` if the name is not registered.
    """
    try:
        return AGENT_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Agent '{name}' is not registered.") from exc


def autodiscover_agents(package: str = __name__) -> None:
    """
    Walk the given ``package`` (default: the current ``ai_agents`` package)
    and import every submodule.  Importing a submodule triggers the
    ``@register_agent`` decorator on any ``BaseAgent`` subclasses it defines,
    thus populating ``AGENT_REGISTRY`` automatically.

    This function is optional – you can also import modules manually.
    """
    for _, mod_name, is_pkg in pkgutil.iter_modules(
        importlib.import_module(package).__path__
    ):
        full_name = f"{package}.{mod_name}"
        importlib.import_module(full_name)
        if is_pkg:
            autodiscover_agents(full_name)


# Auto‑discover agents on import so that the registry is ready.
autodiscover_agents()
