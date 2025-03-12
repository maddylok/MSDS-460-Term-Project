# --- Load the Data ---
import geopandas as gpd
import pandas as pd

# Load the Fire Perimeter Shapefile
fire_perimeter = gpd.read_file("fire_perimeter_shapefile/data/commondata/tnc_pardise/Camp_Perimeter.shp")
print("Fire Perimeter Columns:")
print(fire_perimeter.columns)
print(fire_perimeter.head())

# Load the Fire Progression CSV
fire_progression = pd.read_csv("fire_progression_data.csv")
print("\nFire Progression CSV Columns:")
print(fire_progression.columns)
print(fire_progression.head())

# Load the Infrastructure Damage CSV
infrastructure = pd.read_csv("POSTFIRE_MASTER_DATA_SHARE_-Camp.csv")
print("\nInfrastructure Damage CSV Columns:")
print(infrastructure.columns)
print(infrastructure.head())

# --- Convert CSVs to GeoDataFrames ---
from shapely.geometry import Point

# Convert the Fire Progression CSV to GeoDataFrame
fire_progression['geometry'] = fire_progression.apply(
    lambda row: Point(row['Longitude'], row['Latitude']), axis=1
)
fire_progression_gdf = gpd.GeoDataFrame(fire_progression, geometry='geometry', crs="EPSG:4326")

# Convert the Infrastructure Damage CSV to GeoDataFrame
infrastructure['geometry'] = infrastructure.apply(
    lambda row: Point(row['Longitude'], row['Latitude']), axis=1
)
infrastructure_gdf = gpd.GeoDataFrame(infrastructure, geometry='geometry', crs="EPSG:4326")

# Reproject the Fire Progression and Infrastructure Damage to match the Fire Perimeter CRS
print("\nFire perimeter CRS:", fire_perimeter.crs)

fire_progression_gdf = fire_progression_gdf.to_crs(fire_perimeter.crs)
infrastructure_gdf = infrastructure_gdf.to_crs(fire_perimeter.crs)

# --- Visualize the Data ---
import matplotlib.pyplot as plt
import contextily as ctx

fig, ax = plt.subplots(figsize=(12, 10))

# Reproject to Web Mercator (for compatibility with contextily basemap)
fire_perimeter.to_crs(epsg=3857).plot(ax=ax, edgecolor='red', linewidth=1, facecolor='none', label="Fire Perimeter")
infrastructure_gdf.to_crs(epsg=3857).plot(ax=ax, color='blue', markersize=3, alpha=0.5, label="Structures")
fire_progression_gdf.to_crs(epsg=3857).plot(ax=ax, color='orange', markersize=5, alpha=0.5, label="Fire Progression")

# Add satellite imagery as basemap
ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)

# Final touches
ax.set_title("Camp Fire with Real-World Map Context")
ax.set_axis_off()
plt.legend()
plt.show()

# --- Assign Fire Arrival Time to infrastructures ---

# Combine the date and time columns into a single datetime column
fire_progression_gdf['Fire_Timestamp'] = pd.to_datetime(
    fire_progression_gdf['Date'] + ' ' + fire_progression_gdf['Time'],
    # Handle bad entries
    errors='coerce'
)

# Assign a fire progression point to each structure
from scipy.spatial import cKDTree
import numpy as np

# ---- Missing Data Handling ----
# Drop rows with missing or invalid geometry
fire_progression_gdf = fire_progression_gdf[
    fire_progression_gdf.geometry.notnull() &
    ~fire_progression_gdf.geometry.is_empty
]

# Drop rows with missing latitude/longitude
fire_progression_gdf = fire_progression_gdf[
    fire_progression_gdf['geometry'].apply(lambda g: g.is_valid)
]

# Reset index
fire_progression_gdf = fire_progression_gdf.reset_index(drop=True)

# Get the centroids as coordinate arrays
fire_coords = np.array(list(zip(fire_progression_gdf.geometry.x, fire_progression_gdf.geometry.y)))
structure_coords = np.array(list(zip(infrastructure_gdf.geometry.x, infrastructure_gdf.geometry.y)))

# Create the spatial index tree
print(f"KD-tree will be built from {len(fire_coords)} fire points.")
fire_tree = cKDTree(fire_coords)

# Query the nearest fire progression point for each structure
distances, indices = fire_tree.query(structure_coords, k=1)

