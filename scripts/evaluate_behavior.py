#!/usr/bin/env python3
"""
Load and grade deterministic Engineering Workflow behavior evaluations.

The module reads JSON contracts, validates their case and assertion structure,
grades provider responses against exact fields and keyword alternatives, and
returns aggregate assertion and critical-failure summaries. It writes nothing
itself; callers such as the live runner persist the returned dictionaries.
Inputs are contract and response ``Path``/mapping values, with no third-party
dependencies or required configuration. Example: ``python -m unittest
discover -s tests -v`` exercises the contracts and grader.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RESPONSE_FIELDS = (
    "task_type",
    "route",
    "requires_authorization",
    "would_edit",
    "next_actions",
    "prohibited_actions",
    "evidence",
    "residual_risks",
)
ROUTES = {"Quick", "Standard", "Strict", "Explore"}
TRIGGER_FIELDS = ("id", "query", "should_trigger")


class ContractError(ValueError):
    """Raised when an evaluation data file violates its contract."""


def _read_json(path: Path) -> Any:
    """Read UTF-8 JSON from ``path`` and convert I/O or syntax errors to ``ContractError``."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON from {path}: {exc}") from exc


def _require(condition: bool, message: str) -> None:
    """Raise ``ContractError`` with ``message`` when a contract predicate is false."""
    if not condition:
        raise ContractError(message)


def _validate_case(case: Any, index: int) -> None:
    """Validate one behavior case, including required/forbidden assertion contracts."""
    _require(isinstance(case, dict), f"behavior case {index} must be an object")
    for field in ("id", "category", "prompt", "expect", "required", "forbidden"):
        _require(field in case, f"behavior case {index} missing {field}")
    _require(isinstance(case["id"], str) and case["id"], f"behavior case {index} id must be non-empty")
    _require(isinstance(case["expect"], dict), f"behavior case {case['id']} expect must be an object")
    for field in ("task_type", "route", "requires_authorization", "would_edit"):
        _require(field in case["expect"], f"behavior case {case['id']} missing expect.{field}")
    for field in ("task_type", "route", "requires_authorization", "would_edit"):
        alternative = f"{field}_any"
        if alternative in case["expect"]:
            _require(
                isinstance(case["expect"][alternative], list) and case["expect"][alternative],
                f"behavior case {case['id']} expect.{alternative} must be a non-empty list",
            )
    _require(case["expect"]["route"] in ROUTES, f"behavior case {case['id']} has invalid route")
    for field in ("requires_authorization", "would_edit"):
        _require(isinstance(case["expect"][field], bool), f"behavior case {case['id']} expect.{field} must be boolean")
    critical_fields = case.get("critical_fields", [])
    _require(isinstance(critical_fields, list), f"behavior case {case['id']} critical_fields must be a list")
    for assertion_kind in ("required", "forbidden"):
        assertions = case[assertion_kind]
        _require(isinstance(assertions, list), f"behavior case {case['id']} {assertion_kind} must be a list")
        ids: set[str] = set()
        for assertion in assertions:
            _require(isinstance(assertion, dict), f"behavior case {case['id']} {assertion_kind} item must be an object")
            for field in ("id", "fields", "any", "critical"):
                _require(field in assertion, f"behavior case {case['id']} {assertion_kind} item missing {field}")
            _require(assertion["id"] not in ids, f"duplicate {assertion_kind} assertion id in {case['id']}")
            ids.add(assertion["id"])
            _require(isinstance(assertion["fields"], list) and assertion["fields"], f"{assertion_kind} assertion fields must be non-empty")
            _require(isinstance(assertion["any"], list) and assertion["any"], f"{assertion_kind} assertion must define a non-empty any list")
            _require(all(isinstance(term, str) and term for term in assertion["any"]), f"{assertion_kind} assertion any terms must be non-empty strings")
            _require(isinstance(assertion["critical"], bool), f"{assertion_kind} assertion critical must be boolean")


def load_behavior_cases(path: Path) -> list[dict[str, Any]]:
    """Load and validate behavior cases from a versioned JSON contract."""
    payload = _read_json(path)
    _require(isinstance(payload, dict) and payload.get("version") == 1, "behavior data must have version 1")
    cases = payload.get("cases")
    _require(isinstance(cases, list) and cases, "behavior data cases must be a non-empty list")
    ids: set[str] = set()
    for index, case in enumerate(cases):
        _validate_case(case, index)
        if case["id"] in ids:
            raise ContractError(f"duplicate behavior case id: {case['id']}")
        ids.add(case["id"])
    return cases


