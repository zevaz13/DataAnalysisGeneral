"""Load the light meter (Gigahertz-Optik LIGHTmetric ONE) spectra.

Raw data: /home/sebas/data/LigthMeter_Filters/*.txt (read in place). Each file
has a metadata header, then a `wavelength / nm` / `spectral irradiance /
W/(m2 nm)` table, 360-830 nm. File names encode the condition:
`<stimulus>_<filter>.txt`, e.g. `blue2000_red2000_YF` = blue at 2000 plus red
at 2000, through the yellow filter. Filters: NF none, YF yellow, RF red.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path("/home/sebas/data/LigthMeter_Filters")


def load_spectra(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Long table: stimulus, filter, wavelength, irradiance."""
    frames = []
    for path in sorted(raw_dir.glob("*.txt")):
        stimulus, filt = path.stem.rsplit("_", 1)
        lines = path.read_text(encoding="latin-1").splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("wavelength")) + 1
        rows = [line.split("\t") for line in lines[start:] if line.strip()]
        df = pd.DataFrame(rows, columns=["wavelength", "irradiance"]).astype(float)
        frames.append(df.assign(stimulus=stimulus, filter=filt))
    return pd.concat(frames, ignore_index=True)[["stimulus", "filter", "wavelength", "irradiance"]]


STIM_FITTING_DIR = RAW_DIR / "stimFitting"


def load_traces(raw_dir: Path = STIM_FITTING_DIR) -> pd.DataFrame:
    """Long table: trace, wavelength, irradiance. Trace = file name (e.g. red1800Blue1350LO)."""
    frames = []
    for path in sorted(raw_dir.glob("*.txt")):
        lines = path.read_text(encoding="latin-1").splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("wavelength")) + 1
        rows = [line.split("\t") for line in lines[start:] if line.strip()]
        df = pd.DataFrame(rows, columns=["wavelength", "irradiance"]).astype(float)
        frames.append(df.assign(trace=path.stem))
    return pd.concat(frames, ignore_index=True)[["trace", "wavelength", "irradiance"]]
