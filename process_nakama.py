#!/usr/bin/env python3
"""
process_nakama.py
=================
Reads all .nakama-0 Parquet event files from date folders, transforms them,
and writes two output files:

  events_by_map.json.gz  — all events, grouped by map_id → match_id, gzip-compressed
  matches_index.json     — one entry per match: map, date, player/bot/event counts

Usage
-----
    python process_nakama.py                       # uses defaults below
    python process_nakama.py --base /path/to/data  # override data root
    python process_nakama.py --out  /path/to/out   # override output dir

Notes on the data
-----------------
* Files are named  {user_id}_{match_id}.nakama-0
* The match_id field stored *inside* each Parquet file includes the ".nakama-0"
  suffix — this script strips it so both outputs use clean UUIDs.
* is_bot is True when user_id matches ^\d+$ (numeric), False for UUID users.
* The event column is stored as bytes; it is decoded to UTF-8 strings.
* Timestamps (ts) are serialised as ISO-8601 strings in the JSON output.
"""

import argparse
import gzip
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq

# ── Try optional progress bar ─────────────────────────────────────────────────
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── Configuration defaults ────────────────────────────────────────────────────

DEFAULT_BASE = Path(__file__).parent          # folder containing the February_XX dirs
DEFAULT_OUT  = Path(__file__).parent / "output"

DATE_FOLDERS = [
    "February_10",
    "February_11",
    "February_12",
    "February_13",
    "February_14",
]

# Maps folder names → ISO dates (year assumed 2025)
_FOLDER_DATES: dict[str, str] = {}
for _folder in DATE_FOLDERS:
    try:
        _month, _day = _folder.split("_", 1)
        _FOLDER_DATES[_folder] = (
            datetime.strptime(f"{_month} {_day} 2025", "%B %d %Y").strftime("%Y-%m-%d")
        )
    except ValueError:
        _FOLDER_DATES[_folder] = _folder

# ── Regex patterns ─────────────────────────────────────────────────────────────

_RE_NUMERIC = re.compile(r"^\d+$")


# ── Logging setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("process_nakama")


# ── Helpers ────────────────────────────────────────────────────────────────────

def decode_event(val) -> str:
    """Safely decode a bytes event value to a UTF-8 string."""
    if isinstance(val, (bytes, bytearray)):
        return val.decode("utf-8", errors="replace")
    return str(val) if val is not None else ""


def ts_to_str(val) -> str | None:
    """Convert a pandas Timestamp (or None) to an ISO-8601 string."""
    if val is None:
        return None
    try:
        return val.isoformat()
    except AttributeError:
        return str(val)


def strip_nakama_suffix(match_id: str) -> str:
    """Remove '.nakama-0' (or similar) suffix from match_id stored in parquet."""
    return re.sub(r"\.nakama-\d+$", "", match_id)


def row_to_dict(row, is_bot: bool, date: str) -> dict:
    """Convert a pandas Series row to a clean, JSON-serialisable dict."""
    return {
        "user_id":  str(row["user_id"]),
        "match_id": strip_nakama_suffix(str(row["match_id"])),
        "map_id":   str(row["map_id"]),
        "x":        float(row["x"]),
        "y":        float(row["y"]),
        "z":        float(row["z"]),
        "ts":       ts_to_str(row["ts"]),
        "event":    decode_event(row["event"]),
        "is_bot":   is_bot,
        "date":     date,
    }


# ── Core processing ────────────────────────────────────────────────────────────

