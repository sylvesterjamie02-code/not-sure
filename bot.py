#!/usr/bin/env python3
"""East London badminton court availability checker."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BADMINTON_PATTERNS = [
    re.compile(r"\bbadminton\b", re.IGNORECASE),
    re.compile(r"\bracket\s*sports?\b", re.IGNORECASE),
]

AVAILABILITY_PATTERNS = [
    re.compile(r"\bavailable\b", re.IGNORECASE),
    re.compile(r"\bavailability\b", re.IGNORECASE),
    re.compile(r"\bbook\s*now\b", re.IGNORECASE),
    re.compile(r"\bspaces?\s*left\b", re.IGNORECASE),
    re.compile(r"\bslots?\b", re.IGNORECASE),
]


@dataclass
class Centre:
    name: str
    borough: str
    provider: str
    booking_url: str


@dataclass
class AvailabilityResult:
    centre: str
    borough: str
    provider: str
    booking_url: str
    status: str
    confidence: str
    snippet: str
    checked_at: str
    error: str | None = None


def load_centres(path: Path) -> list[Centre]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Centre(**item) for item in raw]


def fetch_page(url: str, timeout: int) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="ignore")


def extract_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    cleaned = unescape(without_tags)
    return re.sub(r"\s+", " ", cleaned).strip()


def contains_any(text: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def find_snippet(text: str, keyword: str, window: int = 90) -> str:
    lowered = text.lower()
    idx = lowered.find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(keyword) + window)
    return text[start:end].strip()


def check_centre(centre: Centre, timeout: int) -> AvailabilityResult:
    now = datetime.now(timezone.utc).isoformat()

    try:
        html = fetch_page(centre.booking_url, timeout=timeout)
        text = extract_text(html)

        has_badminton = contains_any(text, BADMINTON_PATTERNS)
        has_availability = contains_any(text, AVAILABILITY_PATTERNS)

        if has_badminton and has_availability:
            status = "likely_available"
            confidence = "medium"
            snippet = find_snippet(text, "badminton") or find_snippet(text, "available")
        elif has_badminton:
            status = "badminton_found_no_clear_slots"
            confidence = "low"
            snippet = find_snippet(text, "badminton")
        else:
            status = "badminton_not_detected"
            confidence = "low"
            snippet = ""

        return AvailabilityResult(
            centre=centre.name,
            borough=centre.borough,
            provider=centre.provider,
            booking_url=centre.booking_url,
            status=status,
            confidence=confidence,
            snippet=snippet,
            checked_at=now,
        )
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return AvailabilityResult(
            centre=centre.name,
            borough=centre.borough,
            provider=centre.provider,
            booking_url=centre.booking_url,
            status="error",
            confidence="none",
            snippet="",
            checked_at=now,
            error=str(exc),
        )


def print_table(results: list[AvailabilityResult]) -> None:
    headers = ["Centre", "Borough", "Status", "Confidence", "Error"]
    rows = [[r.centre, r.borough, r.status, r.confidence, (r.error or "")[:70]] for r in results]
    widths = [len(h) for h in headers]

    for row in rows:
        for i, col in enumerate(row):
            widths[i] = max(widths[i], len(str(col)))

    def fmt(values: list[str]) -> str:
        return " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(values))

    print(fmt(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))


def run(args: argparse.Namespace) -> int:
    centres = load_centres(Path(args.centres))
    results = [check_centre(c, timeout=args.timeout) for c in centres]
    print_table(results)

    if args.output:
        Path(args.output).write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
        print(f"\nSaved report to {args.output}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check East London leisure centres for badminton availability clues.")
    parser.add_argument("--centres", default="centres.json", help="Path to centres JSON file")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--output", help="Optional path to write JSON output")
    return parser


if __name__ == "__main__":
    sys.exit(run(build_parser().parse_args()))
