"""Side-by-side EEG heatmap and behavioral click-density map, for visually
comparing where each modality's response is concentrated.

Both panels share the physical (red, green) grid, [red_idx, green_idx]
orientation (see overlap.py's module docstring for the orientation bug this
project fixed relative to the template code) -- red on x, green on y,
matching every other heatmap in this repo.
"""

import matplotlib.pyplot as plt
import numpy as np

from overlap import DEFAULT_GREEN, DEFAULT_RED, behavioral_density_map

EEG_CMAP = "viridis"
DENSITY_CMAP = "Blues"


def _plot_grid(ax: plt.Axes, grid: np.ndarray, *, red: np.ndarray, green: np.ndarray, cmap: str, title: str) -> None:
    # grid is [red_idx, green_idx]; imshow needs [row, col] = [y, x], so
    # transpose and put the origin at the bottom to keep red on x, green on y.
    im = ax.imshow(grid.T, origin="lower", cmap=cmap, aspect="auto", extent=(red[0], red[-1], green[0], green[-1]))
    ax.set_xlabel("red")
    ax.set_ylabel("green")
    ax.set_title(title)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def plot_overlap(
    beh_df, eeg_grid: np.ndarray, sub_ids: list[str], *, red: np.ndarray = DEFAULT_RED, green: np.ndarray = DEFAULT_GREEN, title: str | None = None
) -> plt.Figure:
    """Two panels: the EEG response grid (eeg_grid, e.g. from
    analysis.mean_grid/mean_grid_across_subjects) and the behavioral
    click-density map for the same sub_ids (behavioral_density_map) --
    single participant (one-element sub_ids) or a pooled group."""
    B = behavioral_density_map(beh_df, sub_ids, red=red, green=green)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    _plot_grid(axes[0], eeg_grid, red=red, green=green, cmap=EEG_CMAP, title="EEG response")
    _plot_grid(axes[1], B, red=red, green=green, cmap=DENSITY_CMAP, title=f"Behavioral clicks (n={int(B.sum())})")
    fig.suptitle(title or f"{len(sub_ids)} subject(s)")
    fig.tight_layout()
    return fig