# Assign fire arrival time to each structure based on distance
infrastructure_gdf['Fire_Arrival_Time'] = fire_progression_gdf.iloc[indices]['Fire_Timestamp'].values
infrastructure_gdf['Distance_To_FirePoint'] = distances

print(infrastructure_gdf[['Fire_Arrival_Time', 'Distance_To_FirePoint']].head())

# --- Run Simulation Using Pre-Defined Flammability Scores ---
# In this section, we will simulate fire progression based on a pre-defined flammability score for each structure material.

# Extract the material types for each section of the infrastructure
material_columns = [
    '* Exterior Siding',
    '* Roof Construction',
    '* Deck/Porch On Grade',
    '* Deck/Porch Elevated'
]

for col in material_columns:
    print(f"\n--- Unique values in {col} ---")
    print(infrastructure_gdf[col].dropna().unique())
    
# Assign pre-defined flammability scores to each material type
# Exterior Siding
siding_scores = {
    "Ignition Resistant": 0.35,
    "Combustible": 0.85,
    "Unknown": 0.5,
    "": 0.5
}

# Roof
roof_scores = {
    "Asphalt": 0.8,
    "Metal": 0.2,
    "Concrete": 0.3,
    "Tile": 0.4,
    "Wood": 0.95,
    "Other": 0.6,
    "Unknown": 0.5,
    "": 0.5
}

# Decks (on grade and elevated use same scores)
deck_scores = {
    "Wood": 0.9,
    "Composite": 0.5,
    "Masonry/Concrete": 0.2,
    "No Deck/Porch": 0.1,
    "Unknown": 0.5,
    "": 0.5
}

# Generate a composite flammability score based on the four structure section materials
def compute_flammability(row):
    siding = str(row.get('* Exterior Siding', '')).strip()
    roof = str(row.get('* Roof Construction', '')).strip()
    deck1 = str(row.get('* Deck/Porch On Grade', '')).strip()
    deck2 = str(row.get('* Deck/Porch Elevated', '')).strip()
    
    siding_score = siding_scores.get(siding, 0.5)
    roof_score = roof_scores.get(roof, 0.5)
    deck1_score = deck_scores.get(deck1, 0.5)
    deck2_score = deck_scores.get(deck2, 0.5)
    
    return np.mean([siding_score, roof_score, deck1_score, deck2_score])

infrastructure_gdf['Composite_Flammability'] = infrastructure_gdf.apply(compute_flammability, axis=1)

# --- Simulation Loop Using Composite Flammability and Distance-Based Delay Implementation ---

import random
from datetime import timedelta

FIRE_SPREAD_RATE = 20 # m/min

# Calculate the delay in minutes and simulate fire arrival time
infrastructure_gdf['Fire_Delay_Minutes'] = infrastructure_gdf['Distance_To_FirePoint'] / FIRE_SPREAD_RATE
infrastructure_gdf['Simulated_Fire_Arrival_Time'] = infrastructure_gdf.apply(
    lambda row: row['Fire_Arrival_Time'] + pd.to_timedelta(row['Fire_Delay_Minutes'], unit='m')
    if pd.notnull(row['Fire_Arrival_Time']) else pd.NaT,
    axis=1
)

event_log = []

for idx, row in infrastructure_gdf.iterrows():
    structure_id = row['OBJECTID']
    arrival_time = row['Simulated_Fire_Arrival_Time']
    flammability = row.get('Composite_Flammability', 0.5)
    
    if pd.notnull(arrival_time):
        # Simulate fire arrival event
        event_log.append({
            "Case_ID": structure_id,
            "Timestamp": arrival_time,
            "Event": "Fire_Arrival",
            "Flammability_Score": round(flammability, 2)
        })
        
        # Simulate the ignition event
        if random.random() < flammability:
            ignition_time = arrival_time + timedelta(minutes=random.randint(5, 30))
            event_log.append({
                "Case_ID": structure_id,
                "Timestamp": ignition_time,
                "Event": "Ignition",
                "Flammability_Score": round(flammability, 2)
            })
            
            # Simulate the destruction event
            destruction_time = ignition_time + timedelta(minutes=random.randint(5, 90))
            event_log.append({
                "Case_ID": structure_id,
                "Timestamp": destruction_time,
                "Event": "Destroyed",
                "Flammability_Score": round(flammability, 2)
            })
            
# Convert the event log to a DataFrame and sort by time
event_log_df = pd.DataFrame(event_log)
event_log_df = event_log_df.sort_values(by=["Timestamp", "Case_ID"]).reset_index(drop=True)

