-- 004 — Crée la table `settings` (paramètres globaux du restaurant).
-- Reprise de la table Airtable « Settings_Cherimoya ».
--
-- Singleton : une seule ligne est attendue. La PK fixe (id=1) + le CHECK
-- forcent ce contrat au niveau base. Le code admin peut donc faire
-- `update().eq("id", 1)` sans gestion d'unicité applicative.

CREATE TABLE IF NOT EXISTS public.settings (
  id                      smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  total_seats             integer NOT NULL DEFAULT 50,
  max_reservations_per_day integer NOT NULL DEFAULT 100,
  lunch_start_time        text NOT NULL DEFAULT '12:00',
  lunch_end_time          text NOT NULL DEFAULT '14:00',
  dinner_start_time       text NOT NULL DEFAULT '19:00',
  dinner_end_time         text NOT NULL DEFAULT '22:00',
  closed_days             text[] NOT NULL DEFAULT '{}'::text[],  -- ex {"0","1"}
  min_advance_booking_hours integer NOT NULL DEFAULT 2,
  max_advance_booking_days  integer NOT NULL DEFAULT 90,
  updated_at              timestamptz NOT NULL DEFAULT now()
);

-- Seed la ligne unique si absente.
INSERT INTO public.settings (id) VALUES (1)
  ON CONFLICT (id) DO NOTHING;
