import pandas as pd
import streamlit as st

from src.db import fetch_jobs, fetch_job_by_id

st.set_page_config(page_title="Jobs", layout="wide")
st.title("Jobs")

# Load from DB
limit = st.slider("How many jobs to load?", min_value=25, max_value=2000, value=500, step=25)
rows = fetch_jobs(limit=limit, keyword=None)

if not rows:
    st.info("No jobs found yet. Go to the Ingest page and fetch some jobs.")
    st.stop()

df = pd.DataFrame(rows)

df["posted_at_dt"] = pd.to_datetime(df["posted_at"], errors="coerce", utc=True)
df["posted_date"] = df["posted_at_dt"].dt.date

# ---- FILTERS  ----
st.sidebar.header("Filters")

# Date range
min_date = df["posted_date"].min()
max_date = df["posted_date"].max()

date_range = None
if pd.isna(min_date) or pd.isna(max_date):
    st.sidebar.warning("No valid posted_at dates found.")
else:
    date_range = st.sidebar.date_input(
        "Posted date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

# Position / Title
title_query = st.sidebar.text_input("Position / Title contains", value="")

# Company
companies = sorted([c for c in df["company"].dropna().unique().tolist() if str(c).strip()])
selected_companies = st.sidebar.multiselect("Company", options=companies, default=[])

# Location
locations = sorted([l for l in df["location"].dropna().unique().tolist() if str(l).strip()])
selected_locations = st.sidebar.multiselect("Location", options=locations, default=[])

remote_only = st.sidebar.checkbox("Remote only", value=False)
keyword = st.sidebar.text_input("Keyword (title/company/description)", value="")


# ---- APPLY FILTERS ----
filtered = df.copy()

# Date range filter
if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[(filtered["posted_date"] >= start_date) & (filtered["posted_date"] <= end_date)]

# Title contains
if title_query.strip():
    filtered = filtered[filtered["title"].fillna("").str.contains(title_query.strip(), case=False, na=False)]

# Company filter
if selected_companies:
    filtered = filtered[filtered["company"].isin(selected_companies)]

# Location filter
if selected_locations:
    filtered = filtered[filtered["location"].isin(selected_locations)]

# Remote only
if remote_only:
    filtered = filtered[filtered["is_remote"] == True]

# Keyword across fields
if keyword.strip():
    kw = keyword.strip().lower()
    filtered = filtered[
        filtered["title"].fillna("").str.lower().str.contains(kw, na=False)
        | filtered["company"].fillna("").str.lower().str.contains(kw, na=False)
        | filtered["description"].fillna("").str.lower().str.contains(kw, na=False)
    ]

st.subheader(f"Results: {len(filtered)} jobs")

# Display with date-only column
display_cols = ["id", "company", "title", "location", "is_remote", "posted_date", "apply_url"]
filtered_display = filtered[display_cols].sort_values(by=["posted_date"], ascending=False)

st.dataframe(filtered_display, use_container_width=True, hide_index=True)

st.divider()
st.subheader("View job details")

job_ids = filtered_display["id"].astype(str).tolist()
if not job_ids:
    st.info("No jobs match the current filters.")
    st.stop()

selected = st.selectbox("Select a job", options=job_ids, index=0)
job = fetch_job_by_id(selected)

if job:
    st.markdown(f"### {job.get('title','')}")
    st.write(f"**Company:** {job.get('company','')}")
    st.write(f"**Location:** {job.get('location','')}")
    st.write(f"**Remote:** {job.get('is_remote')}")

    posted_at = job.get("posted_at")
    posted_date = pd.to_datetime(posted_at, errors="coerce", utc=True).date() if posted_at else None
    st.write(f"**Posted date:** {posted_date}")

    apply_url = job.get("apply_url") or ""
    if apply_url:
        st.link_button("Open Apply Page", apply_url)

    st.markdown("#### Description")
    st.markdown(job.get("description") or "", unsafe_allow_html=True)
