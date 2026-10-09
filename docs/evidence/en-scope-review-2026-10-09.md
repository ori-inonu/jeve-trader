# Independent pre-implementation scope and test-seam review

Review status: **Proceed with explicit boundaries.** The frozen local increment EN-T1–T3 is implementable against the proposed seams. This report reviews scope and testability only; there is no candidate implementation here, no acceptance criterion was changed, and no tests were run.

## Baseline and identity

Review used the isolated read-only checkout `C:\Users\gabri\.codex\worktrees\en-scope-review\jeve-trader`. Git HEAD is `385e79119b75bb8ea0277e3b0cfcb1656f443fba`, tree `c9c06f1c99e7be9ccdee910affb5f0c795c2dae3`; the working tree was clean before and after review. The conversation-bound harness context returned SDD revision 0, phase `research`, status `idle`; no other conversation state was imported. Candidate files and acceptance criteria were not edited. The only written outputs are this report and its JSON companion under `C:\Users\gabri\.codex\implementation-research`.

The immutable SPEC `docs/specs/Instrumentacao_Protocolo_Multimercado_2026-10-09.md` hashes to `9e6d06ed4ea275981bdcf8c0d4d26e568b3ff79d9f9be20482feb06e77565e26`, matching the frozen readiness record. That record declares only EN-T1–T3 ready for local implementation. Readiness JSON says all listed I/FW/N/R source hashes matched; I independently re-hashed the files below.

## Acceptance coverage

The proposed seams can cover the complete local EN-01–04 contract if implementation keeps these checks:

- **EN-01 / T1, package origin:** the packaging orchestrator captures commit, tree and dirty state once before build mutations, then passes that same immutable origin into Vite and packaging. A temporary-rooted validator checks the closed manifest, required app and sidecar entries, each file hash, missing/tampered files, normalized duplicates, absolute/traversal paths and paths that resolve outside the package root. Dirty or source-less output stays ineligible. The post-build CLI can bind the embedded manifest hash and app/sidecar hashes in an outer origin record; include the installer hash there when an installer is produced. The package manifest must omit its own hash as the SPEC requires.
- **EN-02 / T2, telemetry:** a pure collector/export validator is a suitable public seam for closed schemas, allowlisting, sanitization, null rules, ring capacity/drop counts and sample order. Receipt metadata must be captured once when a snapshot enters the renderer, and the exact identity/epoch/sequence receipt must be correlated to the React commit using the same injected renderer monotonic clock. Test rapid/reordered publishes, duplicate delivery and command-result snapshots so one render is not attributed to another receipt.
- **EN-03 / T2, interpretation:** test the exporter and frontend/sidecar mapping offline. Preserve the existing meanings of `process_p95_ms` (backend processing clock) and `market_lag_ms` (apparent wall-clock age with unknown offset/uncertainty); do not subtract Python and renderer clocks. GPU remains null. Keep quote/trade/book/account TTLs at 5/30/2/60 seconds, stale-context rejection and existing controls.
- **EN-04 / T3, protocol:** a local validator over hash-bound fixtures is sufficient for closed run/task/event/comparison schemas and independent stage states. Negative fixtures should reject browser/synthetic evidence promoted to native, incomplete or post-freeze pairs, unqualified origins, and gain without the frozen B treatment and prospective complete pairs. Preserve failures and keep `gain: null` in T1–T3.

The fixed acceptance remains intact: I-01–I-12, FW-01–FW-12, N-01–N-05 and the separate R-01–R-04 regression acceptance are not replaced by EN. Screenshots remain excluded from v1 and the screenshot portion of N-04 stays open. T4/T5, native J1–J6 observation/J6 bridge, B3 entitlement, private-account access and any gain claim remain outside this increment. No build, installation, Windows journey, real market/account access or measured improvement is certified by this review.

## Concrete nonblocking findings

1. **Legacy packager boundary.** `README.md` and `app/WINDOWS_BUILD.md` still document `app/build_windows.ps1` → `app/packaging/build_installer.py`. It assembles the conventional CPython/Tk artifact and emits a different `package-manifest.json`; it does not contain the Tauri cockpit plus the separate engine sidecar required by the EN package contract. The frozen T1 table names `desktop/build-windows.ps1`, so leaving the legacy route unchanged is acceptable only if the EN package set is explicitly limited to the multimarket Tauri builder and no claim is made that every supported JevWIN packaging path is EN-eligible. Keep that exclusion visible in evidence.
2. **Origin timing and installer hash.** Vite and the packaging script must share one origin snapshot taken before generated build output. The post-build CLI/outer origin record must actually produce and verify the installer SHA when an installer exists; deferring it to a later undocumented step would leave EN-01 incomplete. Portable runs may retain `installer_sha256: null`.
3. **React lifecycle test limit.** The current test command is `node --test tests/*.test.mjs`; the declared frontend dependencies do not include a DOM or React test renderer, and existing tests do not mount React components. Pure collector tests can prove receipt-state logic, but cannot prove the actual `useLayoutEffect` ran after the exact component commit. Either provide an existing dependency-free mount seam, or state that lifecycle verification remains untested; do not describe collector-only assertions as React commit verification. The UI currently mirrors the `snapshot` prop into `localSnapshot` in a passive `useEffect`, while command results also update local state directly. This is a concrete source of lag/double attribution unless the receipt and committed object are kept aligned.
4. **Export compatibility.** `metricsExportPayload` currently emits `schema_version: 1` with `gpu_bytes`, legacy gate names and `measurement_scope`. A new strict v1 envelope has a different shape. No in-repository consumer of the old downloaded file was found, but preserve a distinct schema identity (or otherwise explicitly handle compatibility) rather than silently changing the meaning of the same versioned export.
5. **Comparison limits.** The readiness record explicitly notes the current pair validator does not enforce full host/runtime equality. That is a T5 follow-up, not a T1–T3 blocker; do not claim comparable gain until the future protocol freezes equivalent environments or qualifies the differences.

