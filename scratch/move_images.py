import os
import shutil
import glob

# Source: brain directory
source_dir = r"C:\Users\pasca\.gemini\antigravity\brain\2725d438-3ee2-4087-bacd-789e877e15fc"
# Destination: project directory
dest_dir = r"c:\Users\pasca\Downloads\Programme vibe coding\Restaurant Le Cherimoya\Photos Menu\Generated"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Patterns to match generated images
patterns = [
    "the_noir_en_sachet_premium*.png",
    "infusion_camomille_premium*.png",
    "jus_ananas_premium*.png",
    "coleslaw_maison_premium*.png",
    "biere_saigon_premium*.png",
    "biere_pression_premium*.png",
    "eau_coco_premium*.png",
    "bavarois_selection_premium*.png",
    "nouilles_poulet_premium*.png",
    "citron_rafraichissant_premium*.png",
    "nouilles_boeuf_premium*.png",
    "brise_asie_soleil_premium*.png"
]

for pattern in patterns:
    files = glob.glob(os.path.join(source_dir, pattern))
    for f in files:
        # Clean filename: remove timestamp (everything after the last underscore if it's a number)
        base = os.path.basename(f)
        name, ext = os.path.splitext(base)
        parts = name.split('_')
        if parts[-1].isdigit():
            clean_name = "_".join(parts[:-1]) + ext
        else:
            clean_name = base
            
        dest_path = os.path.join(dest_dir, clean_name)
        print(f"Moving {f} to {dest_path}")
        shutil.copy2(f, dest_path)
