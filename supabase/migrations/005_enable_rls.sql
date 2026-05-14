-- 005 — Active Row Level Security et pose les policies minimales.
--
-- ⚠️ PRÉREQUIS : il faut une SUPABASE_SERVICE_ROLE_KEY définie dans .env
--    et sur Vercel AVANT d'appliquer ce script. Sinon le backend Flask, qui
--    utilise actuellement la clé publishable (rôle `anon`), ne pourra plus
--    faire ni UPDATE ni DELETE et l'admin sera cassé.
--
-- Le service_role est exempt de RLS par défaut. Le backend doit donc
-- créer son client Supabase avec cette clé :
--     create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
--
-- Le rôle `anon` (clé publishable) garde uniquement le SELECT public sur
-- les tables affichées sur le site (menu, wines, special_menus).
-- Tout le reste est interdit côté anon.

-- ─── Active RLS sur toutes les tables applicatives ───────────────────────────
ALTER TABLE public.menu            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wines           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.special_menus   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reservations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.availability    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clients         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.commandes       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings        ENABLE ROW LEVEL SECURITY;

-- ─── Policies SELECT publiques ───────────────────────────────────────────────
-- Le site (rôle anon) doit pouvoir lire menu, vins, événements actifs.

DROP POLICY IF EXISTS "menu lisible publiquement"          ON public.menu;
CREATE POLICY "menu lisible publiquement"          ON public.menu
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "vins lisibles publiquement"         ON public.wines;
CREATE POLICY "vins lisibles publiquement"         ON public.wines
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "menus speciaux lisibles publiquement" ON public.special_menus;
CREATE POLICY "menus speciaux lisibles publiquement" ON public.special_menus
  FOR SELECT TO anon, authenticated USING (true);

-- availability est lue uniquement pour vérifier la dispo lors d'une réservation.
-- C'est consommé côté serveur via service_role, mais on garde un SELECT public
-- ouvert (il n'y a aucune donnée sensible dedans : juste capacité totale et
-- nombre déjà confirmé).
DROP POLICY IF EXISTS "availability lisible publiquement" ON public.availability;
CREATE POLICY "availability lisible publiquement" ON public.availability
  FOR SELECT TO anon, authenticated USING (true);

-- ─── Aucune policy pour les tables sensibles ─────────────────────────────────
-- reservations, clients, commandes, settings : RLS activée, AUCUNE policy
-- pour le rôle anon. Toute lecture/écriture passe obligatoirement par
-- le backend Flask via service_role.
--
-- (Le rôle service_role contourne RLS par design — il a tous les droits.)

-- ─── Note opérationnelle ─────────────────────────────────────────────────────
-- Pour récupérer la SUPABASE_SERVICE_ROLE_KEY :
--   Dashboard Supabase → Project Settings → API → Service Role secret
-- À copier dans :
--   1. .env local                 → SUPABASE_SERVICE_ROLE_KEY=eyJ...
--   2. Vercel Project Settings    → Environment Variables (les DEUX projets si
--                                   tu as deux comptes connectés au même repo)
--
-- Puis dans app.py / settings_manager.py / booking_manager.py / main_engine.py,
-- préférer SUPABASE_SERVICE_ROLE_KEY à SUPABASE_KEY côté serveur :
--   key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
