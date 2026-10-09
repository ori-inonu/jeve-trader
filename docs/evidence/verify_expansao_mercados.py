"""Verify documentary links, exact arithmetic and unchanged app, without network."""
from decimal import Decimal, localcontext
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
from urllib.parse import unquote


def run(root: Path) -> dict:
    root = root.resolve()
    notes = sorted((root / "docs/research").glob("Expansao_Mercados_*_2026-10-09.md"))
    expected = {"APIs", "Aceites", "B3_Binarias", "Cripto_Esportes", "Direcao", "Economia", "Plano"}
    assert {p.stem.removeprefix("Expansao_Mercados_").removesuffix("_2026-10-09") for p in notes} == expected
    files = notes + [root / "docs/specs/Coleta_Multimercado_2026-10-09.md",
                     root / "docs/evidence/expansao-mercados-decisoes-2026-10-09.json",
                     Path(__file__).resolve()]
    missing, checked, external = [], [], set()
    for path in files:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
        if path.suffix != ".md":
            continue
        body = path.read_text(encoding="utf-8-sig")
        links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", body)
        links += re.findall(r"^\[[^\]]+\]:\s*(\S+)", body, re.MULTILINE)
        for raw in links:
            target = raw.strip().strip("<>").split("#", 1)[0]
            if target.startswith(("https://", "http://")):
                external.add(target)
                continue
            if not target:
                continue
            target_path = Path(unquote(target))
            if not target_path.is_absolute():
                target_path = path.parent / target_path
            checked.append({"source": path.relative_to(root).as_posix(), "target": raw})
            if not target_path.is_file():
                missing.append(checked[-1])
    assert not missing, missing
    with localcontext() as ctx:
        ctx.prec = 50
        d = Decimal
        factor = d(4000) / d(400)
        assert factor == 10
        r5 = factor ** (d(1) / d(5)) - 1
        r7 = factor ** (d(1) / d(7)) - 1
        assert (r5 * 100).quantize(d(".000001")) == d("58.489319")
        assert (r7 * 100).quantize(d(".000001")) == d("38.949549")
        b = d(".8")
        p_star = 1 / (1 + b)
        assert abs(p_star * b - (1 - p_star)) < d("1e-48")
        wins = {}
        for fraction, expected_wins in [(d(".10"), 30), (d(".02"), 146)]:
            k = 0
            while (1 + b * fraction) ** k < factor:
                k += 1
            assert k == expected_wins
            assert (1 + b * fraction) ** (k - 1) < factor <= (1 + b * fraction) ** k
            wins[str(fraction)] = k
        assert (1 + b) ** 4 == d("10.4976")
        assert d(1000) * d(".20") == 200
        assert d(100) * (d(5) - 1) == 400
        odds, commission = d(2), d(".05")
        back_threshold = 1 / (1 + (odds - 1) * (1 - commission))
        assert abs(back_threshold * (odds - 1) * (1 - commission) - (1 - back_threshold)) < d("1e-48")
        math = {"factor": str(factor), "net_gain_brl": "3600", "net_return_percent": "900",
                "five_session_rate_percent": str(r5 * 100), "seven_day_rate_percent": str(r7 * 100),
                "binary_net_payout": str(b), "binary_break_even_probability": str(p_star),
                "ideal_all_win_counts": wins, "all_in_four_win_factor": "10.4976",
                "win_1000_points_gross_brl": "200", "lay_100_at_5_liability_brl": "400",
                "single_back_at_2_commission_5pct_break_even": str(back_threshold),
                "target_probability": None, "observed_financial_performance": None}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=root, text=True).splitlines()
    assert not changed, changed
    assert head == "da96c6ad4187030a98c4daa86a6b96e1e5b809a9", head
    app_files = [root / "app" / name for name in ("profit_bridge.py", "profitdll_contract.py", "decision_engine.py")]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {"status": "pass", "platform": platform.platform(), "python": platform.python_version(),
            "baseline": head, "tracked_changes": changed, "network_calls": 0,
            "local_links_checked": len(checked), "external_references_count": len(external),
            "external_links_live_verified_by_this_script": False,
            "math": math, "artifacts": {p.relative_to(root).as_posix(): digest(p) for p in files},
            "app_hashes": {p.relative_to(root).as_posix(): digest(p) for p in app_files},
            "scope": "Documentation/arithmetic/integrity only; no WS, account, execution or profitability validation."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.root)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
