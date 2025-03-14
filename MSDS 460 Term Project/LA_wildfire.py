import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns
import folium
from folium.plugins import HeatMap
from scipy.spatial import cKDTree
import numpy as np

df_fires=pd.read_csv('/Users/spud/Documents/MSDS 460/MSDS 460 Term Project/Infrared_Spread_Data.csv')

df_damage=pd.read_csv('/Users/spud/Documents/MSDS 460/MSDS 460 Term Project/POSTFIRE_MASTER_DATA_SHARE_8915263461538710042.csv', low_memory=False)

with open('/Users/spud/Documents/MSDS 460/MSDS 460 Term Project/Infrared_Spread_Data.csv', 'r', encoding='utf-8') as f:
    for _ in range(10):  # Print first 10 lines
        print(f.readline())

df_raw = pd.read_csv('/Users/spud/Documents/MSDS 460/MSDS 460 Term Project/Infrared_Spread_Data.csv', sep=None, engine='python', nrows=5)
print(df_raw)

import chardet

with open('/Users/spud/Documents/MSDS 460/MSDS 460 Term Project/Infrared_Spread_Data.csv', 'rb') as f:
    rawdata = f.read(10000)  # Read first 10,000 bytes
    result = chardet.detect(rawdata)
    print("Detected file encoding:", result['encoding'])


df_fires = pd.read_csv('/Users/spud/Documents/MSDS 460/MSDS 460 Term Project/Infrared_Spread_Data.csv', dtype=str, low_memory=False)
print(df_fires.head())

print(df_fires.dtypes)  # Display column data types

if "acq_time" in df_fires.columns:
    df_fires["acq_time"] = pd.to_numeric(df_fires["acq_time"], errors="coerce")  # Convert to numeric

if "acq_date" in df_fires.columns:
    df_fires["acq_date"] = pd.to_datetime(df_fires["acq_date"], errors="coerce")  # Convert to datetime

print(df_fires.head())  # Verify data is loading correctly
print("Number of records:", len(df_fires))

print(df_fires.isnull().sum())  # Count missing values per column

# Convert latitude and longitude to numeric
df_fires["latitude"] = pd.to_numeric(df_fires["latitude"], errors="coerce")
df_fires["longitude"] = pd.to_numeric(df_fires["longitude"], errors="coerce")

# Drop any rows where latitude or longitude is NaN
df_fires = df_fires.dropna(subset=["latitude", "longitude"])

# Now apply the filtering for Los Angeles
LA_BOUNDS = {
    "lat_min": 34.0,
    "lat_max": 34.5,
    "lon_min": -119.0,
    "lon_max": -118.5
}

df_fires = df_fires[
    (df_fires["latitude"] >= LA_BOUNDS["lat_min"]) &
    (df_fires["latitude"] <= LA_BOUNDS["lat_max"]) &
    (df_fires["longitude"] >= LA_BOUNDS["lon_min"]) &
    (df_fires["longitude"] <= LA_BOUNDS["lon_max"])
]

# Select relevant columns for fire events
df_fires = df_fires[["latitude", "longitude", "acq_time", "frp", "confidence"]]

df_fires = df_fires.sort_values(by="acq_time").reset_index(drop=True)
fire_events = df_fires.to_dict(orient="records")


# Initialize log
fire_log = []

if not df_fires.empty:
    plt.figure(figsize=(10, 6))

    # Use kdeplot with optimized settings
    sns.kdeplot(
        x=df_fires['longitude'], 
        y=df_fires['latitude'], 
        fill=True, 
        cmap='Reds', 
        bw_adjust=0.3,  # Adjust bandwidth for better density
        alpha=0.8
    )

    # Overlay actual fire locations
    plt.scatter(df_fires['longitude'], df_fires['latitude'], color='red', s=5, alpha=0.5)

    # Titles and labels
    plt.title("Heatmap of Fire Intensity in Los Angeles in 2018")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    # Save and display
    plt.savefig("fire_intensity_heatmap.png")
    plt.show()
else:
    print("No fire data available for heatmap.")
    
    # Ensure 'frp' is numeric
df_fires["frp"] = pd.to_numeric(df_fires["frp"], errors="coerce")

# Drop NaN values in 'frp' to avoid multiplication errors
df_fires = df_fires.dropna(subset=["frp"])

# Time-Lapse Animation of Fire Spread
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(LA_BOUNDS["lon_min"], LA_BOUNDS["lon_max"])
ax.set_ylim(LA_BOUNDS["lat_min"], LA_BOUNDS["lat_max"])
ax.set_title("Time-Lapse of Fire Spread in Los Angeles")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
scatter = ax.scatter([], [], c='red', alpha=0.6, edgecolors='black')

def update(frame):
    current_fires = df_fires[df_fires['acq_time'] <= frame]
    scatter.set_offsets(current_fires[['longitude', 'latitude']].values)
    scatter.set_sizes(current_fires['frp'] * 0.5)  # Scale fire sizes based on FRP
    return scatter,

ani = animation.FuncAnimation(fig, update, frames=range(int(df_fires['acq_time'].min()), int(df_fires['acq_time'].max()), 10), interval=100, blit=False)
ani.save("fire_spread_timelapse.gif", writer="pillow")
plt.show()

print("Time-lapse animation saved as 'fire_spread_timelapse.gif'")

import folium
from folium.plugins import HeatMap

# Define the center of the map (Los Angeles)
LA_CENTER = [34.0522, -118.2437]

# Create the base map
m = folium.Map(location=LA_CENTER, zoom_start=10, tiles="cartodbpositron")

# Ensure latitude and longitude are numeric
df_fires["latitude"] = pd.to_numeric(df_fires["latitude"], errors="coerce")
df_fires["longitude"] = pd.to_numeric(df_fires["longitude"], errors="coerce")
df_fires = df_fires.dropna(subset=["latitude", "longitude"])

# Convert data to list format for HeatMap
heat_data = df_fires[["latitude", "longitude"]].values.tolist()

# Add heatmap layer
HeatMap(heat_data, radius=15, blur=10).add_to(m)

# Save and display the map
map_filename = "la_fire_heatmap.html"
m.save(map_filename)
print(f"Heatmap saved as {map_filename}")



