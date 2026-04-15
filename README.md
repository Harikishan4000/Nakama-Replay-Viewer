# Nakama Replay Viewer

An interactive match replay and analysis tool for Nakama game data. Built as a weekend solo project to help level designers understand player movement, conflict hotspots, and loot patterns across three maps and five days of match data.

**Live demo:** https://celadon-sunburst-76027c.netlify.app/

---

## Features

### Match Selection

![Match selection dropdown](screenshots/screenshot6)

### Heatmap View

![Daily aggregate heatmap with heat layers](screenshots/Screenshot2)

### Timeline Playback

![Timeline scrubber and playback controls](screenshots/screenshot1)

### Hot zones

![Hotzone zoom](screenshots/Screenshot5)

### Daily aggregate heat map

![Daily aggrigate heatmap](screenshots/Screenshot4)

### Lonely Zones

![Lonely zones](screenshots/Screenshot3)

---

## Tech stack

| Layer           | Technology                                                                 |
| --------------- | -------------------------------------------------------------------------- |
| Frontend        | Vanilla HTML5 / CSS / JavaScript — no framework, no build step             |
| Rendering       | HTML5 Canvas 2D (paths, heatmaps, event markers)                           |
| Decompression   | [pako.js 2.1.0](https://github.com/nodeca/pako) via CDN — client-side gzip |
| Data processing | Python 3.10+, PyArrow, Pandas                                              |
| Hosting         | Netlify (auto-deploy from GitHub `main`)                                   |

---

## Repository structure

```
├── index.html              # The entire frontend — open this in a browser
├── process_nakama.py       # One-time data pipeline: parquet → JSON
├── public/                 # Files served by Netlify
│   ├── index.html          # Copy of root index.html (deployment target)
│   ├── data/
│   │   ├── matches_index.json      # Match metadata (map, date, player counts)
│   │   └── events_by_map.json.gz  # All events compressed (2.7 MB)
│   └── minimaps/
│       ├── AmbroseValley.png
│       ├── GrandRift.png
│       └── Lockdown.png
├── February_10/            # Raw .nakama-0 parquet files (not in repo — see below)
├── February_11/
├── February_12/
├── February_13/
├── February_14/
├── netlify.toml            # Netlify publish config and cache headers
├── ARCHITECTURE.md         # Design decisions and coordinate mapping
└── INSIGHTS.md             # Three level-design insights from the data
```

> **Note:** The raw parquet files (`February_*/`) are not committed to the repository due to size. The processed output files in `public/data/` are included and are all that the frontend needs.

---

## Running locally

### Prerequisites

- Python 3.10+
- A modern browser (Chrome, Firefox, Safari, Edge)

### 1. Install Python dependencies

```bash
pip install pyarrow pandas tqdm
```

### 2. (Optional) Re-process the raw data

Only needed if you have the original `.nakama-0` parquet files and want to regenerate the JSON:

```bash
python process_nakama.py
# Output written to ./output/
# Copy to public/data/ before serving:
cp output/matches_index.json public/data/
cp output/events_by_map.json.gz public/data/
```

### 3. Run a local dev server

The frontend requires a server (not `file://`) to load the gzip payload:

```bash
# Python built-in server — from the repo root:
python -m http.server 8080
# Then open: http://localhost:8080/public/
```

Or using Node:

```bash
npx serve public
```

No environment variables are required. The tool is fully static.

---

## Deployment

The `public/` folder is the Netlify publish directory (set in `netlify.toml`). Any push to `main` triggers an automatic redeploy.

To deploy manually or to a different host, copy the contents of `public/` to any static file host (Vercel, GitHub Pages, AWS S3, etc.).

---

## Feature walkthrough

### Match selection

Use the left sidebar to filter by map, date, and match. Each match entry shows human player count, bot count, and total event count. Matches with only bots are included in the list but clearly labelled.

### Paths view

Player movement paths are drawn as polylines on the minimap. Human players appear in blue tones, bots in red/orange tones. The start position is marked with a filled dot. Overlay toggles in the sidebar control which event types are shown:

- 💀 Kill events
- ✕ Death events (including storm kills)
- 📦 Loot pickups
- ⚡ Storm deaths

Hover over any event marker to see the player ID, event type, and timestamp in a tooltip.

### Timeline and playback

The timeline bar at the bottom scrubs through the match chronologically. Hit Play to watch the match unfold in real time (1× speed). Pause and resume without resetting position. The timeline shows the full duration even for long matches; binary search keeps scrubbing smooth regardless of event count.

### Heatmap view

Switch to Heatmap mode using the toggle at the top of the right sidebar. Three independent layers can be toggled on/off:

- **High-traffic areas** — position density across all players
- **Kill zones** — where kills were recorded
- **Death zones** — where deaths occurred

Enable **Daily aggregate** to combine all matches on the selected date and map into a single heatmap. Alpha scaling and post-render normalisation prevent the combined view from saturating to a uniform red.

### Hot zones

The Hot Zones panel lists the top combat cells in a 16×16 grid over the minimap. Clicking a zone entry zooms the canvas to that cell, making it easy to inspect paths or events in a specific area.

### Lonely zones

The Lonely Zones panel identifies cells with fewer than N events (adjustable with a slider). These are areas the map has but players are not reaching — useful for spotting dead space in level design.

### Survival leaderboard

Shows how long each player survived in the current match. Toggle **Include bots** to compare human and bot survival patterns side by side.

### Share a moment

The Share button encodes the current match, timestamp, zoom level, and active layers into a URL hash. Paste the link to share an exact view of any moment in any match.

### Zoom and pan

Scroll wheel or +/− buttons to zoom (1×–8×). Click and drag to pan. The coordinate transform is applied at the canvas level, so all event markers and heatmap blobs stay correctly positioned at any zoom level.
