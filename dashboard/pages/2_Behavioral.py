import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import streamlit as st

from _pagesetup import use_scripts

mods = use_scripts("beh/scripts", "loader", "features", "comparisons", "plotting")
loader, features, comparisons, plotting = mods["loader"], mods["features"], mods["comparisons"], mods["plotting"]

st.set_page_config(page_title="Behavioral", page_icon="🎨")
st.title("Behavioral (manual match)")

CATEGORY_OPTIONS = {
    "HC": {"group": "CTR"},
    "PD": {"group": "PD"},
    "CVD": {"group": "CVD"},
    "protan": {"subgroup": "protan"},
    "deutan": {"subgroup": "deutan"},
}
SHAPE_FEATURES = ["orientation_deg", "along_var", "perp_var"]


@st.cache_data
def load_data():
    return loader.load_behavioral()


df = load_data()

st.sidebar.header("Groups (up to 3)")
selected_labels = st.sidebar.multiselect(
    "Categories", list(CATEGORY_OPTIONS), default=["HC", "protan", "deutan"], max_selections=3
)
categories = [{"label": label, **CATEGORY_OPTIONS[label]} for label in selected_labels]

x_feature = st.sidebar.selectbox("Shape feature (x-axis)", SHAPE_FEATURES, index=0)
y_feature = st.sidebar.selectbox("Shape feature (y-axis)", SHAPE_FEATURES, index=2)

st.sidebar.header("Single subject (optional)")
subject = st.sidebar.selectbox("Subject", ["(none)"] + sorted(df["sub_id"].unique()))

st.subheader("Shape-feature space (PCA line per subject)")
if categories:
    ax = plotting.plot_feature_space(df, categories, x_feature=x_feature, y_feature=y_feature)
    st.pyplot(ax.figure)
    plt.close(ax.figure)
else:
    st.info("Select at least one category in the sidebar.")

st.subheader("Raw click clouds")
if categories:
    fig = plotting.plot_groups_side_by_side(df, categories)
    st.pyplot(fig)
    plt.close(fig)

if subject != "(none)":
    st.subheader(f"{subject}'s click cloud, with fitted PCA line")
    ax = plotting.plot_subject_cloud(df, subject, show_fit=True)
    st.pyplot(ax.figure)
    plt.close(ax.figure)

st.subheader("Pairwise comparisons")
if len(categories) >= 2:
    location_rows, shape_rows = [], []
    for cat1, cat2 in itertools.combinations(categories, 2):
        pair_label = f"{cat1['label']} vs {cat2['label']}"
        location = comparisons.compare_groups(
            df,
            group1=cat1.get("group"),
            subgroup1=cat1.get("subgroup"),
            group2=cat2.get("group"),
            subgroup2=cat2.get("subgroup"),
        )
        location_rows.append({"pair": pair_label, "p_value": round(location["p_value"], 4), "n1": location["n1"], "n2": location["n2"]})
        shape = features.compare_shape_feature(
            df,
            x_feature,
            group1=cat1.get("group"),
            subgroup1=cat1.get("subgroup"),
            group2=cat2.get("group"),
            subgroup2=cat2.get("subgroup"),
        )
        shape_rows.append({"pair": pair_label, "p_value": round(shape["p_value"], 4), "n1": shape["n1"], "n2": shape["n2"]})

    st.write("Click location (Hotelling T²)")
    st.table(location_rows)
    st.write(f"{x_feature} (Mann-Whitney U)")
    st.table(shape_rows)
else:
    st.info("Select at least two categories to compare.")
