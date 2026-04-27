"""tool_result_taint -- track untrusted tool output before it reaches prompts.

Public surface (mirrors the JS sibling, plus Pythonic helpers):

    from tool_result_taint import (
        mark_tainted,
        is_tainted,
        taint_aware_dict,
        taint_report,
        unwrap_trusted,
        Tainted,
        TaintReport,
    )

* ``mark_tainted(value, source)`` -- wrap a raw tool result as ``Tainted``.
* ``is_tainted(value)`` -- predicate for "should this be reviewed?"
* ``taint_aware_dict(mapping, source)`` -- shallow-wrap each value in a dict.
* ``taint_report(inputs)`` -- aggregate audit of a list.
* ``unwrap_trusted(value)`` -- guard that raises on tainted input.
"""

from .taint import (
    Tainted,
    TaintReport,
    is_tainted,
    mark_tainted,
    taint_aware_dict,
    taint_report,
    unwrap_trusted,
)

# JS-name aliases for cross-language search-and-port parity.
markTainted = mark_tainted
taintReport = taint_report
unwrapTrusted = unwrap_trusted

__version__ = "0.1.0"
VERSION = __version__

__all__ = [
    "VERSION",
    "Tainted",
    "TaintReport",
    "is_tainted",
    "mark_tainted",
    "markTainted",
    "taint_aware_dict",
    "taint_report",
    "taintReport",
    "unwrap_trusted",
    "unwrapTrusted",
]
