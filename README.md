# tool-result-taint-py

[![PyPI](https://img.shields.io/pypi/v/tool-result-taint-py.svg)](https://pypi.org/project/tool-result-taint-py/)
[![Python](https://img.shields.io/pypi/pyversions/tool-result-taint-py.svg)](https://pypi.org/project/tool-result-taint-py/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Track untrusted tool output before it enters prompts or actions.** Tag any value that came back from an LLM tool call as "tainted", carry that taint through your pipeline, and refuse to use it in a sensitive context until you've explicitly reviewed and unwrapped it. Zero runtime dependencies.

Python port of [@mukundakatta/tool-result-taint](https://github.com/MukundaKatta/tool-result-taint).

## Install

```bash
pip install tool-result-taint-py
```

## Usage

```python
from tool_result_taint import (
    mark_tainted,
    is_tainted,
    taint_aware_dict,
    taint_report,
    unwrap_trusted,
)

# Wrap raw tool output before it enters your prompt-building pipeline.
result = mark_tainted("balance: $4321.00", source="bank.get_balance")

is_tainted(result)        # True
result.value              # "balance: $4321.00"
result.source             # "bank.get_balance"

# Audit a batch of inputs (mix tainted + plain).
report = taint_report([result, "trusted-system-prompt"])
report.safe               # False
report.tainted            # [{"source": "bank.get_balance", "value": "..."}]

# Refuse to use a tainted value in a sensitive context.
try:
    unwrap_trusted(result)
except RuntimeError:
    pass  # Caller must explicitly review or sanitize first.

unwrap_trusted("plain trusted string")     # "plain trusted string"

# Wrap a dict so every entry is tainted automatically.
taint_aware_dict({"name": "Alice", "ssn": "XXX-XX-1234"}, source="crm.lookup")
# -> {"name": Tainted("Alice"), "ssn": Tainted("XXX-XX-1234")}
```

## API

| Symbol | Behavior |
|---|---|
| `mark_tainted(value, source)` | Wraps `value` in a `Tainted` record stamped with `source`. |
| `is_tainted(value)` | `True` for any `Tainted` record (or dict with `tainted=True`). |
| `taint_aware_dict(mapping, source)` | Returns a new dict with each entry wrapped via `mark_tainted`. |
| `taint_report(inputs)` | Aggregates a list of inputs into `TaintReport(safe, tainted)`. |
| `unwrap_trusted(value)` | Returns the raw value; raises if `is_tainted(value)`. |

See the JS sibling's [README](https://github.com/MukundaKatta/tool-result-taint) for the full design notes.
