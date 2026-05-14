-- 002 — Crée la table `clients` (CRM Chérimoya).
-- Reprise de la structure Airtable « Clients » + des champs consommés par la
-- fiche admin (dashboard.html `fetchClients` / cartes CRM).
--
-- Champs additionnels notés "à compléter plus tard" par l'utilisateur :
--   - note         : rating 0..5 affiché dans la fiche admin
--   - avis_recu    : booléen (avis Google reçu ou non)
-- Ils sont créés ici pour cohérence ; le code ne les écrira pas tant qu'ils ne
-- sont pas branchés côté formulaire.

CREATE TABLE IF NOT EXISTS public.clients (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nom                  text NOT NULL,
  email                text UNIQUE,
  telephone            text,
  nb_reservations      integer NOT NULL DEFAULT 0,
  derniere_visite      date,
  dernier_avis_envoye  date,
  notes                text,
  note                 numeric(2,1),                       -- 0.0 .. 5.0
  avis_recu            boolean NOT NULL DEFAULT false,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS clients_email_idx     ON public.clients (email);
CREATE INDEX IF NOT EXISTS clients_derniere_idx  ON public.clients (derniere_visite DESC);
