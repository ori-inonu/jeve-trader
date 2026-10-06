"""Small, fail-closed TypeSafe client for a replay/advisory application.

Official contract: https://docs.typesafe.ai/api
No market-data connection, order placement, redirects, or automatic retries.
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from typing import Any


PINNED_MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
MAX_RESPONSE_BYTES = 262_144


class JevError(Exception):
    """Sanitized integration failure; callers must suppress the candidate signal."""


def _unit_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= value <= 1
        and math.isfinite(value)
    )


def _validate_questions(questions: dict) -> None:
    if not isinstance(questions, dict) or not questions:
        raise JevError("Questions must be a nonempty object.")
    for question_id, question in questions.items():
        if not isinstance(question_id, str) or not question_id:
            raise JevError("Question identifiers are invalid.")
        if not isinstance(question, dict):
            raise JevError("Question schema is invalid.")
        if set(question) - {"type", "instructions", "criteria"}:
            raise JevError("Question contains unsupported fields.")
        instructions = question.get("instructions")
        if not isinstance(instructions, (str, dict, list)) or not instructions:
            raise JevError("Question instructions are invalid.")
        kind = question.get("type")
        criteria = question.get("criteria")
        if kind == "choice":
            if not isinstance(criteria, dict) or not 2 <= len(criteria) <= 255:
                raise JevError("Choice criteria are invalid.")
            if any(not isinstance(key, str) or not key for key in criteria):
                raise JevError("Choice labels are invalid.")
            if any(value is not None and not isinstance(value, (str, dict, list)) for value in criteria.values()):
                raise JevError("Choice descriptions are invalid.")
        elif kind == "noul":
            if criteria is not None:
                if not isinstance(criteria, dict) or set(criteria) != {"true", "false"}:
                    raise JevError("Noul criteria are invalid.")
                if any(not isinstance(value, (str, dict, list)) for value in criteria.values()):
                    raise JevError("Noul descriptions are invalid.")
        else:
            raise JevError("Only Choice and Noul questions are supported by this adapter.")


def build_payload(state: dict, questions: dict, model: str = PINNED_MODEL) -> dict:
    """Build the documented REST shape; state contains observations, not account data."""
    if model != PINNED_MODEL:
        raise JevError("The adapter requires the pinned, reviewed model version.")
    if not isinstance(state, dict):
        raise JevError("State must be an object.")
    _validate_questions(questions)
    return {"state": state, "model": model, "questions": questions}


def validate_response(response: dict, questions: dict, expected_model: str) -> dict:
    """Validate a raw API response without network access or state mutation."""
    _validate_questions(questions)
    if expected_model != PINNED_MODEL:
        raise JevError("The expected model must be the pinned version.")
    if not isinstance(response, dict) or set(response) != {"model", "answers", "usage"}:
        raise JevError("Response schema is invalid.")
    if response.get("model") != expected_model:
        raise JevError("Response model does not match the pinned version.")
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise JevError("Response question identifiers do not match the request.")
    usage = response.get("usage")
    if not isinstance(usage, dict) or set(usage) != {"input_tokens", "output_tokens"}:
        raise JevError("Response usage schema is invalid.")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in usage.values()):
        raise JevError("Response token usage is invalid.")
    for question_id, question in questions.items():
        answer = answers[question_id]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise JevError("Response answer type does not match the question.")
        if question["type"] == "noul":
            if set(answer) != {"type", "noul"} or not _unit_number(answer.get("noul")):
                raise JevError("Response Noul probability is invalid.")
            continue
        if set(answer) != {"type", "choice", "probabilities", "confidence"}:
            raise JevError("Response Choice schema is invalid.")
        labels = question["criteria"]
        choice = answer.get("choice")
        if not isinstance(choice, str) or choice not in labels:
            raise JevError("Response Choice label is unknown.")
        probabilities = answer.get("probabilities")
        if not isinstance(probabilities, dict) or set(probabilities) != set(labels):
            raise JevError("Response probability labels do not match the choices.")
        if not all(_unit_number(value) for value in probabilities.values()):
            raise JevError("Response contains an invalid probability.")
        if not math.isclose(math.fsum(probabilities.values()), 1.0, rel_tol=0.0, abs_tol=1e-6):
            raise JevError("Response probabilities do not sum to one.")
        if probabilities[choice] < max(probabilities.values()):
            raise JevError("Response Choice is inconsistent with its probabilities.")
        if not _unit_number(answer.get("confidence")):
            raise JevError("Response confidence is invalid.")
    return response


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise JevError("API redirects are disabled.")


def _reject_json_constant(value: str) -> None:
    raise JevError("Response contains nonstandard JSON numbers.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise JevError("Response contains duplicate JSON keys.")
        result[key] = value
    return result


class JevClient:
    """One HTTPS attempt per evaluation, with no credential-bearing error details."""

    def __init__(self, model: str = PINNED_MODEL, timeout_seconds: float = 1.0, *, api_key: str | None = None):
        if model != PINNED_MODEL:
            raise JevError("The adapter requires the pinned, reviewed model version.")
        if (
            not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or not 0 < timeout_seconds <= 60
            or not math.isfinite(timeout_seconds)
        ):
            raise JevError("Timeout must be finite and between zero and 60 seconds.")
        self.model = model
        self.timeout_seconds = float(timeout_seconds)
        if api_key is not None and not isinstance(api_key, str):
            raise JevError("API key must be text.")
        self._api_key = api_key
        self._opener = urllib.request.build_opener(_NoRedirect())

    def evaluate(self, state: dict, questions: dict) -> dict:
        payload = build_payload(state, questions, self.model)
        key = (self._api_key if self._api_key is not None else os.environ.get("TYPESAFE_API_KEY", "")).strip()
        if not key or any(ord(char) > 127 or ord(char) < 33 for char in key):
            raise JevError("A valid TYPESAFE_API_KEY environment variable is required.")
        try:
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, OverflowError, RecursionError):
            raise JevError("Request data must be finite, serializable JSON.") from None
        request = urllib.request.Request(
            API_URL,
            data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as result:
                if result.status != 200:
                    raise JevError("API returned an unsuccessful HTTP status.")
                if result.geturl() != API_URL:
                    raise JevError("API response URL does not match the authorized endpoint.")
                raw = result.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise JevError("API response exceeded the size limit.")
            response = json.loads(
                raw.decode("utf-8"),
                parse_constant=_reject_json_constant,
                object_pairs_hook=_unique_object,
            )
            return validate_response(response, questions, self.model)
        except JevError:
            raise
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            raise JevError("API request failed or timed out; no signal is available.") from None
        except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError):
            raise JevError("API response could not be decoded or validated.") from None
