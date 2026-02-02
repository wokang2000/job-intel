import os
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from psycopg.types.json import Json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it in .env")

UPSERT_SQL = """
insert into jobs (
  source, source_job_id, company, title, location, is_remote,
  posted_at, apply_url, description, raw_json, updated_at
)
values (
  %(source)s, %(source_job_id)s, %(company)s, %(title)s, %(location)s, %(is_remote)s,
  %(posted_at)s, %(apply_url)s, %(description)s, %(raw_json)s, now()
)
on conflict (source, source_job_id)
do update set
  company = excluded.company,
  title = excluded.title,
  location = excluded.location,
  is_remote = excluded.is_remote,
  posted_at = excluded.posted_at,
  apply_url = excluded.apply_url,
  description = excluded.description,
  raw_json = excluded.raw_json,
  updated_at = now();
"""

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def upsert_jobs(jobs: List[Dict[str, Any]]) -> int:
    """Upsert job records. Returns number of rows attempted (len(jobs))."""
    if not jobs:
        return 0

    # Convert Python dict -> JSON wrapper psycopg can adapt to jsonb
    for j in jobs:
        if isinstance(j.get("raw_json"), dict):
            j["raw_json"] = Json(j["raw_json"])

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, jobs)

    return len(jobs)

def fetch_jobs(limit: int = 200, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = """
    select
      id, source, source_job_id, company, title, location, is_remote,
      posted_at, apply_url, description, updated_at
    from jobs
    """
    params = {}
    if keyword:
        sql += " where (title ilike %(kw)s or company ilike %(kw)s or description ilike %(kw)s)"
        params["kw"] = f"%{keyword}%"
    sql += " order by posted_at desc nulls last, updated_at desc limit %(limit)s"
    params["limit"] = limit

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def fetch_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    select *
    from jobs
    where id = %(id)s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"id": job_id})
            row = cur.fetchone()
            return row
