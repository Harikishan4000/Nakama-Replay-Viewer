# Insights - Nakama Replay Viewer

Three findings drawn from 796 matches across AmbroseValley, GrandRift, and Lockdown (February 10–14, 2025).

---

## Insight 1 - The Labour Quarters / Mine Pit corridor is GrandRift's only real arena

### What caught my eye

Enabling the daily heatmap on GrandRift immediately showed two hot orange blobs: one at Labour Quarters on the western edge, and one spilling down from Cave House into the Mine Pit. The rest of the map - Burnt Zone, Maintenance Bay, Gas Station, Engineer's Quarters - were barely registered. The lonely zones proved the same too (Set at<= 5 events).

### The data

Using a 4×4 grid mapped over GrandRift's world coordinates:

| Zone (grid cell) | Kills | % of map total | Loot events | % of map total |
|---|---|---|---|---|
| Labour Quarters / Cave House (1,1) | 53 | 27.5% | 222 | 25.2% |
| Mine Pit corridor (1,2) | 54 | 28.0% | 156 | 17.7% |
| **Combined** | **107** | **55.4%** | **378** | **42.9%** |

The two cells together account for 55% of all kills while covering roughly 12% of the map's playable area. The kill-to-loot ratio in these cells is meaningfully higher than the map average, meaning players are not just passing through - they are being funnelled into encounters they cannot avoid.

The heatmap also shows blue traffic lines tracing the road network, and those roads converge directly on Mine Pit from every direction. There is no practical route from the western half of the map to the eastern half that does not pass near Mine Pit.

### Why a level designer should care

Mine Pit functions as an involuntary chokepoint, not a chosen hot drop. Players who want to reach Engineer's Quarters or Gas Station must pass through it regardless of their intended route. This collapses mid-game decision-making - positioning, rotation, and loot pathing all become the same choice. A map where 55% of kills happen in two quadrants has effectively shrunk itself.

### Actionable items

