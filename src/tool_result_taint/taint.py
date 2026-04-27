"""Taint tracking primitives for tool output.

Mirrors the JS sibling (``markTainted`` / ``taintReport`` / ``unwrapTrusted``)
with a Pythonic dataclass record (``Tainted``) and an extra ``taint_aware_dict``
helper that walks a single-level mapping and wraps every value.

Design notes:

* ``Tainted`` is a frozen dataclass so callers can't accidentally mutate the
  source field after the fact. The ``tainted`` boolean is stored alongside the
  value to keep wire-format parity with the JS object shape
  (``{"value", "tainted": True, "source"}``) for serialization.
* ``is_tainted`` accepts both ``Tainted`` instances and bare dicts that look
  taint-shaped, so values round-tripped through JSON still report correctly.
* ``unwrap_trusted`` raises ``RuntimeError`` (rather than silently passing
  through) so that misuse fails loudly in CI / tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class Tainted:
    """A wrapper marking a value as untrusted tool output.

    Attributes:
        value: The original tool result (any type).
        source: Identifier of the tool that produced ``value`` (e.g. tool name).
        tainted: Always ``True``; included for JSON parity with the JS sibling.
    """

    value: Any
    source: str
    tainted: bool = True


@dataclass
class TaintReport:
    """Aggregated audit of a batch of inputs.

    Attributes:
        safe: ``True`` iff none of the inputs are tainted.
        tainted: One ``{"source", "value"}`` dict per tainted input.
    """

    safe: bool
    tainted: List[dict] = field(default_factory=list)


def mark_tainted(value: Any, source: str) -> Tainted:
    """Wrap ``value`` as a tainted tool result attributed to ``source``.

    Args:
        value: The raw tool output (string, dict, anything).
        source: A short identifier of the originating tool, e.g. ``"web.fetch"``.

    Returns:
        A :class:`Tainted` record carrying ``value`` and ``source``.

    Raises:
        TypeError: If ``source`` is not a string.
    """
    if not isinstance(source, str) or not source:
        raise TypeError("mark_tainted: source must be a non-empty string")
    return Tainted(value=value, source=source)


def is_tainted(value: Any) -> bool:
    """Return ``True`` if ``value`` is (or looks like) a tainted record."""
    if isinstance(value, Tainted):
        return True
    if isinstance(value, Mapping):
        # JSON-roundtripped shape: {"value": ..., "tainted": True, "source": ...}
        return bool(value.get("tainted")) and "value" in value
    return False


def taint_aware_dict(
    mapping: Mapping[str, Any],
    source: str,
    *,
    skip_already_tainted: bool = True,
) -> dict:
    """Shallow-wrap every entry of ``mapping`` with :func:`mark_tainted`.

    Useful when an entire tool result dict is untrusted and you want each leaf
    to carry attribution, e.g. so that downstream filtering can pick out
    individual tainted fields.

    Args:
        mapping: Source dict; not mutated.
        source: Attribution stamped on each wrapped value.
        skip_already_tainted: If ``True`` (default), values already tainted
            are passed through unchanged so attribution isn't overwritten.

    Returns:
        A new dict with the same keys and tainted values.
    """
    if not isinstance(mapping, Mapping):
        raise TypeError("taint_aware_dict: mapping must be a Mapping")
    out: dict = {}
    for key, val in mapping.items():
        if skip_already_tainted and is_tainted(val):
            out[key] = val
        else:
            out[key] = mark_tainted(val, source)
    return out


def taint_report(inputs: Iterable[Any]) -> TaintReport:
    """Aggregate a batch of inputs into a :class:`TaintReport`.

    Mirrors the JS sibling's ``taintReport``: returns ``safe=True`` when no
    inputs are tainted, plus a list describing each tainted entry.
    """
    tainted_entries: List[dict] = []
    for item in inputs:
        if isinstance(item, Tainted):
            tainted_entries.append({"source": item.source, "value": item.value})
        elif isinstance(item, Mapping) and is_tainted(item):
            tainted_entries.append(
                {"source": item.get("source"), "value": item.get("value")}
            )
    return TaintReport(safe=len(tainted_entries) == 0, tainted=tainted_entries)


def unwrap_trusted(value: Any) -> Any:
    """Return the underlying value -- but only if it isn't tainted.

    Raises:
        RuntimeError: If ``value`` is tainted (caller must explicitly review).

    Returns:
        The unwrapped value. For a non-tainted input, returns the value as-is.
    """
    if is_tainted(value):
        if isinstance(value, Tainted):
            raise RuntimeError(
                "Tainted tool result requires review (source="
                + repr(value.source)
                + ")"
            )
        # Mapping-shaped tainted record.
        raise RuntimeError(
            "Tainted tool result requires review (source="
            + repr(value.get("source") if isinstance(value, Mapping) else None)
            + ")"
        )
    return value
