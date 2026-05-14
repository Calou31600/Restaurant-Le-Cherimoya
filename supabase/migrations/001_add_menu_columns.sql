-- 001 — Ajoute à `menu` les colonnes présentes dans Airtable Dynamic_Menu
--       mais oubliées lors de la première migration.
--
-- Champs ajoutés :
--   plat_en              : titre du plat en anglais
--   description_geo_en   : description en anglais
--   menu                 : catégories (Entrées / Asie / À Partager / Côté Terre /
--                          Côté Mer / Douceurs / Boissons / Formules)
--   intolerances         : allergènes (Lactose / Gluten / Cacahuète)
--
-- Idempotent : utilise IF NOT EXISTS.

ALTER TABLE public.menu ADD COLUMN IF NOT EXISTS plat_en            text;
ALTER TABLE public.menu ADD COLUMN IF NOT EXISTS description_geo_en text;
ALTER TABLE public.menu ADD COLUMN IF NOT EXISTS menu               text[] DEFAULT '{}'::text[];
ALTER TABLE public.menu ADD COLUMN IF NOT EXISTS intolerances       text[] DEFAULT '{}'::text[];
