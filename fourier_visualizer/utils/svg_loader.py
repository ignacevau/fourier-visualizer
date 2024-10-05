import numpy as np
from svgpathtools import svg2paths


def load_svg(svg_path):
    paths, _ = svg2paths(svg_path)
    if not paths:
        raise ValueError("No paths found in SVG file.")
    path = paths[0]  # Assuming the first path
    f = np.vectorize(path.point)
    return f
