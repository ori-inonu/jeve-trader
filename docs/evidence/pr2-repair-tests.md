# PR2 regression repair test evidence — 2026-10-09

> Publication projection: personal checkout paths and the conversation UUID are omitted. Non-personal task and reviewer role labels are retained as provenance. Acceptance, findings, source hashes and measured results are unchanged. Raw source SHA-256: 6edac6ac5c826028424e3a4f0b6ec48853d79163dbd4768bcbd2f85b969914f5

Checkout: `{repair_checkout}`  
Baseline: `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`  
Frozen acceptance: `docs/specs/PR2_Revisao_Main_2026-10-09.md`, SHA-256 `89f127a4fd48e30790ffb2d8fdb8e1f662e586eb89e2b29078d31862119a1c5c`  
Interpreter: `{integration_checkout}\.venv\Scripts\python.exe`; tests ran from the checkout's `app` directory.

## RED

- `python -m unittest test_mesa_control.MesaControlTests.test_off_cannot_complete_between_final_gate_and_external_invocation -v` failed on the baseline with `AssertionError: Lists differ: [True] != [False]`. OFF returned while the test paused at the final dispatch boundary before the fake external client invocation.
- The two `MarketStateTests` for strict capacity validation/default visibility and saturation/recovery failed on the baseline: snapshot raised `KeyError: 'deduplication'`, and explicit capacity raised `TypeError: MarketState.__init__() got an unexpected keyword argument 'dedup_capacity'`.
- `MultimarketIntegrationTests.test_dedup_overflow_requests_resync_and_clears_context_without_claiming_full_tape` failed on the baseline with the same unexpected-keyword `TypeError`.

## GREEN

- Desktop dispatch race plus OFF-during-call accounting/revocation: 2 tests passed in 2.448 s.
- MarketState capacity and saturation/epoch recovery: 2 tests passed in 0.002 s.
- Service resync/context-clear/full-tape behavior: 1 test passed in 0.233 s.
- Complete owned test files: `python -m unittest test_mesa_control test_multimarket_domain test_multimarket_service -v` — 48 tests passed in 7.203 s.
- `git diff --check` passed.

An additional offline run of `scripts/verify.py` completed before the parent clarified that integration/full verification belongs to root: Windows `win32`, Python 3.14.7, 326 tests passed in 29.679 s and desktop self-test passed. The harness marked `python_socket_network_blocked=true`; GUI, Windows runtime, live JEV, live Profit/Excel, and order execution were not tested. Its machine result is in checkout `.artifacts/verification.json`.

## Change and limits

The JEV final revision/enabled check and external `client.evaluate()` now share a lock with ON/OFF revision changes. Client construction remains outside the gate. Accounting is retained; late results cannot revive the context/cadence after OFF/revision changes. OFF acknowledgement can wait for an in-flight evaluation, and the 3-second transport timeout does not prove a total deadline.

MarketState now validates an exact positive integer capacity (bool rejected, upper bound 100000, default 100000), checks duplicates before saturation, invalidates and clears all retained IDs on the first new unique event at capacity, increments the epoch through the existing invalidation path, and exposes retained/capacity in its snapshot. The service-level test uses a fake external API and confirms resync, context clearing, and `full_tape=False`.

Only the five owned files are in the patch. The pre-existing untracked immutable SPEC in the checkout is excluded and was not changed. No commit was made. The binary patch is `{private_evidence_directory}\pr2-regression-repair-2026-10-09.patch`; SHA-256 is reported separately after generation.