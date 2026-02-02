create extension if not exists "uuid-ossp";

create table if not exists jobs (
  id uuid primary key default uuid_generate_v4(),
  source text not null,
  source_job_id text not null,
  company text,
  title text,
  location text,
  is_remote boolean default false,
  posted_at timestamptz,
  apply_url text,
  description text,
  raw_json jsonb,
  inserted_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (source, source_job_id)
);

create index if not exists idx_jobs_posted_at on jobs (posted_at desc);
create index if not exists idx_jobs_company on jobs (company);
create index if not exists idx_jobs_title on jobs (title);