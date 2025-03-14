# Wildfire Impact Simulation: Camp Fire Case Study

This project models the spread and destructive impact of the 2018 Camp Fire using a discrete event simulation approach. It evaluates how structure-level characteristics particularly building materials affect vulnerability to fire. Using real spatial data and scenario-based modeling, the simulation enables "what-if" testing of fire mitigation strategies like improved siding or deck replacements.

---

## Contents

- `fire_simulation.py` — Main script: data prep, simulation, and visualizations
- `fire_progression_data.csv` — Fire observation points with timestamps
- `POSTFIRE_MASTER_DATA_SHARE_-Camp.csv`, `Camp_Fire_Structure_Damage_Data.csv` — Original damage assessment data
- `fire_perimeter_shapefile/` — Folder containing Camp Fire perimeter shapefiles
- `event_log_combined.csv` — Combined event log for all simulation scenarios
- `fire_simulation_event_log.csv` — Event log for baseline scenario
- `summary_destruction_by_scenario.csv` — Summary table of destruction counts per scenario
- `comparison_siding.csv`, `comparison_roof.csv`, `comparison_deck1.csv`, `comparison_deck2.csv` — CSVs of material-based scenario comparisons
- `destruction_counts.csv`, `structure_destroyed_per_scenario.png` — Output charts
- `fire_area_progression_map.html`, `fire_simulation_timeline_map.html` — Interactive animated maps
- `perimeter_infra_progress_map.png`, `fire_intensity_heatmap.png` — Static visualization images
- `fire_spread_timelapse.gif` — GIF animation of fire spread

---

## Project Goals

- Simulate fire arrival, ignition, and destruction at the structure level
- Analyze how different materials (siding, roof, deck) contribute to fire risk
- Test mitigation strategies using what-if scenarios
- Visualize fire spread and structure destruction on interactive maps

---

## Methods Summary

- **Fire arrival times** estimated using proximity to reported fire progression points
- **Flammability scores** derived from observed damage rates per material type
- **Composite flammability** calculated using siding, roof, and deck characteristics
- **Simulation events**:
  - `Fire_Arrival`
  - `Ignition` (probabilistic)
  - `Destroyed` (delayed post-ignition)
- **Event log** contains timestamps, structure IDs, event types, and scenario labels

---

## How to Run

1. Clone the repository  
2. Place data files in the working directory:
   - `fire_progression_data.csv`
   - `POSTFIRE_MASTER_DATA_SHARE_-Camp.csv`
   - Fire perimeter shapefiles
3. Install dependencies:
   ```bash
   pip install pandas geopandas shapely folium matplotlib scipy
   ```
4. Run the simulation script:
   ```bash
   python fire_simulation.py
   ```

---

## Scenarios Simulated

| Scenario                        | Description                                        |
|--------------------------------|----------------------------------------------------|
| `baseline`                     | Simulation using original material composition     |
| `all_ignition_resistant_siding`| Assumes all siding is ignition resistant           |
| `no_wood_decks`                | Replaces all wood decks with masonry/concrete      |

---

## Visual Outputs

- **Animated fire progression map** (`fire_area_progression_map.html`)
- **Scenario comparison map** (`structure_destruction_overlay_map.html`)
- **Bar and timeline plots** for structure destruction by scenario

---

## Data Sources

- CAL FIRE post-fire structure assessments
- Fire perimeter shapefiles (via Data Basin)
- Hand-collected fire progression points dataset

---

## Results Highlights

- The simulation showed clear differences in destruction outcomes between baseline and mitigation strategies.
- Structures with ignition-resistant siding showed significantly lower ignition and destruction rates.
- Removing wood decks reduced destruction moderately, especially near initial ignition zones.

---

## Contributors

Maddy Lok and Hamdi Kucukengin