def process_files(base_dir: Path) -> tuple[dict, list]:
    """
    Read all parquet files and return:
      grouped  — {map_id: {match_id: [event_dicts, ...]}}
      index    — [{match_id, map_id, date, player_count, bot_count, event_count}, ...]
    """
    # Collect all file paths with their folder metadata
    work_items: list[tuple[Path, str, str]] = []   # (path, folder_name, iso_date)
    for folder in DATE_FOLDERS:
        folder_path = base_dir / folder
        if not folder_path.is_dir():
            log.warning("Folder not found, skipping: %s", folder_path)
            continue
        date_str = _FOLDER_DATES.get(folder, folder)
        files = sorted(folder_path.glob("*.nakama-0"))
        log.info("%-14s  (%s)  → %d files", folder, date_str, len(files))
        for f in files:
            work_items.append((f, folder, date_str))

    log.info("Total files to process: %d", len(work_items))

    # Accumulators
    # grouped[map_id][match_id] = list of event dicts
    grouped: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    # per_match accumulates stats needed for the index
    match_meta: dict[str, dict] = {}   # match_id → {map_id, date, players, bots}

    total_rows = 0
    errors     = 0

    iterator = work_items
    if HAS_TQDM:
        iterator = tqdm(work_items, unit="file", desc="Processing")

    for pf_path, folder, date_str in iterator:
        # Derive user_id from filename (used for is_bot; cross-checked against column)
        stem = pf_path.name.removesuffix(".nakama-0")
        # user_id is everything before the last '_'
        uscore_idx = stem.rfind("_")
        fname_user_id = stem[:uscore_idx] if uscore_idx != -1 else stem

        try:
            table = pq.read_table(pf_path)
        except Exception as exc:
            log.error("Cannot read %s: %s", pf_path, exc)
            errors += 1
            continue

        if table.num_rows == 0:
            continue

        df = table.to_pandas()

        # Determine is_bot from the user_id column (use first row; all rows share same user)
        col_user_id = str(df["user_id"].iloc[0]) if "user_id" in df.columns else fname_user_id
        is_bot = bool(_RE_NUMERIC.match(col_user_id))

        # Process each row
        for _, row in df.iterrows():
            rec = row_to_dict(row, is_bot, date_str)
            map_id   = rec["map_id"]
            match_id = rec["match_id"]      # already stripped of .nakama-0
            user_id  = rec["user_id"]

            grouped[map_id][match_id].append(rec)

            # Update per-match metadata (accumulate unique player/bot sets)
            if match_id not in match_meta:
                match_meta[match_id] = {
                    "match_id": match_id,
                    "map_id":   map_id,
                    "date":     date_str,
                    "players":  set(),   # human (non-bot) user_ids only
                    "bots":     set(),   # bot (numeric) user_ids only
                }
            meta = match_meta[match_id]
            if is_bot:
                meta["bots"].add(user_id)
            else:
                meta["players"].add(user_id)   # humans only

        total_rows += len(df)

    if not HAS_TQDM:
        log.info("Processed: %d rows, %d errors", total_rows, errors)

    log.info(
        "Done reading.  rows=%d  maps=%d  matches=%d  errors=%d",
        total_rows, len(grouped),
        sum(len(v) for v in grouped.values()),
        errors,
    )

    # Build index list (convert sets → counts, sort for stable output)
    index: list[dict] = []
    for match_id, meta in match_meta.items():
        # Sum events across all map_ids (a match_id should belong to one map)
        map_id = meta["map_id"]
        event_count = len(grouped.get(map_id, {}).get(match_id, []))
        index.append({
            "match_id":     match_id,
            "map_id":       map_id,
            "date":         meta["date"],
            "player_count": len(meta["players"]),
            "bot_count":    len(meta["bots"]),
            "event_count":  event_count,
        })

    index.sort(key=lambda x: (x["date"], x["map_id"], x["match_id"]))

    return grouped, index


# ── Writers ────────────────────────────────────────────────────────────────────

def write_events_gz(grouped: dict, out_path: Path) -> None:
    """
    Write events_by_map.json.gz.

    Structure:
        {
          "map_id_A": {
            "match_id_1": [ {event}, {event}, ... ],
            "match_id_2": [ ... ]
          },
          "map_id_B": { ... }
        }

    Written incrementally (map by map) to keep peak memory low.
    """
    log.info("Writing %s …", out_path)
    map_ids = list(grouped.keys())
    n_maps  = len(map_ids)

    with gzip.open(out_path, "wt", encoding="utf-8", compresslevel=6) as fh:
        fh.write("{\n")
        for m_idx, map_id in enumerate(map_ids):
            matches   = grouped[map_id]
            match_ids = list(matches.keys())
            n_matches = len(match_ids)

            fh.write(f"  {json.dumps(map_id)}: {{\n")
            for j_idx, match_id in enumerate(match_ids):
                events = matches[match_id]
                fh.write(f"    {json.dumps(match_id)}: ")
                fh.write(json.dumps(events, ensure_ascii=False, default=str))
                fh.write(",\n" if j_idx < n_matches - 1 else "\n")
            fh.write("  }")
            fh.write(",\n" if m_idx < n_maps - 1 else "\n")
        fh.write("}\n")

    size_mb = out_path.stat().st_size / 1_048_576
    log.info("  → %.2f MB compressed", size_mb)


def write_index(index: list, out_path: Path) -> None:
    """
    Write matches_index.json — pretty-printed, one entry per match.

    Consumers can load this file to populate filter dropdowns:
      - date picker
      - map_id dropdown
      - match_id dropdown
      - player / bot / event count badges
    """
    log.info("Writing %s …", out_path)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
    size_kb = out_path.stat().st_size / 1024
    log.info("  → %.1f KB  (%d matches)", size_kb, len(index))


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process Nakama .parquet files → events_by_map.json.gz + matches_index.json"
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=DEFAULT_BASE,
        help=f"Root directory containing the February_XX folders (default: {DEFAULT_BASE})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    log.info("Base dir : %s", args.base.resolve())
    log.info("Output   : %s", args.out.resolve())

    grouped, index = process_files(args.base)

    write_events_gz(grouped, args.out / "events_by_map.json.gz")
    write_index(index, args.out / "matches_index.json")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_events = sum(
        len(events)
        for matches in grouped.values()
        for events in matches.values()
    )
    total_players = sum(e["player_count"] for e in index)
    total_bots    = sum(e["bot_count"]    for e in index)

    log.info("━" * 60)
    log.info("  Maps              : %d", len(grouped))
    log.info("  Matches           : %d", len(index))
    log.info("  Total events      : %s", f"{total_events:,}")
    log.info("  Total player-slots: %d  (across all matches)", total_players)
    log.info("  Total bot-slots   : %d  (across all matches)", total_bots)
    log.info("━" * 60)
    log.info("Output files:")
    log.info("  %s", (args.out / "events_by_map.json.gz").resolve())
    log.info("  %s", (args.out / "matches_index.json").resolve())


if __name__ == "__main__":
    main()
