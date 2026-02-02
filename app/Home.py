import streamlit as st

st.set_page_config(page_title="Job Intel", layout="wide")

st.title("Job Intel (Greenhouse → Postgres → Streamlit)")
st.markdown("""
This app ingests public job postings from **Greenhouse job boards** and stores them in **Postgres**.

Use the **Ingest** page to fetch jobs, then browse them in **Jobs**.
""")
