# Independent standards review — PR #2 vs main

Baseline: 0171aed6c4a25adf26d349bfe2c3140805a35e97  
Candidate: 5f15ab73f4f5adfd3221b9bd5f785c24c9afc496  
Reviewer: Codex independent reviewer, task /root/pr2_main_standards_review.  
Scope: exact three-dot diff; 236 files (+26,910/−160), in the isolated read-only worktree.

## Hard violations

None evidenced against the reviewed repository rules. The B3 feed, private account access, financial-model promotion and native Windows evidence remain explicitly gated external work, not claimed as complete.

## Possible smells / defects

- **P2 — possible unbounded live deduplication state:** app/multimarket/market_state.py:53 declares an unbounded _seen set; changed lines 97–100 add every event key. The Binance adapter creates a unique trade:<id> for each individual trade (adapters.py:327–340), and invalidation never prunes the set. Unlike _trades, which is capped at 200, dedup entries accumulate for the process lifetime and across epochs. A long-running live feed can grow memory without bound. This is a possible runtime defect against the real-time memory-measurement scope in multimarket I-11; a bounded deduplication policy or evidence-backed lifetime limit is needed.

The required smell baseline was assessed: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest. No additional reportable findings.

Total: 1 possible finding; worst priority P2. **Not approved** pending resolution or bounded evidence.

Checks: 62 focused multimarket tests passed; desktop self-test passed. Full offline verification ran 322 tests but had 6 environment-related errors because this host’s Python 3.14 environment lacks the declared tzdata package; subsequent temporary SQLite cleanup also hit Windows file locks. The checkout’s declared runtime/build requirements include tzdata. No paid JEV call, network market access, order, installation or external write was made.
