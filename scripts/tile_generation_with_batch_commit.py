import os
import math
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import subprocess

# --- SETTINGS ---
TILE_SIZE = 256
tiff_path = r"main\products\maps\PH\ph_rules_august_25.tif"
tiles_dir = r"main\html\agronomy_farms_soil_mapping\docs\page_files\maps\PH_auto\tiles"
legend_path = r"main\html\agronomy_farms_soil_mapping\docs\page_files\maps\PH_auto\legend.png"

commit_message = "Add/update generated PH tiles and legend"

# --- GIT HELPER ---
def git_commit_and_push(commit_message):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Changes committed and pushed to GitHub.")
    except subprocess.CalledProcessError as e:
        print("⚠️ Git command failed:", e)

# --- TILE HELPERS ---
WEBMERC_MIN = -20037508.342789244
WEBMERC_MAX = 20037508.342789244
WEBMERC_SIZE = WEBMERC_MAX - WEBMERC_MIN

def mercator_tile_bounds(x, y, z):
    n = 2 ** z
    tile_size = WEBMERC_SIZE / n
    minx = WEBMERC_MIN + x * tile_size
    maxx = WEBMERC_MIN + (x + 1) * tile_size
    maxy = WEBMERC_MAX - y * tile_size
    miny = WEBMERC_MAX - (y + 1) * tile_size
    return minx, miny, maxx, maxy

def get_tile_range(bounds, zoom):
    n = 2 ** zoom
    x_min = int((bounds.left - WEBMERC_MIN) / WEBMERC_SIZE * n)
    x_max = int((bounds.right - WEBMERC_MIN) / WEBMERC_SIZE * n)
    y_min = int((WEBMERC_MAX - bounds.top) / WEBMERC_SIZE * n)
    y_max = int((WEBMERC_MAX - bounds.bottom) / WEBMERC_SIZE * n)
    return x_min, x_max, y_min, y_max

# --- TILE GENERATION ---
cmap = plt.get_cmap("viridis")
zoom_levels = range(9, 19)

with rasterio.open(tiff_path) as src:
    bounds = src.bounds
    data = src.read(1, masked=True)
    data_min = data.min()

    for z in zoom_levels:
        x_min, x_max, y_min, y_max = get_tile_range(bounds, z)

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                minx, miny, maxx, maxy = mercator_tile_bounds(x, y, z)
                window = from_bounds(minx, miny, maxx, maxy, src.transform)

                tile_array = src.read(
                    1,
                    window=window,
                    out_shape=(TILE_SIZE, TILE_SIZE),
                    resampling=Resampling.bilinear
                )

                # Clip + normalize
                tile_array_clipped = np.clip(tile_array, None, 14)
                norm = (tile_array_clipped - data_min) / (14 - data_min)
                norm = np.clip(norm, 0, 1)
                rgba = (cmap(norm) * 255).astype(np.uint8)

                if src.nodata is not None:
                    mask = tile_array == src.nodata
                    rgba[mask] = [0, 0, 0, 0]
                rgba[tile_array <= 4] = [0, 0, 0, 0]

                img = Image.fromarray(rgba, mode="RGBA")

                # Save locally inside repo
                tile_path = os.path.join(tiles_dir, str(z), str(x))
                os.makedirs(tile_path, exist_ok=True)
                file_path = os.path.join(tile_path, f"{y}.png")
                img.save(file_path)

print("✅ Tiles saved locally")

# --- LEGEND GENERATION ---
fig, ax = plt.subplots(figsize=(2, 6))
fig.subplots_adjust(right=0.5)
norm = plt.Normalize(vmin=data_min, vmax=14)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

cbar = fig.colorbar(sm, cax=ax)
cbar.set_label('Soil pH', rotation=270, labelpad=15)

ticks = np.linspace(data_min, 14, 6)
cbar.set_ticks(ticks)
tick_labels = [str(int(t)) for t in ticks[:-1]] + [">14"]
cbar.set_ticklabels(tick_labels)

fig.savefig(legend_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"✅ Legend saved locally to {legend_path}")

# --- FINAL GIT PUSH ---
git_commit_and_push(commit_message)

