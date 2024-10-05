# fourier_visualizer/core/fourier_transform.py

import numpy as np
import scipy.integrate as sc_integrate


def integrate(f, a, b):
    return sc_integrate.fixed_quad(f, a, b, n=1000)[0]


def compute_fourier_series(f, depth):
    term_data = []
    N = depth // 2  # Number of positive frequencies

    # Compute positive and negative frequencies
    # Ignore DC component (k=0) because it only adds a constant offset
    for k in range(1, N + 1):
        c_k = integrate(lambda t: f(t) * np.exp(-1j * 2 * np.pi * k * t), 0, 1)
        c_minus_k = integrate(lambda t: f(t) * np.exp(-1j * 2 * np.pi * -k * t), 0, 1)
        term_data.append({"k": k, "c": c_k})
        term_data.append({"k": -k, "c": c_minus_k})

    return term_data


def fourier_series_function(t, term_data):
    result = 0 + 0j
    for term in term_data:
        k = term["k"]
        c = term["c"]
        result += c * np.exp(1j * 2 * np.pi * k * t)
    return result
