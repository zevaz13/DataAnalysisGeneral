Light meter spectra through colored filters. Data:
`/home/sebas/data/LigthMeter_Filters/` (9 txt files, read in place). Code
under `/light_meter`.

## Data

LIGHTmetric ONE export: metadata header, then spectral irradiance
(W/(m2 nm)), 360-830 nm at 1 nm. File name = `<stimulus>_<filter>.txt`.

- Stimuli: `blue2000`, `blue2000_red2000`, `blue2000_yellow2000` (LED
  intensities)
- Filters: NF none, YF yellow, RF red (meant to attenuate blue differently)

## M1. Load and compare

- [x] `scripts/loader.py` (`load_spectra`, long table) and
  `scripts/plotting.py`
- [x] `notebooks/01_compare.ipynb`: same filter with all stimuli (panel per
  filter), and same stimulus across filters (panel per stimulus)
- [ ] Decide what to quantify (e.g. blue-band transmission per filter)
- [ ] Decide on intermediate data handling (none so far)

## Next milestones

To be defined together.
