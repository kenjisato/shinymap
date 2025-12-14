from shinymap import QUALITATIVE

DEMO_GEOMETRY = {
    "circle": ["M25,50 A20,20 0 1 1 24.999,50 Z"],
    "square": ["M10 10 H40 V40 H10 Z"],
    "triangle": ["M75 70 L90 40 L60 40 Z"],
}

TOOLTIPS = {"circle": "Circle", "square": "Square", "triangle": "Triangle"}
SHAPE_COLORS = {"circle": QUALITATIVE[0], "square": QUALITATIVE[1], "triangle": QUALITATIVE[2]}