print(event_log_df.head())

# Save the event log
event_log_df.to_csv("fire_simulation_event_log.csv", index=False)

# --- Generate Empirical Flammability Scores Using Destruction Data ---
# In this section, we will calculate empirical flammability scores based on which structures were damaged to what extent and what materials they were made of.

# Determine the damage levels
unique_damage_levels = infrastructure_gdf['* Damage'].dropna().unique()
print("\nUnique Damage levels:")
for val in unique_damage_levels:
    print(f"- {val}")
    
# Assign 'destroyed' status to structures that are >50% damaged
infrastructure_gdf['Destroyed'] = infrastructure_gdf['* Damage'].str.contains('Destroyed', case=False, na=False)

# Function to calculate the empirical destruction rate for each section
def calculate_empirical_destruction_rate(df, component_col):
    result = df.groupby(component_col).agg(
        Total=('Destroyed', 'count'),
        Destroyed=('Destroyed', 'sum')
    )
    result['Destruction_Rate'] = result['Destroyed'] / result['Total']
    return result.sort_values('Destruction_Rate', ascending=False)

# Calculate empirical destruction rates for each section
siding_rates = calculate_empirical_destruction_rate(infrastructure_gdf, '* Exterior Siding')
roof_rates = calculate_empirical_destruction_rate(infrastructure_gdf, '* Roof Construction')
deck1_rates = calculate_empirical_destruction_rate(infrastructure_gdf, '* Deck/Porch On Grade')
deck2_rates = calculate_empirical_destruction_rate(infrastructure_gdf, '* Deck/Porch Elevated')

# Report the results
print("\nExterior Siding:\n", siding_rates)
print("\nRoof Construction:\n", roof_rates)
print("\nDeck/Porch On Grade:\n", deck1_rates)
print("\nDeck/Porch Elevated:\n", deck2_rates)

# Function to compare the empirical flammability data with the simulated flammability scores.
def compare_simulated_vs_empirical(df, component_col, simulated_scores_dict, label):
    # Empirical
    empirical = df.groupby(component_col).agg(
        Total=('Destroyed', 'count'),
        Destroyed=('Destroyed', 'sum')
    )
    empirical['Destruction_Rate'] = empirical['Destroyed'] / empirical['Total']
    empirical = empirical.reset_index().rename(columns={component_col: 'Material'})
    
    # Simulated
    empirical['Simulated_Flammability'] = empirical['Material'].map(simulated_scores_dict).fillna(0.5)
    
    # Difference between simulation and empirical
    empirical['Difference'] = empirical['Destruction_Rate'] - empirical['Simulated_Flammability']
    
    print(f"\nComparison Table - {label}")
    print(empirical[['Material', 'Simulated_Flammability', 'Destruction_Rate', 'Difference']])
    
    return empirical

# Compare the simulated and empirical flammability scores for each section
siding_comparison = compare_simulated_vs_empirical(
    infrastructure_gdf, '* Exterior Siding', siding_scores, 'Exterior Siding'
)

roof_comparison = compare_simulated_vs_empirical(
    infrastructure_gdf, '* Roof Construction', roof_scores, 'Roof Construction'
)

deck1_comparison = compare_simulated_vs_empirical(
    infrastructure_gdf, '* Deck/Porch On Grade', deck_scores, 'Deck/Porch On Grade'
)

deck2_comparison = compare_simulated_vs_empirical(
    infrastructure_gdf, '* Deck/Porch Elevated', deck_scores, 'Deck/Porch Elevated'
)

# Export the tables as CSV
siding_comparison.to_csv("comparison_siding.csv", index=False)
roof_comparison.to_csv("comparison_roof.csv", index=False)
deck1_comparison.to_csv("comparison_deck1.csv", index=False)
deck2_comparison.to_csv("comparison_deck2.csv", index=False)

print("\nSaved comparison tables as CSV files.")

# --- Visualize the Simulation on a Map ---

import folium
from folium.plugins import TimestampedGeoJson
from folium import GeoJson

# Initial map generation showed an interactive but under-optimized map that ran slow.
# Following code only visualizes the most significant (latest) event for each structure to tackle this performance issue.
latest_events = event_log_df.sort_values('Timestamp').drop_duplicates('Case_ID', keep='last')

# Merge geometry with event log
geo_events = latest_events.merge(
    infrastructure_gdf[['OBJECTID', 'geometry']], left_on='Case_ID', right_on='OBJECTID'
)

