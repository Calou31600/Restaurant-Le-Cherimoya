-- 003 — Crée la table `commandes` (tablette salle, écran cuisine, facturation).
-- Reprise de la table Airtable « Commandes » utilisée par app.py:634-811 et
-- les pages order.html / kitchen.html / facturation.html.
--
-- Champ `items` : stocké en JSONB (la version Airtable utilisait du JSON
-- sérialisé dans un champ texte). On garde le typage natif, le code Python
-- saura sérialiser/désérialiser via le SDK Supabase.

CREATE TABLE IF NOT EXISTS public.commandes (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ref           text,                                          -- "Table 5 - 19:42"
  table_n       integer NOT NULL,
  items         jsonb NOT NULL DEFAULT '[]'::jsonb,
  total         numeric(10,2) NOT NULL DEFAULT 0,
  statut        text NOT NULL DEFAULT 'En attente'
                CHECK (statut IN ('En attente','En cuisine','Prêt','Servi','Payé','Annulé')),
  heure         timestamptz NOT NULL DEFAULT now(),
  service       text CHECK (service IN ('Midi','Soir')),
  notes         text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS commandes_statut_idx   ON public.commandes (statut);
CREATE INDEX IF NOT EXISTS commandes_table_n_idx  ON public.commandes (table_n);
CREATE INDEX IF NOT EXISTS commandes_heure_idx    ON public.commandes (heure DESC);
