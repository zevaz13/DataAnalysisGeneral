import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import streamlit as st

from _pagesetup import use_scripts

mods = use_scripts("ssveps/scripts", "analysis", "permutation", "plotting")
analysis, permutation, plotting = mods["analysis"], mods["permutation"], mods["plotting"]

st.set_page_config(page_title="SSVEP", page_icon="🎨")
st.title("SSVEP (EEG grid response)")

SESSION = 1  # every subject has a session-1 row (matches every ssveps/ notebook)

CATEGORY_OPTIONS = {
    "HC": {"group": "CTR"},
    "PD": {"group": "PD"},
    "CVD": {"group": "CVD"},
    "protan": {"subgroup": "protan"},
    "deutan": {"subgroup": "deutan"},
}
NORMALIZE_OPTIONS = {
    "percent change (default)": analysis.DEFAULT_NORMALIZE,
    "db": {"scope": "run", "trials": "all", "method": "db"},
    "raw": None,
}


@st.cache_data
def load_data():
    return analysis.load_runmap(), analysis.load_baselines(), analysis.load_metadata()


runmap_df, baselines_df, metadata_df = load_data()

st.sidebar.header("Groups (up to 3)")
selected_labels = st.sidebar.multiselect(
    "Categories", list(CATEGORY_OPTIONS), default=["HC", "protan", "deutan"], max_selections=3
)
categories = [{"label": label, **CATEGORY_OPTIONS[label]} for label in selected_labels]

normalize_label = st.sidebar.radio("Normalization", list(NORMALIZE_OPTIONS), index=0)
normalize = NORMALIZE_OPTIONS[normalize_label]

st.sidebar.header("Significance test")
n_perm = st.sidebar.slider("Permutations", 100, 1000, 300, step=100)

st.subheader("Mean response grids")
if categories:
    fig = plotting.plot_groups_side_by_side(runmap_df, baselines_df, metadata_df, SESSION, categories, normalize=normalize)
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("Select at least one category in the sidebar.")

st.subheader("Individual subjects")
subject_category = st.selectbox("Category to break down by subject", ["(none)"] + selected_labels)
if subject_category != "(none)":
    cat = {"label": subject_category, **CATEGORY_OPTIONS[subject_category]}
    fig = plotting.plot_subjects_side_by_side(
        runmap_df, baselines_df, metadata_df, SESSION, group=cat.get("group"), subgroup=cat.get("subgroup"), normalize=normalize
    )
    st.pyplot(fig)
    plt.close(fig)


@st.cache_data(show_spinner="Running permutation test...")
def run_permutation(_runmap_df, _baselines_df, _metadata_df, session, group1, subgroup1, group2, subgroup2, normalize, n_perm):
    return permutation.permutation_test_weighted(
        _runmap_df,
        _baselines_df,
        _metadata_df,
        session,
        group1=group1,
        subgroup1=subgroup1,
        group2=group2,
        subgroup2=subgroup2,
        normalize=normalize,
        n_perm=n_perm,
        seed=0,
    )


st.subheader("Pairwise cluster-permutation significance")
st.caption("Cluster-weight-corrected two-tailed permutation test (Maris & Oostenveld style) between each pair's mean grid.")
if len(categories) >= 2:
    rows = []
    for cat1, cat2 in itertools.combinations(categories, 2):
        result = run_permutation(
            runmap_df,
            baselines_df,
            metadata_df,
            SESSION,
            cat1.get("group"),
            cat1.get("subgroup"),
            cat2.get("group"),
            cat2.get("subgroup"),
            normalize,
            n_perm,
        )
        cluster_pvals = [c["pvalue"] for c in result["cluster_results"]]
        min_p = round(min(cluster_pvals), 4) if cluster_pvals else None
        rows.append(
            {
                "pair": f"{cat1['label']} vs {cat2['label']}",
                "min cluster p_value": min_p if min_p is not None else "no significant cluster",
                "n1": result["n1"],
                "n2": result["n2"],
            }
        )
    st.table(rows)
else:
    st.info("Select at least two categories to compare.")
