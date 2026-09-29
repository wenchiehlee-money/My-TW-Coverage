"""Render dynamic valuation charts for every numeric company JSON ticker.

The per-symbol renderer remains the source of truth.  This wrapper only
orchestrates it: it skips complete artifacts, rotates the configured FinMind
tokens across workers, and writes a retryable failure report without making a
failed company page look complete.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _load_local_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.is_file():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_local_dotenv()


ARTIFACT_SUFFIXES = ("_dynamic_valuation_box_3y.png", "_dynamic_valuation_box_3y.svg", "_dynamic_valuation_box_3y.csv")


def _symbols(json_dir: Path) -> list[str]:
    symbols: set[str] = set()
    for path in sorted(json_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ticker = str(record.get("ticker", "")).strip()
        if ticker.isdigit():
            symbols.add(ticker.zfill(4))
    return sorted(symbols)


def _complete(output_dir: Path, symbol: str) -> bool:
    return all((output_dir / f"{symbol}{suffix}").is_file() for suffix in ARTIFACT_SUFFIXES)


def _quota_remaining(token: str) -> int:
    try:
        response = requests.get(
            "https://api.web.finmindtrade.com/v2/user_info",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        body = response.json()
        limit = int(body.get("api_request_limit", 0) or 0)
        used = int(body.get("user_count", 0) or 0)
        return max(limit - used, 0) if limit > 0 else 0
    except (requests.RequestException, ValueError, TypeError):
        return 0


def _run_one(
    symbol: str,
    token: str,
    renderer: Path,
    output_dir: Path,
    analyzer_revenue: str,
    finmind_revenue: str | None,
    years: int,
    end_date: str | None,
) -> tuple[str, bool, str]:
    env = os.environ.copy()
    # Each child must see only its assigned token.  If the parent environment
    # exposes the whole token pool, the renderer would rotate across all tokens
    # inside every worker and defeat the batch-level quota allocation.
    token_env_names = [
        "FINMIND_TOKEN", "FINMIND_API_TOKEN",
        *(f"FINMIND_TOKEN{index}" for index in range(1, 21)),
        "FINDMIND_GMAIL_TOKEN", *(f"FINDMIND_GMAIL_TOKEN{index}" for index in range(1, 21)),
    ]
    for name in token_env_names:
        env[name] = ""
    if token:
        env["FINMIND_TOKEN"] = token
    command = [
        sys.executable,
        str(renderer),
        "--symbols",
        symbol,
        "--years",
        str(years),
        "--output-dir",
        str(output_dir),
        "--analyzer-revenue-csv",
        analyzer_revenue,
    ]
    if finmind_revenue:
        command.extend(["--finmind-revenue-csv", finmind_revenue])
    if end_date:
        command.extend(["--end-date", end_date])
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300, env=env)
    except subprocess.TimeoutExpired:
        return symbol, False, "timeout after 300 seconds"
    if result.returncode == 0 and _complete(output_dir, symbol):
        return symbol, True, ""
    error = (result.stderr or result.stdout or f"renderer exited {result.returncode}").strip()
    # Never put a credential into the persisted failure report.
    for candidate in (token, os.environ.get("FINMIND_TOKEN", ""), os.environ.get("FINMIND_API_TOKEN", "")):
        if candidate:
            error = error.replace(candidate, "<redacted-token>")
    return symbol, False, error[-2000:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-dir", default="data/enrichment_all")
    parser.add_argument("--renderer", help="Per-symbol renderer; defaults to this skill's renderer")
    parser.add_argument("--output-dir", default="output/dynamic_valuation_box")
    parser.add_argument("--analyzer-revenue-csv", required=True)
    parser.add_argument("--finmind-revenue-csv")
    parser.add_argument("--failure-log", default="output/dynamic_valuation_box_failures.tsv")
    parser.add_argument("--token-env-prefix", default="FINMIND_TOKEN")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--years", type=int, choices=(2, 3, 4, 5), default=3)
    parser.add_argument("--end-date")
    parser.add_argument("--force", action="store_true", help="Re-render symbols whose three artifacts already exist")
    args = parser.parse_args()

    json_dir = Path(args.json_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    renderer = Path(args.renderer) if args.renderer else Path(__file__).with_name("render_dynamic_valuation_box.py")
    symbols = _symbols(json_dir)
    pending = [symbol for symbol in symbols if args.force or not _complete(output_dir, symbol)]
    token_names = [f"{args.token_env_prefix}{index}" for index in range(1, 21)]
    token_names += [
        "FINMIND_TOKEN", "FINMIND_API_TOKEN",
        *(f"FINDMIND_GMAIL_TOKEN{index}" for index in range(1, 21)),
        "FINDMIND_GMAIL_TOKEN",
    ]
    tokens = []
    for name in token_names:
        token = os.environ.get(name, "")
        if token and token not in tokens:
            tokens.append(token)
    if tokens:
        before = len(tokens)
        tokens = [token for token in tokens if _quota_remaining(token) > 0]
        print(f"quota_preflight active={len(tokens)} exhausted={before - len(tokens)}")
    if not tokens:
        # A tokenless run remains useful for public/demo environments.  The
        # renderer will report the actual API response instead of failing here.
        tokens = [""]
    workers = max(1, min(args.workers, len(tokens), len(pending) or 1))
    print(f"symbols={len(symbols)} complete={len(symbols) - len(pending)} pending={len(pending)} workers={workers}")

    failures: list[tuple[str, str]] = []
    succeeded = 0
    quota_failure_streak = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _run_one,
                symbol,
                tokens[index % len(tokens)],
                renderer,
                output_dir,
                args.analyzer_revenue_csv,
                args.finmind_revenue_csv,
                args.years,
                args.end_date,
            ): symbol
            for index, symbol in enumerate(pending)
        }
        for future in as_completed(futures):
            symbol, ok, error = future.result()
            if ok:
                succeeded += 1
                quota_failure_streak = 0
                print(f"OK {symbol}")
            else:
                failures.append((symbol, error))
                print(f"FAIL {symbol}: {error}", file=sys.stderr)
                if "quota exhausted" in error.lower() or "reach the upper limit" in error.lower():
                    quota_failure_streak += 1
                    if quota_failure_streak >= max(3, workers):
                        print(
                            "Stopping batch after consecutive FinMind quota failures; "
                            "pending symbols remain retryable on the next quota window.",
                            file=sys.stderr,
                        )
                        for pending_future in futures:
                            pending_future.cancel()
                        break
                else:
                    quota_failure_streak = 0

    failure_path = Path(args.failure_log)
    failure_path.parent.mkdir(parents=True, exist_ok=True)
    failure_path.write_text(
        "symbol\terror\n" + "\n".join(f"{symbol}\t{error.replace(chr(9), ' ')}" for symbol, error in sorted(failures)) + ("\n" if failures else ""),
        encoding="utf-8",
    )
    print(f"completed={succeeded} failed={len(failures)} failure_log={failure_path}")
    if failures:
        print(
            f"ERROR: {len(failures)} valuation charts failed; refusing to publish incomplete company pages.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
