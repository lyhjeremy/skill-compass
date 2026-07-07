-- SkillCompass Phase 2 schema. Paste into Supabase → SQL Editor → Run (one time).
-- Only the backend (service_role key) touches these; no personal data is stored.

create table if not exists sessions (
  id            bigserial primary key,
  session_hash  text not null,
  subtopic      text not null,
  variant       text,
  score         int  not null,
  total         int  not null,
  final_rating  real not null,
  created_at    timestamptz not null default now()
);
create index if not exists sessions_subtopic_time on sessions (subtopic, created_at);

create table if not exists responses (
  id             bigserial primary key,
  session_hash   text not null,
  item_id        text not null,
  subtopic       text,
  concept        text,
  correct        boolean not null,
  response_ms    int,
  first_exposure boolean default true,
  created_at     timestamptz not null default now()
);
create index if not exists responses_item on responses (item_id);

create table if not exists feedback (
  id          bigserial primary key,
  kind        text not null,          -- 'general' | 'item_report'
  item_id     text,
  body        text,
  created_at  timestamptz not null default now()
);

-- Belt-and-suspenders: enable RLS so the anon key can never read these tables.
-- The backend uses the service_role key, which bypasses RLS.
alter table sessions  enable row level security;
alter table responses enable row level security;
alter table feedback  enable row level security;
