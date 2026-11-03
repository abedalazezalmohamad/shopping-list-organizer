# Ahmed Altaha - 2409115853

**Role:** Lead Developer

## My Contributions

### Code: Main Program (`price_watch.py`)
*   Input validation: `validate_url()` (allowed websites only, no user name / password / port, no spaces), `validate_target()`, `validate_currency()`, `validate_whole_number()`. Every validator returns a `(value, error)` tuple.
*   Storage: `load_watchlist()` and `save_watchlist()` with `json`. Damaged entries are skipped with a warning, and a broken file is never overwritten.
*   Features: `add_product()`, `remove_product()`, `show_watchlist()`, `check_item()` and `check_all()`.
*   Alerts: `send_alert()` writes to `alerts.log` in append mode with the date and time; `show_alerts()` shows the latest ones. A target alert is sent only once when the price crosses the target.
*   Scheduling: `watch()` repeats the check every few minutes with `time.sleep()`.
*   Command-line interface: `build_parser()` with sub-commands `add`, `remove`, `list`, `check`, `watch`, `alerts`, and `run_command()` / `main()` with exit codes.

### Other
*   `requirements.txt` (`requests`, `beautifulsoup4`).

## Topics I Worked With
`argparse` sub-commands, JSON files, append mode, `time.sleep()` and `datetime`, `urllib.parse`, functions with `*args`, f-strings.
