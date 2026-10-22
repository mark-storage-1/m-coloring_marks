
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from urllib.request import urlopen
import shutil
import threading

import geopandas as gpd
import matplotlib

matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
# CONFIGURATION
# ============================================================

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "nvkelso/natural-earth-vector/master/"
    "geojson/ne_50m_admin_1_states_provinces.geojson"
)

DATA_DIR = Path.home() / ".mcoloring_data"
DATA_FILE = DATA_DIR / "admin1_states_provinces.geojson"

# Bright colors for a dark interface
PALETTE = [
    "#00FFFF",  # Aqua
    "#7FFF00",  # Chartreuse
    "#FF1493",  # Deep pink
    "#1E90FF",  # Dodger blue
    "#FF4500",  # Orange red
    "#ADFF2F",  # Green yellow
    "#BA55D3",  # Medium orchid
    "#40E0D0",  # Turquoise
    "#F0E68C",  # Khaki
    "#E6E6FA",  # Lavender
    "#FF6D00",  # Bright orange
    "#76FF03",  # Lime
]


# ============================================================
# DOWNLOAD AND LOAD GEOGRAPHIC DATA
# ============================================================

def download_dataset():
    """Download the geographic data if it is not already cached."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists() and DATA_FILE.stat().st_size > 1000:
        return

    temporary_file = DATA_FILE.with_suffix(".tmp")

    try:
        with urlopen(DATA_URL, timeout=90) as response:
            with open(temporary_file, "wb") as output:
                shutil.copyfileobj(response, output)

        if temporary_file.stat().st_size < 1000:
            raise ValueError("The downloaded map file is unexpectedly small.")

        temporary_file.replace(DATA_FILE)

    except Exception:
        temporary_file.unlink(missing_ok=True)
        raise


def load_dataset():
    """Load first-level administrative subdivisions."""

    download_dataset()

    data = gpd.read_file(DATA_FILE)

    required_columns = {"admin", "name", "geometry"}
    missing = required_columns - set(data.columns)

    if missing:
        raise ValueError(
            "The geographic dataset is missing these columns: "
            + ", ".join(sorted(missing))
        )

    data = data.dropna(subset=["admin", "name", "geometry"])
    data = data[
        (~data.geometry.is_empty)
        & data.geometry.is_valid
    ].copy()

    data["admin"] = data["admin"].astype(str).str.strip()
    data["name"] = data["name"].astype(str).str.strip()

    return data


# ============================================================
# BUILD THE ADJACENCY GRAPH
# ============================================================

def build_adjacency_graph(regions):
    """
    Each state/province is a vertex.

    An edge joins two regions if their polygons share
    a boundary of non-zero length.

    Merely touching at one point does not create an edge.
    """

    regions = regions.reset_index(drop=True)
    n = len(regions)

    adjacency = [set() for _ in range(n)]
    geometries = list(regions.geometry)

    for i in range(n):
        for j in range(i + 1, n):
            first = geometries[i]
            second = geometries[j]

            if not first.intersects(second):
                continue

            shared_boundary = (
                first.boundary.intersection(second.boundary)
            )

            # Coordinates are longitude/latitude degrees.
            # This tiny threshold filters point contacts and
            # insignificant numerical artifacts.
            if shared_boundary.length > 1e-7:
                adjacency[i].add(j)
                adjacency[j].add(i)

    return adjacency


# ============================================================
# BACKTRACKING GRAPH COLORING
# ============================================================

def select_vertex(adjacency, colors):
    """
    DSATUR-style selection:
    choose the uncolored vertex with the most distinct
    neighboring colors, then the highest degree.
    """

    best_vertex = -1
    best_score = (-1, -1)

    for v in range(len(adjacency)):
        if colors[v] != 0:
            continue

        neighbor_colors = {
            colors[u]
            for u in adjacency[v]
            if colors[u] != 0
        }

        score = (len(neighbor_colors), len(adjacency[v]))

        if score > best_score:
            best_score = score
            best_vertex = v

    return best_vertex


def greedy_coloring(adjacency):
    """Find a valid coloring to obtain an upper bound."""

    n = len(adjacency)
    colors = [0] * n

    for _ in range(n):
        v = select_vertex(adjacency, colors)

        if v == -1:
            break

        used = {
            colors[u]
            for u in adjacency[v]
            if colors[u] != 0
        }

        c = 1

        while c in used:
            c += 1

        colors[v] = c

    return colors, max(colors, default=0)


def can_color_with_k(adjacency, k):
    """Test whether the graph can be colored with k colors."""

    n = len(adjacency)
    colors = [0] * n

    def backtrack(colored_count):
        if colored_count == n:
            return True

        v = select_vertex(adjacency, colors)

        if v == -1:
            return True

        forbidden = {
            colors[u]
            for u in adjacency[v]
            if colors[u] != 0
        }

        for c in range(1, k + 1):
            if c in forbidden:
                continue

            colors[v] = c

            if backtrack(colored_count + 1):
                return True

            colors[v] = 0

        return False

    if n == 0:
        return True, []

    if backtrack(0):
        return True, colors

    return False, None


def find_chromatic_number(adjacency):
    """
    Search from one color up to a valid greedy upper bound.

    The first successful color count is the chromatic number,
    provided the exact search finishes.
    """

    if not adjacency:
        return 0, []

    _, upper_bound = greedy_coloring(adjacency)

    for k in range(1, upper_bound + 1):
        possible, coloring = can_color_with_k(adjacency, k)

        if possible:
            return k, coloring

    return upper_bound, greedy_coloring(adjacency)[0]


# ============================================================
# TKINTER APPLICATION
# ============================================================

class MapColoringApp:

    def __init__(self, root):
        self.root = root

        self.root.title(
            "State and Province Map Coloring - Backtracking"
        )
        self.root.geometry("1100x780")
        self.root.configure(bg="#1e1e1e")

        self.data = None
        self.map_canvas = None
        self.map_figure = None

        header = tk.Label(
            root,
            text="Geographic Map Coloring",
            font=("Arial", 21, "bold"),
            bg="#1e1e1e",
            fg="white"
        )
        header.pack(pady=(12, 4))

        subtitle = tk.Label(
            root,
            text=(
                "Select a country to color its states or provinces "
                "using backtracking."
            ),
            font=("Arial", 10),
            bg="#1e1e1e",
            fg="#cccccc"
        )
        subtitle.pack(pady=(0, 12))

        controls = tk.Frame(root, bg="#1e1e1e")
        controls.pack(pady=5)

        tk.Label(
            controls,
            text="Country:",
            font=("Arial", 11, "bold"),
            bg="#1e1e1e",
            fg="white"
        ).pack(side=tk.LEFT, padx=6)

        self.country_var = tk.StringVar()

        self.country_combo = ttk.Combobox(
            controls,
            textvariable=self.country_var,
            width=32,
            state="disabled"
        )
        self.country_combo.pack(side=tk.LEFT, padx=6)

        self.run_button = tk.Button(
            controls,
            text="Color Map",
            command=self.start_coloring,
            font=("Arial", 10, "bold"),
            bg="#00b894",
            fg="white",
            activebackground="#00a383",
            width=13,
            state="disabled"
        )
        self.run_button.pack(side=tk.LEFT, padx=6)

        self.status_var = tk.StringVar(
            value="Downloading geographic data..."
        )

        self.status_label = tk.Label(
            root,
            textvariable=self.status_var,
            font=("Arial", 10),
            bg="#1e1e1e",
            fg="#00FFFF",
            wraplength=1000
        )
        self.status_label.pack(pady=8)

        self.map_frame = tk.Frame(root, bg="#000000")
        self.map_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=12,
            pady=8
        )

        # Show the window before loading the data.
        self.root.update_idletasks()

        # Load in a background thread so the interface stays responsive.
        threading.Thread(
            target=self.load_data_worker,
            daemon=True
        ).start()

    def load_data_worker(self):
        try:
            data = load_dataset()

            countries = sorted(
                data["admin"].dropna().unique().tolist(),
                key=str.casefold
            )

            self.root.after(
                0,
                lambda: self.data_loaded(data, countries)
            )

        except Exception as exc:
            self.root.after(
                0,
                lambda error=str(exc): self.show_load_error(error)
            )

    def data_loaded(self, data, countries):
        self.data = data

        self.country_combo["values"] = countries
        self.country_combo.configure(state="readonly")

        self.run_button.configure(state="normal")

        # Choose India if available; otherwise choose the first country.
        preferred = next(
            (name for name in countries if name.casefold() == "india"),
            countries[0] if countries else ""
        )

        self.country_var.set(preferred)

        self.status_var.set(
            f"Loaded geographic data. {len(countries)} countries "
            "with available first-level subdivisions."
        )

    def show_load_error(self, error):
        self.status_var.set("Could not load the geographic data.")

        messagebox.showerror(
            "Data Loading Error",
            "Unable to download or read the geographic dataset.\n\n"
            "Check your internet connection and installed packages.\n\n"
            f"Details: {error}",
            parent=self.root
        )

    def start_coloring(self):
        country = self.country_var.get().strip()

        if not country or self.data is None:
            messagebox.showwarning(
                "Select a Country",
                "Please select a country first.",
                parent=self.root
            )
            return

        regions = self.data[
            self.data["admin"].str.casefold() == country.casefold()
        ].copy()

        regions = regions.reset_index(drop=True)

        if regions.empty:
            messagebox.showerror(
                "No Data",
                f"No subdivisions were found for {country}.",
                parent=self.root
            )
            return

        self.run_button.configure(state="disabled")
        self.country_combo.configure(state="disabled")

        self.status_var.set(
            f"Building the adjacency graph for {country}..."
        )
        self.root.update_idletasks()

        # The graph-building and exact coloring can take time.
        threading.Thread(
            target=self.compute_worker,
            args=(country, regions),
            daemon=True
        ).start()

    def compute_worker(self, country, regions):
        try:
            adjacency = build_adjacency_graph(regions)

            chromatic_number, colors = find_chromatic_number(
                adjacency
            )

            self.root.after(
                0,
                lambda: self.show_result(
                    country,
                    regions,
                    adjacency,
                    chromatic_number,
                    colors
                )
            )

        except Exception as exc:
            self.root.after(
                0,
                lambda error=str(exc): self.show_compute_error(error)
            )

    def show_compute_error(self, error):
        self.run_button.configure(state="normal")
        self.country_combo.configure(state="readonly")

        self.status_var.set("Could not color the selected map.")

        messagebox.showerror(
            "Coloring Error",
            error,
            parent=self.root
        )

    def show_result(
        self,
        country,
        regions,
        adjacency,
        chromatic_number,
        colors
    ):
        self.run_button.configure(state="normal")
        self.country_combo.configure(state="readonly")

        # Print the solution in the terminal.
        print("\n" + "=" * 45)
        print(f"Country: {country}")
        print(f"Number of states/provinces: {len(regions)}")
        print(f"Chromatic number: {chromatic_number}")
        print("-" * 45)

        for i, row in regions.iterrows():
            print(
                f"{row['name']}: Color {colors[i]}"
            )

        print("=" * 45)

        self.status_var.set(
            f"{country}: {len(regions)} subdivisions | "
            f"Chromatic number: {chromatic_number}"
        )

        self.draw_map(
            country,
            regions,
            adjacency,
            colors,
            chromatic_number
        )

    def draw_map(
        self,
        country,
        regions,
        adjacency,
        colors,
        chromatic_number
    ):
        # Remove the previous map.
        for widget in self.map_frame.winfo_children():
            widget.destroy()

        if self.map_figure is not None:
            plt.close(self.map_figure)

        self.map_figure, ax = plt.subplots(
            figsize=(11, 7),
            facecolor="#000000"
        )

        ax.set_facecolor("#000000")

        region_colors = [
            PALETTE[(color - 1) % len(PALETTE)]
            for color in colors
        ]

        # Draw real polygon shapes, not circles.
        regions.plot(
            ax=ax,
            color=region_colors,
            edgecolor="#E0E0E0",
            linewidth=0.65
        )

        ax.set_title(
            f"{country} - Chromatic Number: {chromatic_number}",
            color="white",
            fontsize=15,
            fontweight="bold",
            pad=12
        )

        ax.set_axis_off()

        # Labels can clutter large maps, so label smaller maps only.
        if len(regions) <= 35:
            for i, row in regions.iterrows():
                point = row.geometry.representative_point()

                ax.annotate(
                    f"{row['name']}\nC{colors[i]}",
                    (point.x, point.y),
                    color="#111111",
                    fontsize=6,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    bbox={
                        "facecolor": "white",
                        "alpha": 0.65,
                        "edgecolor": "none",
                        "pad": 1
                    }
                )

        self.map_figure.tight_layout()

        self.map_canvas = FigureCanvasTkAgg(
            self.map_figure,
            master=self.map_frame
        )

        self.map_canvas.draw()

        self.map_canvas.get_tk_widget().pack(
            fill=tk.BOTH,
            expand=True
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = MapColoringApp(root)
    root.mainloop()
