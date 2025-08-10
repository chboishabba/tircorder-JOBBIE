"""Plugins for importing data from account management software."""

from .base import AccountPlugin

try:  # Optional dependency
    from .firefly_plugin import FireflyIIIPlugin
except Exception:  # pragma: no cover - dependency not installed
    FireflyIIIPlugin = None  # type: ignore

try:
    from .gnucash_plugin import GnuCashPlugin
except Exception:  # pragma: no cover - dependency not installed
    GnuCashPlugin = None  # type: ignore

from .kmymoney_plugin import KMyMoneyPlugin
from .moneymanagerex_plugin import MoneyManagerExPlugin
from .quicken_plugin import QuickenPlugin

__all__ = [
    "AccountPlugin",
    "FireflyIIIPlugin",
    "GnuCashPlugin",
    "KMyMoneyPlugin",
    "MoneyManagerExPlugin",
    "QuickenPlugin",
]
