import streamlit as st

from src.greenhouse import extract_board_slug, fetch_greenhouse_jobs
from src.db import upsert_jobs

st.set_page_config(page_title="Ingest", layout="wide")
st.title("Ingest jobs from Greenhouse")

st.write("Enter a Greenhouse **board slug** (e.g., `stripe`) or a Greenhouse board URL.")

board_or_url = st.text_input("Board slug or URL", value="stripe")

col1, col2 = st.columns([1, 2])

with col1:
    do_ingest = st.button("Fetch + Upsert", type="primary")

if do_ingest:
    try:
        board = extract_board_slug(board_or_url)
        st.info(f"Using board: `{board}`")

        with st.spinner("Fetching jobs from Greenhouse..."):
            jobs = fetch_greenhouse_jobs(board)

        st.success(f"Fetched {len(jobs)} jobs from Greenhouse.")

        with st.spinner("Upserting into Postgres..."):
            n = upsert_jobs(jobs)

        st.success(f"Upserted {n} records into Postgres (insert/update).")

        if jobs:
            st.subheader("Preview (first 10)")
            st.dataframe(
                [{k: j.get(k) for k in ["company", "title", "location", "posted_at", "apply_url"]} for j in jobs[:10]],
                use_container_width=True,
            )

    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()
