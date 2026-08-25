import streamlit as st

st.set_page_config(page_title="CVD study dashboard", page_icon="🎨")

st.title("CVD study dashboard")
st.write("Interactive views over the color-vision-deficiency analysis in this repo. Pick a page from the sidebar:")
st.markdown(
    "- **FM100** -- the clinical hue-ordering test\n"
    "- **Behavioral** -- the manual red/green match task\n"
    "- **SSVEP** -- the EEG grid response\n"
)
st.write(
    "Each page reuses the same `loader`/`plotting`/`comparisons` functions "
    "as the corresponding notebook -- nothing here recomputes anything, "
    "it's a thin interactive layer over `beh/`, `ssveps/`, and "
    "`standardizedScores/FM100/`. See `docs/findings.md` for the narrative "
    "behind these results."
)
