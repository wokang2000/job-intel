import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

import requests

GREENHOUSE_LIST_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
# If you want per-job detail later:
# GREENHOUSE_DETAIL_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"

SKIP_HOSTS = {"boards-api.greenhouse.io"}  # For pasting URL

def extract_board_slug(board_or_url: str) -> str:
    """
    Accepts:
      - "stripe"
      - "https://boards.greenhouse.io/stripe"
      - "https://boards.greenhouse.io/embed/job_board?for=stripe"
      - "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"
    Returns: "stripe"
    """
    s = board_or_url.strip()

    if re.fullmatch(r"[a-z0-9][a-z0-9\-_]{1,80}", s, flags=re.I):
        return s.lower()

    try:
        u = urlparse(s)
        host = (u.hostname or "").lower()
        # 1) embed style: ?for=board
        qs = parse_qs(u.query)
        if "for" in qs and qs["for"]:
            return qs["for"][0].strip().lower()
        # 2) boards-api URL: /v1/boards/<board>/jobs
        parts = [p for p in u.path.split("/") if p]
        if host in SKIP_HOSTS and "boards" in parts:
            i = parts.index("boards")
            if i + 1 < len(parts):
                return parts[i + 1].strip().lower()
        # 3) boards.greenhouse.io/<board> or similar: take first path segment
        if parts:
            return parts[0].strip().lower()
    except Exception:
        pass
    raise ValueError("Could not extract a Greenhouse board slug from input.")

def fetch_greenhouse_jobs(board: str, timeout: int = 20) -> List[Dict[str, Any]]:
    """
    Fetches jobs from Greenhouse 'boards-api' endpoint.
    Using content=true returns HTML content in the response (useful for job description).
    """
    url = GREENHOUSE_LIST_URL.format(board=board)
    resp = requests.get(url, params={"content": "true"}, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    jobs = []
    for j in data.get("jobs", []):
        # Some Greenhouse responses have location dict
        loc = ""
        if isinstance(j.get("location"), dict):
            loc = j["location"].get("name", "") or ""
        else:
            loc = j.get("location", "") or ""

        title = j.get("title") or ""
        company = j.get("company_name") or board  # company_name may not exist; fallback to board

        # Very rough remote flag (Will improve later on)
        loc_lower = (loc or "").lower()
        is_remote = any(x in loc_lower for x in ["remote", "work from home", "wfh"])

        job = {
            "source": "greenhouse",
            "source_job_id": str(j.get("id")),
            "company": company,
            "title": title,
            "location": loc,
            "is_remote": is_remote,
            "posted_at": j.get("updated_at") or j.get("created_at"),
            "apply_url": j.get("absolute_url") or "",
            "description": j.get("content") or "",  # HTML
            "raw_json": j,
        }
        # Only keep if has an id (needed for upsert key)
        if job["source_job_id"] and job["source_job_id"] != "None":
            jobs.append(job)

    return jobs