- **Add a bypass route** from the western side (Labour Quarters) to the eastern side (Engineer's Quarters) that goes around Mine Pit rather than through it. This gives players a rotation option and reduces enforced combat.
- **Redistribute high-value loot** away from the Mine Pit approach. Currently the funnel is self-reinforcing: high loot → players arrive → kills happen. Moving one tier of loot to Burnt Zone or Maintenance Bay would create a genuine alternative drop point.
- **Metrics to watch:** kill concentration ratio (what % of kills fall in the top 2 cells) and route diversity (how many distinct paths players take through the map per session). Target: top 2 cells below 40% of kills.

---

## Insight 2 - Looting is a human-only activity, and the data likely records only one player per match

### What caught my eye

Two things stood out together. First, watching the path view for matches with a single human player: the human path shows frequent direction changes and short stops - the signature of looting - while bot paths are smooth and continuous with no pauses. Second, the match list itself: 93.3% of all 796 matches contain exactly one human player, yet that player regularly shows kill events. These kills are registered as `BotKill` events on the human's file. This strongly suggests the data pipeline records one parquet file per player, and what we are seeing in the vast majority of matches is solely the single human participant's perspective. Bots appear as trajectory data and kill targets, not as independent recording subjects.

### The data

Across all 796 matches (all three maps combined):

| Player type | Distinct user_ids | Loot events | User_ids with any loot |
|---|---|---|---|
| Human | 245 | 12,770 | present across all active humans |
| Bot | 94 | 115* | **2 out of 94 (2.1%)** |

*The 115 attributed bot loot events come almost entirely from a single user_id (`1429`) which also emits both `Position` and `BotPosition` event types in the same records - inconsistent with any other bot in the dataset. This looks like a test account or a data recording artefact rather than genuine bot looting behaviour. Excluding it, **92 out of 94 bot user_ids have exactly zero loot events**. Looting is functionally a human-only activity in this dataset.

The consequence is significant: because 93.3% of matches are single-human sessions, the loot heatmap reflects the behaviour of one real player per match - not a contested economy. The 12,885 total loot events in the dataset represent real human decisions, but none of them were contested by a bot picking up the same node first.

### Why a level designer should care

Loot placement is one of the primary levers for shaping player movement and conflict. When the data shows which zones players loot most, that signal is real - but it reflects uncontested access, not competition. A designer who wants to know "does high-value loot in Burnt Zone draw players there?" will see the answer in human paths, but cannot yet measure whether that loot would survive long enough to be worth routing toward in a full human lobby where other players are also looting. This means:

- Loot heatmaps from this dataset show player pathing preferences, not contested resource dynamics.
- Bot kill counts (2,415 total `BotKill` events) reflect positional AI working correctly - bots find and engage players - but bots are not competing for resources before the engagement, which would change positioning and arrival timing.
- Any balance tuning of loot spawn rates or loot zone values based solely on this data needs to account for the fact that it was gathered in effectively single-player conditions.

### Actionable items

- **Instrument bot loot behaviour** so that bots pick up loot nodes at a rate calibrated to real player behaviour. This changes the contested-loot dynamics and will produce more realistic playtest data for zone valuation.
- **Verify the single-player-per-match recording assumption** - if the intent was to capture all participants in a match, check whether bot parquet files are being written and ingested. If they are being skipped deliberately, document this so analysts know the dataset represents the human perspective only.
- **Metrics to watch:** loot contest rate (how often two players attempt to loot the same node within a short time window), and bot loot participation rate (what % of bots pick up at least one item per match - currently ~2%).

---

## Insight 3 - AmbroseValley is carrying the game; GrandRift is nearly invisible

### What caught my eye

Opening the match filter on any day, the map dropdown immediately reveals the imbalance. Scrolling through the match list, GrandRift entries are rare. On some days there are fewer than 10 GrandRift matches visible even before filtering by date.

### The data

**Match distribution over the full 5-day period:**

| Map | Matches | Share |
|---|---|---|
| AmbroseValley | 566 | 71.1% |
| Lockdown | 171 | 21.5% |
| GrandRift | 59 | 7.4% |

**Session volume decline day by day (all maps combined):**

| Date | Matches | Change |
|---|---|---|
| Feb 10 | 285 | - |
| Feb 11 | 200 | −30% |
| Feb 12 | 162 | −19% |
| Feb 13 | 112 | −31% |
| Feb 14 | 37 | −67% |
| **Total decline** | | **−87%** |

Two separate problems are visible here. First, GrandRift's 7.4% share is low enough that it may not be generating sufficient data to balance-test meaningfully - 59 matches over 5 days means some daily combinations have fewer than 10 matches, and kill/death patterns in those slices are statistically thin. Second, the 87% volume decline over 5 days is steep enough to suggest either a constrained test period (intentional) or player churn (a design or onboarding signal).

A third signal appears in the tool's Lonely Zones panel. Setting the event threshold to ≤5 on GrandRift across a full day reveals large blank areas deep within the playable map. The comparison below uses only interior cells (the outermost grid ring is excluded as it falls outside the playable boundary):

| Metric | GrandRift | AmbroseValley |
|---|---|---|
| Interior cells analysed (cols/rows 1–14) | 196 | 196 |
| Cells with 0 events | 83 (42%) | 69 (35%) |
| Cells with ≤5 events | **93 (47%)** | **79 (40%)** |
| Match count used to generate this data | 59 | 566 |

AmbroseValley has nearly 10× more matches yet still has fewer lonely interior cells than GrandRift. This is not a sample-size problem - it means GrandRift has significant developed map geometry that players are simply never reaching. The activity map confirms the pattern: interior cells in the northern (rows 1–2) and southern (rows 13–14) portions of GrandRift are almost entirely dead, even though they sit within the playable boundary. Burnt Zone, Maintenance Bay, and the road leading to Gas Station are all largely bypassed in favour of the Mine Pit corridor.

GrandRift also has the smallest world scale (`scale = 581` vs Lockdown's `1000` and AmbroseValley's `900`), making it the tightest map geometrically. Combined with the corridor chokepoint described in Insight 1 and the lonely zone pattern, it appears that most of the map's named locations exist on paper but not in practice.

### Why a level designer should care

A map that captures 7% of play sessions is generating 7% of the feedback signal. Kill zone data, rotation patterns, and loot path analysis for GrandRift are all based on a thin sample. If the map is intended as a competitive environment alongside AmbroseValley and Lockdown, its current play share means level design iterations are being made with much less data than the other maps receive.

The daily decline also means that whatever problems exist are not self-correcting - players who tried the game early did not return at the same rate. Whether that is a map design issue, a matchmaking issue, or a test-period artefact, the tool's filter-by-date feature makes it easy to compare early-session behaviour (Feb 10) against late-session behaviour (Feb 14) to look for differences in where players go and how long they survive.

### Actionable items

- **Investigate the GrandRift routing problem** (see Insight 1) as a likely contributor to low return rate - a map where early engagements feel unavoidable tends to produce faster eliminations and shorter sessions, which reduces motivation to replay.
- **Address the lonely zone problem directly.** Burnt Zone, Maintenance Bay, and Gas Station are named locations that currently attract near-zero traffic. Options: add a loot tier or objective to one of these zones to create an alternative drop point, or redesign the road layout so that these areas sit on a natural rotation path rather than off a dead end.
- **Add a map-selection incentive** (bonus loot tier, daily challenge) to GrandRift to bring its session share above 20%. Run this for one week and measure whether the kill distribution also spreads out (more routes = more varied combat) and whether the lonely zone count falls.
- **Metrics to watch:** GrandRift session share (target: >20%), interior lonely cell count at ≤5 events threshold (target: below 40%, on par with AmbroseValley at comparable match volume), median match duration per map, and D1/D2 retention split by map.
