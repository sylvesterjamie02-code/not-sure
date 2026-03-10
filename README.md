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

## CLI usage

```bash
python bot.py \
  --centres centres.json \
  --timeout 20 \
  --output availability-report.json
```

### Flags

- `--centres`: Path to centres JSON file (default: `centres.json`)
- `--timeout`: Request timeout in seconds (default: `20`)
- `--output`: Optional path to write machine-readable JSON results

## Configure centres

Edit `centres.json` and add/remove entries as needed:

```json
{
  "name": "Your Centre",
  "borough": "Tower Hamlets",
  "provider": "Better",
  "booking_url": "https://example.com/booking/page"
}
```

## Running as a scheduled bot

Use cron to run every 30 minutes and store outputs:

```bash
*/30 * * * * cd /path/to/repo && /path/to/python bot.py --output latest.json >> bot.log 2>&1
```

Then wire `latest.json` into your own notification logic (email, Slack, Telegram, etc.).

## Disclaimer

This bot reads publicly available booking pages and does not bypass authentication, captchas, or paywalls.
