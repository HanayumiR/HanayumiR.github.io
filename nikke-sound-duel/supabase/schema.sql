-- One anonymous vote per Apple Music track ID and browser-generated UUID.
-- Direct table access stays closed; clients call only the two RPC functions.
create table if not exists public.sound_duel_votes (
  track_id text not null check (track_id ~ '^[0-9]{1,24}$'),
  voter_id uuid not null,
  created_at timestamptz not null default now(),
  primary key (track_id, voter_id)
);

alter table public.sound_duel_votes enable row level security;
revoke all on table public.sound_duel_votes from anon, authenticated;

create or replace function public.get_sound_duel_rankings()
returns table(track_id text, vote_count bigint)
language sql
stable
security definer
set search_path = ''
as $$
  select vote.track_id, count(*)::bigint
  from public.sound_duel_votes as vote
  group by vote.track_id;
$$;

create or replace function public.cast_sound_duel_vote(p_track_id text, p_voter_id uuid)
returns table(accepted boolean, vote_count bigint)
language plpgsql
security definer
set search_path = ''
as $$
declare
  inserted_count integer;
begin
  if p_track_id is null or p_track_id !~ '^[0-9]{1,24}$' or p_voter_id is null then
    raise exception 'Invalid vote.';
  end if;

  insert into public.sound_duel_votes (track_id, voter_id)
  values (p_track_id, p_voter_id)
  on conflict (track_id, voter_id) do nothing;

  get diagnostics inserted_count = row_count;

  return query
    select inserted_count = 1, count(*)::bigint
    from public.sound_duel_votes as vote
    where vote.track_id = p_track_id;
end;
$$;

revoke all on function public.get_sound_duel_rankings() from public, anon, authenticated;
revoke all on function public.cast_sound_duel_vote(text, uuid) from public, anon, authenticated;
grant execute on function public.get_sound_duel_rankings() to anon, authenticated;
grant execute on function public.cast_sound_duel_vote(text, uuid) to anon, authenticated;