# Convert to GeoDataFrame
geo_events_gdf = gpd.GeoDataFrame(geo_events, geometry='geometry', crs=infrastructure_gdf.crs)
geo_events_gdf = geo_events_gdf.to_crs(epsg=4326)

# Format the data for the TimestampedGeoJson
features = []
for _, row in geo_events_gdf.iterrows():
    timestamp = row['Timestamp'].isoformat()
    features.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [row.geometry.x, row.geometry.y],
        },
        "properties": {
            "time": timestamp,
            "popup": f"{row['Event']}<br>ID: {row['Case_ID']}<br>Flammability: {row['Flammability_Score']}",
            "style": {
                "color": (
                    "orange" if row['Event'] == "Fire_Arrival"
                    else "purple" if row['Event'] == "Ignition"
                    else "black"
                )
            }
        }
    })

geojson = {
    "type": "FeatureCollection",
    "features": features
}

# Center the map on the fire zone
center_lat = geo_events_gdf.geometry.y.mean()
center_lon = geo_events_gdf.geometry.x.mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB dark_matter")

TimestampedGeoJson(
    geojson,
    period="PT1H", # 1 hour intervals
    add_last_point=True,
    auto_play=False,
    loop=False,
    max_speed=1,
    loop_button=True,
    date_options="YYYY-MM-DD HH:mm",
    time_slider_drag_update=True
).add_to(m)

fire_perimeter_wgs84 = fire_perimeter.to_crs(epsg=4326)[['geometry']].copy()

GeoJson(
    fire_perimeter_wgs84,
    name="Fire Perimeter",
    style_function=lambda feature: {
        "fillColor": "red",
        "color": "red",
        "weight": 2,
        "fillOpacity": 0.1,
    }
).add_to(m)

m.save("fire_simulation_timeline_map.html")

# --- Area-Based Fire Spread Simulation ---
# While the previous simulation can be informative, it is not performant, and freezes a lot.
# Using an area-based simulation will look smoother and be more performant.

from shapely.geometry import mapping
from shapely.ops import unary_union
from folium.plugins import TimestampedGeoJson
import folium

fire_progression_gdf['Fire_Timestamp'] = fire_progression_gdf['Fire_Timestamp'].apply(
    lambda dt: dt.replace(year=2018) if pd.notnull(dt) else pd.NaT
)

# Round the timestamps to the nearest hour for aggregation
fire_progression_gdf['Time_Bin'] = pd.to_datetime(fire_progression_gdf['Fire_Timestamp']).dt.floor('h')

# Generate the fire zones
fire_zones = []
for time_bin, group in fire_progression_gdf.groupby('Time_Bin'):
    if group.empty:
        continue
    
    # Create buffer zones around the fire points
    buffered = group.geometry.buffer(800) # 800 meters
    merged_zone = unary_union(buffered)
    
    if merged_zone.is_empty:
        continue
    
    # Reproject the merged zone back to EPSG:4326
    merged_latlon = gpd.GeoSeries([merged_zone], crs=3310).to_crs(epsg=4326).iloc[0]
    
    # Wrap outputs as FeatureCollection
    fire_zones.append({
        "type": "Feature",
        "geometry": mapping(merged_latlon),
        "properties": {
            "time": time_bin.isoformat(),
            "style": {
                "color": "orange",
                "weight": 1,
                "fillColor": "red",
                "fillOpacity": 0.4
            }
        }
    })

# Center the map on the fire zone
center = fire_progression_gdf.to_crs(epsg=4326).geometry.union_all().centroid
m = folium.Map(location=[center.y, center.x], zoom_start=11, tiles="CartoDB positron")

# Add the fire perimeter
fire_perimeter_wgs84 = fire_perimeter.to_crs(epsg=4326)[['geometry']]
folium.GeoJson(
    fire_perimeter_wgs84,
    name="Fire Perimeter",
    style_function=lambda feature: {
        "color": "red",
        "weight": 2,
        "fillOpacity": 0,
    }
).add_to(m)

# Add the animated fire zones
TimestampedGeoJson(
    {
        "type": "FeatureCollection",
        "features": fire_zones
    },
    period="PT1H",
    add_last_point=True,
    auto_play=False,
    loop=False,
    max_speed=1,
    loop_button=True,
    date_options="YYYY-MM-DD HH:mm",
    time_slider_drag_update=True
).add_to(m)

m.save("fire_area_progression_map.html")