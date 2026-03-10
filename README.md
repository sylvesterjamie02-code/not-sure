# East London Badminton Court Availability Bot

A lightweight Python bot that checks public booking pages for badminton-court availability across selected East London leisure centres.

## What it does

- Loads a list of East London leisure centres and booking URLs from `centres.json`.
- Fetches each booking page.
- Looks for badminton-related text and common availability signals (`available`, `book now`, `spaces`, etc.).
- Produces a summary table in the terminal.
- Optionally writes results to JSON for use in cron jobs, alerts, or dashboards.

> Note: Different leisure providers structure their booking pages differently. This bot uses resilient text heuristics so you can get useful signals quickly, then tune selectors/keywords per centre.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