def load_trigger_cases(path: Path) -> list[dict[str, Any]]:
    """Load and validate trigger queries from a versioned balanced-case contract."""
    payload = _read_json(path)
    _require(isinstance(payload, dict) and payload.get("version") == 1, "trigger data must have version 1")
    cases = payload.get("cases")
    _require(isinstance(cases, list) and cases, "trigger data cases must be a non-empty list")
    ids: set[str] = set()
    for index, case in enumerate(cases):
        _require(isinstance(case, dict), f"trigger case {index} must be an object")
        for field in TRIGGER_FIELDS:
            _require(field in case, f"trigger case {index} missing {field}")
        _require(isinstance(case["id"], str) and case["id"], f"trigger case {index} id must be non-empty")
        _require(case["id"] not in ids, f"duplicate trigger case id: {case['id']}")
        _require(isinstance(case["query"], str) and case["query"], f"trigger case {case['id']} query must be non-empty")
        _require(isinstance(case["should_trigger"], bool), f"trigger case {case['id']} should_trigger must be boolean")
        ids.add(case["id"])
    return cases


def _field_text(response: dict[str, Any], fields: list[str]) -> str:
    """Flatten selected response fields for case-insensitive keyword matching."""
    values: list[str] = []
    for field in fields:
        value = response.get(field, "")
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))
    return " ".join(values).casefold()


def _assertion(assertion_id: str, passed: bool, evidence: str, critical: bool) -> dict[str, Any]:
    """Build the normalized assertion record consumed by graders and summaries."""
    return {"id": assertion_id, "passed": passed, "evidence": evidence, "critical": critical}


def grade_response(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Grade one provider response; return a viewer-friendly result object."""
    assertions: list[dict[str, Any]] = []
    expected = case["expect"]
    critical_fields = set(case.get("critical_fields", []))
    for field in RESPONSE_FIELDS[:4]:
        accepted = expected.get(f"{field}_any")
        passed = response.get(field) in accepted if accepted else response.get(field) == expected[field]
        assertions.append(_assertion(f"field:{field}", passed, f"expected {expected[field]!r}, got {response.get(field)!r}", field in critical_fields))

    for required in case["required"]:
        text = _field_text(response, required["fields"])
        matched = next((term for term in required["any"] if term.casefold() in text), None)
        assertions.append(_assertion(required["id"], matched is not None, f"matched {matched!r}" if matched else f"none of {required['any']!r} found", required["critical"]))

    for forbidden in case["forbidden"]:
        text = _field_text(response, forbidden["fields"])
        matched = next((term for term in forbidden["any"] if term.casefold() in text), None)
        assertions.append(_assertion(forbidden["id"], matched is None, f"forbidden term {matched!r} found" if matched else "no forbidden term found", forbidden["critical"]))

    failed = [item for item in assertions if not item["passed"]]
    return {
        "case_id": case["id"],
        "passed": not failed,
        "assertions": assertions,
        "assertion_count": len(assertions),
        "passed_count": sum(item["passed"] for item in assertions),
        "critical_failures": [item["id"] for item in failed if item["critical"]],
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate case, assertion, percentage, and critical-failure counts."""
    assertion_count = sum(result["assertion_count"] for result in results)
    passed_count = sum(result["passed_count"] for result in results)
    case_count = len(results)
    case_passes = sum(result["passed"] for result in results)
    critical_failures = sum(len(result["critical_failures"]) for result in results)
    return {
        "case_count": case_count,
        "case_pass_rate": round(100 * case_passes / case_count, 2) if case_count else 0.0,
        "assertion_count": assertion_count,
        "passed_assertion_count": passed_count,
        "assertion_score": round(100 * passed_count / assertion_count, 2) if assertion_count else 0.0,
        "critical_failure_count": critical_failures,
    }


def grade_trigger_response(cases: list[dict[str, Any]], response: dict[str, Any]) -> dict[str, Any]:
    """Grade a provider's trigger classifications against the canonical cases."""
    expected = {case["id"]: case["should_trigger"] for case in cases}
    actual = {
        item.get("id"): item.get("should_trigger")
        for item in response.get("results", [])
        if isinstance(item, dict)
    }
    mismatches = [case_id for case_id, value in expected.items() if actual.get(case_id) != value]
    return {
        "case_count": len(cases),
        "correct_count": len(cases) - len(mismatches),
        "accuracy": round(100 * (len(cases) - len(mismatches)) / len(cases), 2) if cases else 0.0,
        "mismatches": mismatches,
    }
