import os
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from github import Github, Auth
from matplotlib.colors import ListedColormap, BoundaryNorm
import json
import math



properties = ["PH", "BPH", "OM", "CEC"]

for PROPERTY in properties:
    #region GitHub Setup

    # Path to token
    token_file = r"secrets\map_token.txt"

    # Read token file
    with open(token_file, "r") as f:
        GITHUB_TOKEN = f.read().strip()


    GITHUB_REPO = "ajcecil/digital-soil-mapping"

    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(GITHUB_REPO)

    #endregion

    #region Function Building
    def upload_to_github(local_path, git_path, message="committing file"):
        """Upload or update file to GitHub repo"""
        try:
            contents = repo.get_contents(git_path)
            with open(local_path, "rb") as f:
                data = f.read()
            repo.update_file(contents.path, message, data, contents.sha, branch="main")
            print(f"{git_path} UPDATED on GitHub")
        except Exception:  # file does not exist yet
            with open(local_path, "rb") as f:
                data = f.read()
            repo.create_file(git_path, message, data, branch="main")
            print(f"{git_path} CREATED on GitHub")
    #endregion

    #region Tile Generation
    json_path = r"github\digital-soil-mapping\scripts\colormaps.json"

    with open(json_path, "r") as f:
        cmap_config = json.load(f)

    if PROPERTY not in cmap_config:
        raise ValueError(f"Property '{PROPERTY}' not found in colormaps.json")

    colors = cmap_config[PROPERTY]["colors"]
    legend_label = cmap_config[PROPERTY].get("label", PROPERTY)
    step = cmap_config[PROPERTY].get("step", PROPERTY)

    # Open raster to compute data stats
    tiff_path = fr"data\webpage\originals\{PROPERTY}_prediction.tif"
    with rasterio.open(tiff_path) as src:
        data = src.read(1, masked=True)

    # Compute mean and standard deviation
    data_mean = np.mean(data)
    data_std = np.std(data)

    # Generate 7 categories based on ±3 standard deviations
    bin_edges = [data_mean + i * data_std for i in range(math.ceil((-1)*step/2), math.ceil(step/2))]

    # Build discrete colormap + normalizer
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bin_edges, cmap.N)

    tiles_dir = fr"data\webpage\{PROPERTY}\tiles"

    TILE_SIZE = 256
    zoom_levels = range(9, 19)

    WEBMERC_MIN = -20037508.342789244
    WEBMERC_MAX = 20037508.342789244
    WEBMERC_SIZE = WEBMERC_MAX - WEBMERC_MIN

    # cmap = plt.get_cmap("inferno")

    # Build discrete colormap + normalizer
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bin_edges, cmap.N)


    def mercator_tile_bounds(x, y, z):
        n = 2 ** z
        tile_size = WEBMERC_SIZE / n

        minx = WEBMERC_MIN + x * tile_size
        maxx = minx + tile_size

        miny = WEBMERC_MAX - (y + 1) * tile_size
        maxy = WEBMERC_MAX - y * tile_size

        return minx, miny, maxx, maxy


    def get_tile_range(bounds, zoom):
        n = 2 ** zoom

        x_min = int((bounds.left - WEBMERC_MIN) / WEBMERC_SIZE * n)
        x_max = int((bounds.right - WEBMERC_MIN) / WEBMERC_SIZE * n)
        y_min = int((WEBMERC_MAX - bounds.top) / WEBMERC_SIZE * n)
        y_max = int((WEBMERC_MAX - bounds.bottom) / WEBMERC_SIZE * n)

        # ✅ CLAMP TO VALID XYZ RANGE
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(n - 1, x_max)
        y_max = min(n - 1, y_max)

        return x_min, x_max, y_min, y_max



    with rasterio.open(tiff_path) as src:
        bounds = src.bounds
        data = src.read(1, masked=True)
        data_min = data.min()
        data_max = data.max()

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
                    if np.all(tile_array == src.nodata):
                        continue

                    # Clip
                    tile_array_clipped = np.clip(tile_array, None, 335)

                    rgba = (cmap(norm(tile_array_clipped)) * 255).astype(np.uint8)

                    if src.nodata is not None:
                        mask = tile_array == src.nodata
                        rgba[mask] = [0, 0, 0, 0]
                    # rgba[tile_array <= 4] = [0, 0, 0, 0]

                    img = Image.fromarray(rgba, mode="RGBA")

                    # Save locally
                    tile_path = os.path.join(tiles_dir, str(z), str(x))
                    os.makedirs(tile_path, exist_ok=True)
                    file_path = os.path.join(tile_path, f"{y}.png")
                    img.save(file_path)

                    # Upload to GitHub
                    git_path = f"docs/page_files/maps/{PROPERTY}/tiles/{z}/{x}/{y}.png"
                    upload_to_github(file_path, git_path)

    print("Tile generation + GitHub upload complete!")
    #endregion


    #region Legend Build

    main_dir = rf'data\webpage\{PROPERTY}'
    legend_path = os.path.join(main_dir, "legend.png")

    fig, ax = plt.subplots(figsize=(2, 6))
    fig.subplots_adjust(right=0.5)
    norm = plt.Normalize(vmin=data_min, vmax=data_max)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    cbar = fig.colorbar(sm, cax=ax)
    cbar.set_label(legend_label, rotation=270, labelpad=15)

    ticks = np.linspace(data_min, data_max, (step + 1))
    cbar.set_ticks(ticks)
    tick_labels = [str(int(t)) for t in ticks]
    cbar.set_ticklabels(tick_labels)

    fig.savefig(legend_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Legend saved locally to {legend_path}")

    # Upload legend to GitHub
    upload_to_github(legend_path, f"docs/page_files/maps/{PROPERTY}/legend.png")

    #endregion