"""Purge Dynamic_Menu puis crée les 63 nouvelles fiches.

Étapes :
1. Charge les 3 JSON (.tmp/new_dishes_A|B|C.json) et fusionne.
2. Construit le mapping photo : ancien nom -> URL Cloudinary, puis applique au nouveau nom.
3. Supprime les 46 anciens records par batchs de 10.
4. Crée les nouveaux par batchs de 10 avec typecast=true (auto-création prix manquants).
5. Dump le résultat pour vérification.
"""
import os, json, time, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["AIRTABLE_API_KEY"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
URL = f"https://api.airtable.com/v0/{BASE_ID}/Dynamic_Menu"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, ".tmp")

# ---------- 1. Charger les nouvelles fiches ----------
new_dishes = []
for letter in ("A", "B", "C"):
    with open(os.path.join(TMP, f"new_dishes_{letter}.json"), encoding="utf-8") as f:
        new_dishes.extend(json.load(f))
print(f"[1] {len(new_dishes)} nouvelles fiches chargées")

# ---------- 2. Mapping photo (ancien nom Airtable -> nouveau nom) ----------
# Basé sur similarité sémantique. Premier match = on garde l'URL existante.
PHOTO_MAP = {
    # nouveau nom : ancien nom dans backup
    "Paradis Asiatique":                        "Paradis asiatique",
    "Tiramisu au café":                    "Tiramisu au café",
    "Mojito":                                   "Mojito",
    "Americano":                                "Américano",
    "Piña Colada":                         "Pina colada",
    "Sunset Boulevard":                         "Sunset boulevard",
    "Nems croustillants":                       "4 nems poulet croustillants",
    "Assiette de fromages et charcuteries":     "Assiette de charcuterie et fromages",
    "Mini Cabécou Fondant":                "Salade de camembert roti",
    "Tartelette aux Pommes Caramélisées": "Tartelette tatin",
    "Tataki de Bœuf":                      "Tataki de bœuf 250gr",
    "Entrecôte de Bœuf 250gr":         "Faux filet de bœuf 250gr",
    "Tranches de Magret Caramélisé":  "Filet de canard sauce caramel balsamique",
    "Agneau Sublime, Sauce Maison":             "Côtes d’agneau grillés aux herbes",
    "Pavé de Saumon Maison":               "Saumon sauce teriyaki",
    "Délice de Limande":                   "Filet de bar au beurre",
    "Éclats de Poulet, Saveurs d'Asie":    "Poulet sauce teriyaki",
    "Poulet Rôti à la Crème d'Herbes": "Filet de poulet au cheddar",
    "Crème Brûlée traditionnelle": "Crème Brûlée au Café",
    "Glaces au Choix":                          "Glaces (2 boules au choix)",
    "Gambas Sautées au Beurre et Ail":     "Crevettes sautées beurre ail",
    "Flamme de Gambas sur Brochette":           "Grosses gambas grillées 3pc",
    "Hamburger Enfant":                         "Menu Enfant",
    "Joue de Bœuf Confite aux Herbes, Jus Corsé": "Joue de bœuf confite au four",
    "Salade Croquante au Nem":                  "Salade de nems",
}

with open(os.path.join(TMP, f"dishes_backup_2026-05-12.json"), encoding="utf-8") as f:
    old_records = json.load(f)
old_photo_by_name = {r["fields"].get("Plat", ""): r["fields"].get("Photo", "")
                     for r in old_records if r["fields"].get("Photo")}

# Field IDs (from full_schema.json)
F = {
    "Plat":              "fldfpeyIoKJ0nQFp6",
    "description_geo":   "fldfrjUmO3NC5XgEn",
    "prix":              "fldzfu1Q3TnICqgFZ",
    "Photo":             "fld1VuTZCm8iYZnBr",
    "Plat_EN":           "fldsdlILhLzzdj6ZA",
    "description_geo_EN":"fld7MNQigQ4FqlWu9",
    "Menu":              "fldcuYN3xIXwEZyFr",
    "tags_meteo":        "fldPXf4BA4TYNBl1N",
}

matched, missed = 0, 0
for d in new_dishes:
    old = PHOTO_MAP.get(d["Plat"])
    if old and old_photo_by_name.get(old):
        d["_photo_url"] = old_photo_by_name[old]
        matched += 1
    else:
        d["_photo_url"] = ""
        missed += 1
print(f"[2] Photos reportées : {matched} / {len(new_dishes)}  (sans photo : {missed})")

# ---------- 3. Purge des anciens ----------
old_ids = [r["id"] for r in old_records]
print(f"[3] Suppression de {len(old_ids)} anciens records...")
deleted = 0
for i in range(0, len(old_ids), 10):
    batch = old_ids[i:i+10]
    params = "&".join(f"records[]={rid}" for rid in batch)
    res = requests.delete(f"{URL}?{params}", headers=HEADERS)
    if res.status_code == 200:
        deleted += len(batch)
        print(f"    supprimé batch {i//10+1} ({len(batch)} records)")
    else:
        print(f"    ERREUR batch {i//10+1}: {res.status_code} {res.text[:200]}")
        raise SystemExit(1)
    time.sleep(0.25)
print(f"[3] Total supprimé : {deleted}")

# ---------- 4. Création des nouveaux ----------
print(f"[4] Création de {len(new_dishes)} nouveaux records (typecast=true)...")
created = 0
created_records = []
for i in range(0, len(new_dishes), 10):
    batch = new_dishes[i:i+10]
    records_payload = []
    for d in batch:
        fields = {
            F["Plat"]:               d["Plat"],
            F["Plat_EN"]:            d["Plat_EN"],
            F["description_geo"]:    d["description_geo"],
            F["description_geo_EN"]: d["description_geo_EN"],
            F["prix"]:               d["prix"],
            F["Menu"]:               d["Menu"],
        }
        if d.get("_photo_url"):
            fields[F["Photo"]] = d["_photo_url"]
        records_payload.append({"fields": fields})
    payload = {"records": records_payload, "typecast": True}
    res = requests.post(URL, headers=HEADERS, json=payload)
    if res.status_code == 200:
        rec = res.json().get("records", [])
        created += len(rec)
        created_records.extend(rec)
        print(f"    créé batch {i//10+1} ({len(rec)} records)")
    else:
        print(f"    ERREUR batch {i//10+1}: {res.status_code} {res.text[:500]}")
        raise SystemExit(2)
    time.sleep(0.25)
print(f"[4] Total créé : {created}")

# ---------- 5. Dump pour vérification ----------
out = os.path.join(TMP, "dishes_after_swap.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(created_records, f, ensure_ascii=False, indent=2)
print(f"[5] Snapshot post-swap : {out}")
print("OK")
