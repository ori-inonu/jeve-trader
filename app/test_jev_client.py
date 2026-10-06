"""Offline contract tests. All model outputs here are explicitly synthetic."""

import copy
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import urllib.error

from jev_client import API_URL, MAX_RESPONSE_BYTES, PINNED_MODEL, JevClient, JevError, validate_response


QUESTIONS = json.loads(Path(__file__).with_name("questions.json").read_text(encoding="utf-8"))


def synthetic_response():
    labels = QUESTIONS["flow_interpretation"]["criteria"]
    return {
        "model": PINNED_MODEL,
        "answers": {
            "flow_interpretation": {
                "type": "choice",
                "choice": "inconclusive",
                "probabilities": {key: float(key == "inconclusive") for key in labels},
                "confidence": 1.0,
            },
            "setup_evidence_support": {"type": "noul", "noul": 0.2},
            "contradictory_evidence": {"type": "noul", "noul": 0.3},
        },
        "usage": {"input_tokens": 500, "output_tokens": 80},
    }


class FakeResponse(io.BytesIO):
    status = 200

    def geturl(self):
        return API_URL


class JevContractTests(unittest.TestCase):
    def test_valid_response_is_returned_unchanged(self):
        response = synthetic_response()
        self.assertIs(validate_response(response, QUESTIONS, PINNED_MODEL), response)

    def test_missing_extra_ids_or_wrong_type_fail_closed(self):
        for mutation in (
            lambda r: r["answers"].pop("contradictory_evidence"),
            lambda r: r["answers"].update({"unrequested": {"type": "noul", "noul": 1.0}}),
            lambda r: r["answers"]["setup_evidence_support"].update(type="choice"),
            lambda r: r.update(model="jev-latest"),
            lambda r: r.update(usage={"input_tokens": True, "output_tokens": 1}),
        ):
            response = synthetic_response()
            mutation(response)
            with self.subTest(response=response), self.assertRaises(JevError):
                validate_response(response, QUESTIONS, PINNED_MODEL)

    def test_unknown_choices_and_invalid_distributions(self):
        for mutation in (
            lambda a: a.update(choice="buy_now"),
            lambda a: a["probabilities"].update(unrequested=0.0),
            lambda a: a["probabilities"].update(inconclusive=0.5),
            lambda a: a.update(choice="buying_absorbed"),
            lambda a: a.update(confidence=float("nan")),
        ):
            response = synthetic_response()
            mutation(response["answers"]["flow_interpretation"])
            with self.assertRaises(JevError):
                validate_response(response, QUESTIONS, PINNED_MODEL)

    def test_nonfinite_out_of_range_and_boolean_probabilities(self):
        for value in (float("nan"), float("inf"), -0.1, 1.01, True, "0.7", 10 ** 1000):
            response = synthetic_response()
            response["answers"]["setup_evidence_support"]["noul"] = value
            with self.subTest(value=repr(value)[:40]), self.assertRaises(JevError):
                validate_response(response, QUESTIONS, PINNED_MODEL)

    @patch.dict(os.environ, {"TYPESAFE_API_KEY": "synthetic-test-key"})
    def test_mocked_transport_uses_documented_payload_and_one_attempt(self):
        client = JevClient()
        response = synthetic_response()
        client._opener.open = Mock(return_value=FakeResponse(json.dumps(response).encode()))
        state = {"observed_facts": {}, "computed_features": {}, "candidate_setup": {}}
        self.assertEqual(client.evaluate(state, QUESTIONS), response)
        client._opener.open.assert_called_once()
        request = client._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, API_URL)
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), {"state": state, "model": PINNED_MODEL, "questions": QUESTIONS})
        self.assertEqual(client._opener.open.call_args.kwargs["timeout"], 1.0)

    @patch.dict(os.environ, {"TYPESAFE_API_KEY": "synthetic-secret-value"})
    def test_transport_error_never_exposes_key_or_response_body(self):
        client = JevClient()
        client._opener.open = Mock(side_effect=urllib.error.URLError("synthetic-secret-value"))
        with self.assertRaises(JevError) as context:
            client.evaluate({}, QUESTIONS)
        self.assertNotIn("synthetic-secret-value", str(context.exception))
        client._opener.open.assert_called_once()

    @patch.dict(os.environ, {"TYPESAFE_API_KEY": "synthetic-test-key"})
    def test_invalid_json_duplicate_keys_and_oversized_response(self):
        for raw in (
            b"not json",
            b'{"model":"one","model":"two"}',
            b'{"answers":NaN}',
            b"x" * (MAX_RESPONSE_BYTES + 1),
        ):
            client = JevClient()
            client._opener.open = Mock(return_value=FakeResponse(raw))
            with self.assertRaises(JevError):
                client.evaluate({}, QUESTIONS)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_prevents_network(self):
        client = JevClient()
        client._opener.open = Mock()
        with self.assertRaises(JevError):
            client.evaluate({}, QUESTIONS)
        client._opener.open.assert_not_called()

    @patch.dict(os.environ, {"TYPESAFE_API_KEY": "synthetic-test-key"})
    def test_redirect_handler_refuses_other_host(self):
        client = JevClient()
        handlers = [handler for handler in client._opener.handlers if hasattr(handler, "redirect_request")]
        self.assertEqual(len(handlers), 1)
        with self.assertRaises(JevError):
            handlers[0].redirect_request(None, None, 302, "Found", {}, "https://other.invalid/")


if __name__ == "__main__":
    unittest.main()
