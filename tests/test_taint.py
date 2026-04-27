"""Tests for the tool_result_taint public surface."""

from __future__ import annotations

import pytest

from tool_result_taint import (
    Tainted,
    TaintReport,
    is_tainted,
    mark_tainted,
    taint_aware_dict,
    taint_report,
    unwrap_trusted,
)


def test_mark_tainted_returns_record_with_value_and_source():
    t = mark_tainted("balance: $42", source="bank.get_balance")
    assert isinstance(t, Tainted)
    assert t.value == "balance: $42"
    assert t.source == "bank.get_balance"
    assert t.tainted is True


def test_mark_tainted_requires_string_source():
    with pytest.raises(TypeError):
        mark_tainted("x", source=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        mark_tainted("x", source="")


def test_is_tainted_recognizes_tainted_record():
    assert is_tainted(mark_tainted("x", "tool")) is True


def test_is_tainted_recognizes_dict_shape_after_json_roundtrip():
    # Wire format: {"value": ..., "tainted": True, "source": ...}
    payload = {"value": "x", "tainted": True, "source": "tool"}
    assert is_tainted(payload) is True


def test_is_tainted_returns_false_for_plain_values():
    assert is_tainted("plain string") is False
    assert is_tainted({"value": "x"}) is False  # missing tainted=True
    assert is_tainted(None) is False
    assert is_tainted(42) is False


def test_unwrap_trusted_passes_plain_values_through():
    assert unwrap_trusted("hello") == "hello"
    assert unwrap_trusted({"some": "dict"}) == {"some": "dict"}
    assert unwrap_trusted(None) is None


def test_unwrap_trusted_raises_on_tainted_record():
    t = mark_tainted("secret", source="leaky.tool")
    with pytest.raises(RuntimeError) as exc:
        unwrap_trusted(t)
    assert "leaky.tool" in str(exc.value)


def test_unwrap_trusted_raises_on_dict_shape_taint():
    payload = {"value": "secret", "tainted": True, "source": "json.tool"}
    with pytest.raises(RuntimeError):
        unwrap_trusted(payload)


def test_taint_report_all_safe_when_no_tainted_inputs():
    report = taint_report(["plain", 42, {"untainted": True}])
    assert isinstance(report, TaintReport)
    assert report.safe is True
    assert report.tainted == []


def test_taint_report_collects_tainted_entries():
    a = mark_tainted("aa", source="tool-a")
    b = mark_tainted("bb", source="tool-b")
    report = taint_report([a, "plain", b])
    assert report.safe is False
    sources = [t["source"] for t in report.tainted]
    assert sources == ["tool-a", "tool-b"]


def test_taint_aware_dict_wraps_each_entry():
    out = taint_aware_dict({"name": "Alice", "ssn": "XXX"}, source="crm.lookup")
    assert isinstance(out["name"], Tainted)
    assert out["name"].value == "Alice"
    assert out["ssn"].source == "crm.lookup"


def test_taint_aware_dict_skips_already_tainted_by_default():
    pre = mark_tainted("x", source="prior.tool")
    out = taint_aware_dict({"a": pre, "b": "raw"}, source="new.tool")
    assert out["a"] is pre  # source preserved
    assert out["b"].source == "new.tool"


def test_taint_aware_dict_overwrites_when_skip_disabled():
    pre = mark_tainted("x", source="prior.tool")
    out = taint_aware_dict(
        {"a": pre},
        source="new.tool",
        skip_already_tainted=False,
    )
    assert out["a"].source == "new.tool"
    # Inner value is the entire prior Tainted record.
    assert out["a"].value is pre


def test_taint_aware_dict_rejects_non_mapping_input():
    with pytest.raises(TypeError):
        taint_aware_dict(["not", "a", "dict"], source="x")  # type: ignore[arg-type]


def test_tainted_record_is_frozen():
    t = mark_tainted("x", source="tool")
    with pytest.raises(Exception):
        t.source = "other"  # type: ignore[misc]


def test_js_alias_names_are_exported():
    from tool_result_taint import markTainted, taintReport, unwrapTrusted

    assert markTainted is mark_tainted
    assert taintReport is taint_report
    assert unwrapTrusted is unwrap_trusted
