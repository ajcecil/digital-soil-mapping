import os
import math
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# Input TIFF
tiff_path = r"main\products\maps\PH\ph_rules_august_25.tif"

# Output tiles folder
tiles_dir = r"main\html\tiles"

# Tile size
TILE_SIZE = 256

# Zoom levels
zoom_levels = range(9, 19)

# Web Mercator bounds
WEBMERC_MIN = -20037508.342789244
WEBMERC_MAX = 20037508.342789244
WEBMERC_SIZE = WEBMERC_MAX - WEBMERC_MIN

# Choose a matplotlib colormap
cmap = plt.get_cmap("RdBu")   # change to "viridis", "terrain", etc.

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

with rasterio.open(tiff_path) as src:
    bounds = src.bounds
    print(f"TIFF bounds: {bounds}")

    # Get global min/max values for normalization
    data = src.read(1, masked=True)
    data_min = data.min()
    data_max = data.max()
    print(f"Raster value range: {data_min} to {data_max}")

    for z in zoom_levels:
        x_min, x_max, y_min, y_max = get_tile_range(bounds, z)
        print(f"Zoom {z}: X {x_min}-{x_max}, Y {y_min}-{y_max}")

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                minx, miny, maxx, maxy = mercator_tile_bounds(x, y, z)

                # Correct window calculation
                window = from_bounds(minx, miny, maxx, maxy, src.transform)

                tile_array = src.read(
                    1,
                    window=window,
                    out_shape=(TILE_SIZE, TILE_SIZE),
                    resampling=Resampling.bilinear
                )

                # -----------------------------
                # Clip values at 14 and normalize
                tile_array_clipped = np.clip(tile_array, None, 14)
                norm = (tile_array_clipped - data_min) / (14 - data_min)
                norm = np.clip(norm, 0, 1)
                # -----------------------------

                # Apply colormap
                rgba = (cmap(norm) * 255).astype(np.uint8)

                # Make nodata or <=4 transparent
                if src.nodata is not None:
                    mask = tile_array == src.nodata
                    rgba[mask] = [0, 0, 0, 0]
                rgba[tile_array <= 4] = [0, 0, 0, 0]

                img = Image.fromarray(rgba, mode="RGBA")

                # Save
                tile_path = os.path.join(tiles_dir, str(z), str(x))
                os.makedirs(tile_path, exist_ok=True)
                img.save(os.path.join(tile_path, f"{y}.png"))

print("Tile generation complete with color mapping!")


# -----------------------------
# Generate legend PNG
# -----------------------------
main_dir = r'main\html'
legend_path = os.path.join(main_dir, "legend.png")
fig, ax = plt.subplots(figsize=(2, 6))
fig.subplots_adjust(right=0.5)

# Normalize 0 -> 14
norm = plt.Normalize(vmin=data_min, vmax=14)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

cbar = fig.colorbar(sm, cax=ax)
cbar.set_label('Soil pH', rotation=270, labelpad=15)

# Set ticks including >14
ticks = np.linspace(data_min, 14, 6)  # example: 0,3,6,9,12,14
cbar.set_ticks(ticks)
tick_labels = [str(int(t)) for t in ticks[:-1]] + [">14"]
cbar.set_ticklabels(tick_labels)

fig.savefig(legend_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"Legend saved to {legend_path}")