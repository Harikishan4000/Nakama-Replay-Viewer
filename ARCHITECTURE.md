# Architecture — Nakama Replay Viewer

## What I built and why

The tool is a single-page browser application: one `index.html` file containing all HTML, CSS, and JavaScript with no build step, no framework, and no backend server. The data pipeline is a separate Python script that runs once offline to convert raw parquet files into browser-ready JSON.

**Stack choices:**

| Layer | Choice | Reason |
|---|---|---|
| Rendering | HTML5 Canvas 2D | Needs to draw 50,000+ position samples and multiple overlapping layers (paths, heatmaps, event markers) per frame. DOM/SVG would be too slow; WebGL is overkill for 2D. Canvas gives direct pixel control at acceptable complexity. |
| UI framework | Vanilla JS | Zero-dependency constraint — the tool must open from `file://` with no npm, no bundler, no network (except the CDN decompression library). React would require a build step. |
| Compression | pako.js (CDN) | The full event dataset is 2.7 MB gzip-compressed (vs ~30 MB raw). pako decompresses it client-side in ~200ms. Loading it uncompressed would be impractical on slower connections. |
| Data processing | Python + PyArrow | Reading 1,243 `.nakama-0` parquet files requires columnar I/O; PyArrow does this ~10× faster than a pure-Python CSV approach. Pandas is used only for row iteration. |
| Hosting | Netlify (GitHub CI/CD) | Static file hosting with zero configuration beyond a `netlify.toml`. Auto-deploys on every push to `main`. |

---

## Data flow

```
1,243 .nakama-0 parquet files
  (February_10 … February_14 folders)
          │
          ▼
  process_nakama.py   (run once, offline)
  ├── PyArrow reads each parquet table
  ├── Detects bots: user_id matches ^\d+$ → is_bot = true
  ├── Strips ".nakama-0" suffix from match_id stored inside parquet
  ├── Decodes event column (stored as raw bytes → UTF-8)
  └── Writes two output files:
       ├── matches_index.json      (145 KB) — match metadata for filter dropdowns
       └── events_by_map.json.gz   (2.7 MB) — all events, grouped map_id → match_id
          │
          ▼
  Browser (index.html)
  ├── fetch("data/matches_index.json")         → populate date / map / match dropdowns
  ├── fetch("data/events_by_map.json.gz")      → pako.inflate() → JSON.parse()
  ├── User selects a match
  ├── processMatch() — separates events by player, builds positions[] and markers[]
  │    ├── Binary search (cutoffIndex) used for O(log n) timeline scrubbing
  │    └── Timestamps: ts is stored as ISO-8601 but the underlying value is in
  │         Unix seconds (not milliseconds). new Date(ts).getTime() returns seconds-as-ms,
  │         so we multiply by 1000 to get real microsecond durations.
  └── drawMatch() — renders onto Canvas at 60fps via requestAnimationFrame
       ├── Paths view: polylines per player, colour-coded (blue=human, red=bot)
       ├── Heatmap view: off-screen canvas accumulation → palette LUT colorisation
       └── Event markers: 💀 kills, ✕ deaths, 📦 loot, ⚡ storm, overlaid on minimap
```

---

## Coordinate mapping — the tricky part

The game engine uses a **right-handed 3D world coordinate system** where `X` and `Z` define the horizontal plane and `Y` is vertical height (not used in the viewer). The minimap images are 1024×1024 PNG files in standard image space (origin top-left, Y increases downward).

The mapping formula (provided in the spec and applied verbatim):

```
u        = (world_x  - origin_x) / scale      →  normalised [0, 1] left→right
v        = (world_z  - origin_z) / scale      →  normalised [0, 1] bottom→top

pixel_x  = u × 1024
pixel_y  = (1 − v) × 1024                     ←  Y-flip: game Z increases northward,
                                                   image Y increases downward
```

Per-map calibration constants:

| Map | `origin_x` | `origin_z` | `scale` |
|---|---|---|---|
| AmbroseValley | −370 | −473 | 900 |
| GrandRift | −290 | −290 | 581 |
| Lockdown | −500 | −500 | 1000 |

`origin_x / origin_z` are the world-space coordinates that correspond to the bottom-left corner of each minimap image. `scale` is the world-space distance that spans the full 1024-pixel width (and height) of the image.

The final canvas pixel is then scaled from the 1024×1024 logical space to whatever the actual canvas dimensions are at render time:

```javascript
return {
  x: (pixel_x / 1024) * canvasWidth,
  y: (pixel_y / 1024) * canvasHeight
};
```

This means the same `worldToCanvas()` function works correctly whether the canvas is 600px or 1200px wide, and also works correctly inside the off-screen heatmap buffer (always rendered at canvas resolution).

Zoom and pan are applied as a `ctx.translate / ctx.scale` transform applied before every draw — the world→canvas mapping itself never changes, keeping coordinate logic simple.

---

## Assumptions made

| Situation | What the data showed | What I assumed |
|---|---|---|
| Bot detection | No explicit `is_bot` field in parquet | A numeric-only `user_id` (e.g. `"12345"`) is a bot; a UUID string is a human. This matched all observable patterns in the data. |
| Timestamp units | `ts` column is typed `timestamp[ms]` in parquet schema | The actual stored values are Unix **seconds** (not milliseconds). `new Date(ts).getTime()` returns seconds-cast-as-ms. Multiplying by 1,000 gives realistic match durations (6–10 min) and is confirmed by the heatmap timeline being correct. |
| match_id suffix | The `match_id` field inside each parquet file ends with `.nakama-0` | This suffix is an artefact of the file format and not part of the logical match ID. It is stripped at ingestion so both output files use clean UUIDs. |
| Player counting | `player_count` in early drafts counted all participants | Bots should not count as human players. The index now stores `player_count` (humans only) and `bot_count` separately, derived from the `is_bot` flag per participant file. |
| Y-axis orientation | World Z increases in the opposite direction to canvas Y | Confirmed by visual inspection: paths without the `(1 − v)` flip appeared mirrored north-south on the minimap. |

---

## Major tradeoffs

| Decision | Alternative considered | What I chose and why |
|---|---|---|
| Single HTML file | Separate JS/CSS files or a bundled React app | Single file: opens from `file://`, zero install, trivially deployable to any static host. Acceptable complexity for a single-feature tool. |
| Load all events at startup | Lazy-load per-match on demand | Load once: the compressed payload is only 2.7 MB, decompresses in ~200ms, and eliminates per-match latency. With 796 matches, per-match fetches would add noticeable delay on every selection change. |
| Python preprocessing step | Process parquet in-browser (via WASM) | Offline Python: WASM parquet readers are still experimental; the one-time 30-second Python run is a worthwhile trade for a simple, reliable browser payload. |
| Canvas 2D + off-screen buffer | WebGL shaders | Canvas 2D: sufficient for the data volumes here (~50K position samples). WebGL would add significant complexity with minimal visual improvement at this scale. |
| `lighter` compositing for heatmap | Kernel density estimation (KDE) | `lighter` compositing: fast, GPU-accelerated, produces visually convincing results. KDE would give a statistically precise density field but at O(n²) cost. A post-render alpha normalisation pass is used to prevent saturation without sacrificing performance. |
