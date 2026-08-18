"""Load SSVEP grid experiment .mat files into plain Python dicts."""

import scipy.io as sio


def load_ssvep(path: str) -> dict:
    """Load a MET*.mat file, dropping MATLAB header keys."""
    raw = sio.loadmat(path, struct_as_record=False, squeeze_me=True)
    return {k: v for k, v in raw.items() if not k.startswith("__")}


def to_rows(d: dict, filename: str) -> tuple[dict, list[dict], list[dict]]:
    """Convert one loaded .mat dict into (metadata_row, runmap_rows, baseline_rows).

    red_idx/green_idx are 0-based positions into redArray/greenArray. run/trial
    are 1-based.
    """
    sub_id, session = d["SubID"], int(d["session"])
    metadata_row = {"filename": filename, "sub_id": sub_id, "session": session, "group": d["group"], "subgroup": d["subgroup"]}

    n_red, n_green, n_runs = d["runMap"].shape
    runmap_rows = [
        {
            "sub_id": sub_id,
            "session": session,
            "run": run + 1,
            "red_idx": red_idx,
            "green_idx": green_idx,
            "value": d["runMap"][red_idx, green_idx, run],
        }
        for red_idx in range(n_red)
        for green_idx in range(n_green)
        for run in range(n_runs)
    ]

    n_trials, n_runs = d["baselines"].shape
    baseline_rows = [
        {"sub_id": sub_id, "session": session, "run": run + 1, "trial": trial + 1, "value": d["baselines"][trial, run]}
        for trial in range(n_trials)
        for run in range(n_runs)
    ]

    return metadata_row, runmap_rows, baseline_rows
