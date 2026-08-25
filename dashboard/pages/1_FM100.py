import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import streamlit as st

from _pagesetup import use_scripts

mods = use_scripts("standardizedScores/FM100/scripts", "loader", "scores", "plotting", "comparisons")
loader, plotting, comparisons = mods["loader"], mods["plotting"], mods["comparisons"]

st.set_page_config(page_title="FM100", page_icon="🎨")
st.title("FM100")

CATEGORY_OPTIONS = {
    "HC": {"group": "CTR"},
    "PD": {"group": "PD"},
    "CVD": {"group": "CVD"},
    "protan": {"subgroup": "protan"},
    "deutan": {"subgroup": "deutan"},
}


@st.cache_data
def load_data():
    return loader.load_fm100_raw()


df = load_data()

st.sidebar.header("Groups")
selected_labels = st.sidebar.multiselect("Categories", list(CATEGORY_OPTIONS), default=["HC", "protan", "deutan"])
categories = [{"label": label, **CATEGORY_OPTIONS[label]} for label in selected_labels]

kind = st.sidebar.radio("Plot style", ["linear", "radial"], index=0)
window = st.sidebar.slider("Smoothing window", 1, 9, 1, step=2)

st.sidebar.header("Single subject (optional)")
subject = st.sidebar.selectbox("Subject", ["(none)"] + sorted(df["sub_id"].unique()))

st.subheader("Group error profiles")
if categories:
    ax = plotting.plot_group_fm100(df, categories, kind=kind, window=window)
    st.pyplot(ax.figure)
    plt.close(ax.figure)
else:
    st.info("Select at least one category in the sidebar.")

if subject != "(none)":
    st.subheader(f"{subject}'s own profile")
    ax = plotting.plot_subject_fm100(df, subject, kind=kind, window=window)
    st.pyplot(ax.figure)
    plt.close(ax.figure)

st.subheader("Pairwise comparisons")
feature = st.selectbox("Feature", comparisons.FEATURES, index=0)
if len(categories) >= 2:
    rows = []
    for cat1, cat2 in itertools.combinations(categories, 2):
        result = comparisons.compare_fm100_feature(
            df,
            feature,
            group1=cat1.get("group"),
            subgroup1=cat1.get("subgroup"),
            group2=cat2.get("group"),
            subgroup2=cat2.get("subgroup"),
        )
        rows.append(
            {
                "pair": f"{cat1['label']} vs {cat2['label']}",
                "p_value": round(result["p_value"], 4),
                "n1": result["n1"],
                "n2": result["n2"],
            }
        )
    st.table(rows)
else:
    st.info("Select at least two categories to compare.")