## Integration boundary

Keep the candidate on the PR2/spec line at base `385e79119b75bb8ea0277e3b0cfcb1656f443fba`. A separate EN-only change targeting `codex/multimarket-spec` preserves the current architecture boundary. Do not merge this work into or replace `main` at `e64226c`, which contains the separate PR1 merge. This review made no branch, publication or integration changes.

## Current source hashes

All paths below are relative to the reviewed checkout. Git tree is an object ID, not a SHA-256 file hash.

| Source | SHA-256 |
| --- | --- |
| `docs/specs/Instrumentacao_Protocolo_Multimercado_2026-10-09.md` | `9e6d06ed4ea275981bdcf8c0d4d26e568b3ff79d9f9be20482feb06e77565e26` |
| `docs/evidence/rt12-next-spec-readiness-final.json` | `3f2a8dba8357eea31c23e956eafa602dab38854cc7e6935b7fffd43672769217` |
| `docs/evidence/rt12-next-spec-readiness-final.md` | `5e8faf96dc180094657e3abe0dd7e03577462e484b4ce7f79763ecc6dea6074c` |
| `docs/research/RT12_Proximo_Ciclo_2026-10-09.md` | `816619846ff7740e0c543af6d1d5e4f84fe7f884225e56acfe5af72ac6107684` |
| `docs/specs/Multimercado_Implementacao_2026-10-09.md` | `af174497bf764b1a7c67818cee6e3b925a40933d98c40c8e14f5b1b0f6bc01f4` |
| `docs/specs/Multimercado_Proximo_Ciclo_2026-10-09.md` | `fff2b8adb6ef815fcc70eadd80f1ff46e91d4bd60ba5a7e7bb3239b078c46c632` |
| `docs/specs/PR2_Revisao_Main_2026-10-09.md` | `89f127a4fd48e30790ffb2d8fdb8e1f662e586eb89e2b29078d31862119a1c5c` |
| `.scratch/wayfinder-live-windows/spec.md` | `0183310d90dcfffd921ac551df12e7d2590db55fdfb7c1e1604a7c2b22f1ced6` |
| `docs/evidence/rt12-planning-jev.json` | `9c8a2b673eb406105888228a7fbace36013933ff8e07f24f6c3f0fb70a117bf3` |
| `docs/evidence/pr2-documentation-manifest.json` | `4eaee9904babcdeb749b38fb6137eb3af5752b2fc06767833fc4ad5dfbc798a7` |
| `desktop/build-windows.ps1` | `50b506bd110ad789801dd28bd178b1ef123f77e32cb3eaeede4f64e7384359938` |
| `app/packaging/build_installer.py` | `e5ec488664fa54151a1cc97a0337051fe2103c987ab6371cf1c4567b180bb05a` |
| `desktop/src/MultimarketRoot.tsx` | `89ab772b5a455a734fda75c8f5d3d924b35989a59a0967567d740a3b002a0a0f` |
| `desktop/src/MultimarketCockpit.tsx` | `bd773a327c6a0ae29b111d17b8a0c29aa55e50a7ce45450987022f0264d5ae3e` |
| `desktop/src/multimarketModel.ts` | `c270f4cb8cfa90218661e19364643de689f7e18419b3a40c1d15df5a3a1f0ef3` |
| `desktop/src/multimarketTransport.ts` | `889a3afab4dd9d03077e9fcda2a9dda01be169ecf58182748fdf055ab5090880` |
| `app/multimarket/service.py` | `b87386d071b9e1b1d10c4fdca23b1a8d3f3f5af513bc269f81926cce42af2d00` |
| `desktop/package.json` | `f63cd7a2276646c36a718d92e5f4d4c1132854698216a4f6c79b1422a42d3e46` |
| `desktop/tests/multimarket.test.mjs` | `0c494f660a3e9be0d60608a42009a8d3725fa75601c150c106e047d7bfb61674` |
| `desktop/tests/multimarketTransport.test.mjs` | `72d4f906eb266467b1b53e3e6dc72643e6ae5f1dd499ef023e9005d0379ac5c9` |
| `desktop/tests/multimarket-wire.test.mjs` | `b5e704f19145530a542e1bee720198fc9b00deb92f9558da2732e7f5fb82c244` |
| `app/test_multimarket_service.py` | `945411481bce79fa84f32c0f10029182212f79bcc0581c96868db20633e897e9` |
| `app/test_multimarket_domain.py` | `016e56b1afc176753d3e58a03d597981dda80078535d398927e0fbf3a26ad1ee` |

All source hashes above were rechecked from the isolated checkout. Tests and builds were not executed because this is a read-only pre-implementation scope review. This report is a scope/testability assessment, not an implementation verification or a Jev decision receipt.
