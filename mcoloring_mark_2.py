import math
import tkinter as tk
from tkinter import messagebox, simpledialog
import turtle


# --- Backtracking Algorithm for M-Coloring ---
def is_safe(v, graph, color, c):
    """Check if color c is safe for vertex v."""
    for i in range(len(graph)):
        if graph[v][i] == 1 and color[i] == c:
            return False
    return True


def graph_coloring_util(graph, m, color, v):
    """Solve graph coloring using backtracking."""
    if v == len(graph):
        return True

    for c in range(1, m + 1):
        if is_safe(v, graph, color, c):
            color[v] = c

            if graph_coloring_util(graph, m, color, v + 1):
                return True

            color[v] = 0  # Backtrack

    return False


def find_chromatic_number(graph):
    """Find the minimum number of colors required."""
    n = len(graph)

    if n == 0:
        return 0, []

    for m in range(1, n + 1):
        color = [0] * n

        if graph_coloring_util(graph, m, color, 0):
            return m, color

    return n, list(range(1, n + 1))


# --- User Input via Tkinter ---
def get_graph_input():
    root = tk.Tk()
    root.withdraw()

    try:
        # Accept 0 or any positive number of vertices
        n = simpledialog.askinteger(
            "Input",
            "Enter the number of vertices (0 or greater):",
            minvalue=0
        )

        if n is None:
            root.destroy()
            return None, None

        graph = [[0] * n for _ in range(n)]

        if n == 0:
            root.destroy()
            return n, graph

        messagebox.showinfo(
            "Instructions",
            f"Enter edges for a graph with {n} vertices "
            f"(indexed from 0 to {n - 1}).\n\n"
            "Enter each edge as u,v (e.g., 0,1).\n"
            "Leave blank or press Cancel when finished."
        )

        # Get edges
        while True:
            edge_input = simpledialog.askstring(
                "Add Edge",
                "Enter an edge as 'u,v' (e.g., 0,1).\n"
                "Leave blank or Cancel to finish."
            )

            if not edge_input:
                break

            try:
                u, v = map(int, edge_input.split(","))

                if 0 <= u < n and 0 <= v < n and u != v:
                    graph[u][v] = 1
                    graph[v][u] = 1
                else:
                    messagebox.showerror(
                        "Error",
                        f"Invalid edge! Enter vertices between 0 and {n - 1}, "
                        "and do not use self-loops."
                    )

            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Invalid format! Enter an edge as u,v (e.g., 0,1)."
                )

        root.destroy()
        return n, graph

    except Exception as e:
        root.destroy()
        messagebox.showerror("Error", str(e))
        return None, None


# --- Turtle Visualization ---
def draw_graph(n, graph, colors, chromatic_number):
    screen = turtle.Screen()
    screen.title("Graph Coloring & Chromatic Number Visualization")
    screen.bgcolor("black")

    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    # Color palette
    palette = [
        "red", "green", "blue", "yellow", "orange",
        "purple", "cyan", "magenta", "pink", "brown"
    ]

    # Calculate vertex positions in a circle
    radius = max(150, 20 * n)
    coords = []

    for i in range(n):
        angle = 2 * math.pi * i / n
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        coords.append((x, y))

    # Draw title
    t.penup()
    t.goto(0, radius + 70)
    t.color("black")
    t.write(
        f"Chromatic Number: {chromatic_number}",
        align="center",
        font=("Arial", 16, "bold")
    )

    # Draw edges
    t.pensize(2)

    for i in range(n):
        for j in range(i + 1, n):
            if graph[i][j] == 1:
                t.penup()
                t.goto(coords[i])
                t.pendown()
                t.color("gray")
                t.goto(coords[j])

    # Draw vertices with colored outlines and white labels
    for i in range(n):
        t.penup()
        t.goto(coords[i][0], coords[i][1] - 25)
        t.pendown()
    
        # Pick color based on solution (1-indexed to 0-indexed palette)
        color_idx = (colors[i] - 1) % len(palette)
        t.fillcolor(palette[color_idx])
        t.begin_fill()
        t.circle(25)
        t.end_fill()
    
        # Draw Vertex Label
        t.penup()
        t.goto(coords[i][0], coords[i][1] - 8)
        t.color("aqua")
        t.write(
            f"{i}",
            align="center",
            font=("Arial", 10, "bold"),
        )
    

    turtle.done()


# --- Main Execution ---
if __name__ == "__main__":
    n, graph = get_graph_input()

    if n is not None and graph is not None:
        if n == 0:
            print("Graph has 0 vertices.")
            print("Chromatic Number: 0")
            print("Vertex Colors: []")

        else:
            print(
                f"Finding chromatic number for graph with {n} vertices..."
            )

            chromatic_num, coloring = find_chromatic_number(graph)

            print(f"Chromatic Number: {chromatic_num}")
            print(f"Vertex Colors: {coloring}")

            draw_graph(n, graph, coloring, chromatic_num)
