import math
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
import turtle


# --- Backtracking Algorithm for M-Coloring ---
def is_safe(v, graph, color, c):
  """Check if color 'c' is safe for vertex 'v'."""
  for i in range(len(graph)):
    if graph[v][i] == 1 and color[i] == c:
      return False
  return True


def graph_coloring_util(graph, m, color, v):
  """Utility function to solve graph coloring using backtracking."""
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
  """Finds the chromatic number (minimum m required to color the graph)."""
  n = len(graph)
  for m in range(1, n + 1):
    color = [0] * n
    if graph_coloring_util(graph, m, color, 0):
      return m, color
  return n, [i + 1 for i in range(n)]


# --- User Input via Tkinter ---
def get_graph_input():
  root = tk.Tk()
  root.withdraw()  # Hide main tkinter window

  try:
    # Get number of vertices
    n = simpledialog.askinteger(
        "Input", "Enter the number of vertices (e.g., 4 to 8):", minvalue=1, maxvalue=15
    )
    if n is None:
      return None, None

    # Initialize adjacency matrix with 0
    graph = [[0] * n for _ in range(n)]

    messagebox.showinfo(
        "Instructions",
        f"You will now enter the edges for a graph with {n} vertices (indexed 0 to"
        f" {n-1}).",
    )

    # Get edges
    while True:
      edge_input = simpledialog.askstring(
          "Add Edge",
          "Enter an edge as 'u,v' (e.g., 0,1). Leave blank or cancel to finish.",
      )
      if not edge_input:
        break
      try:
        u, v = map(int, edge_input.split(","))
        if 0 <= u < n and 0 <= v < n and u != v:
          graph[u][v] = 1
          graph[v][u] = 1
        else:
          messagebox.showerror("Error", "Invalid vertex index or self-loop!")
      except ValueError:
        messagebox.showerror("Error", "Please enter in format u,v (e.g., 0,1)")

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

  # Color palette mapping
  palette = [
      "red",
      "green",
      "blue",
      "yellow",
      "orange",
      "purple",
      "cyan",
      "magenta",
      "pink",
      "brown",
  ]

  # Calculate vertex positions in a circle
  radius = 150
  coords = []
  for i in range(n):
    angle = 2 * math.pi * i / n
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    coords.append((x, y))

  # Draw Title & Info
  t.penup()
  t.goto(0, 220)
  t.color("black")
  t.write(
      f"Chromatic Number: {chromatic_number}",
      align="center",
      font=("Arial", 16, "bold"),
  )

  # Draw Edges
  t.pensize(2)
  for i in range(n):
    for j in range(i + 1, n):
      if graph[i][j] == 1:
        t.penup()
        t.goto(coords[i])
        t.pendown()
        t.color("gray")
        t.goto(coords[j])

  # Draw Vertices and Color Them
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
    t.color("black")
    t.write(
        f"{i}",
        align="center",
        font=("Arial", 10, "bold"),
    )

  # Keep window open
  turtle.done()


# --- Main Execution ---
if __name__ == "__main__":
  n, graph = get_graph_input()

  if n and graph:
    print(f"Finding chromatic number for graph with {n} vertices...")
    chromatic_num, coloring = find_chromatic_number(graph)
    print(f"Chromatic Number: {chromatic_num}")
    print(f"Vertex Colors: {coloring}")

    # Launch Turtle Visualization
    draw_graph(n, graph, coloring, chromatic_num)