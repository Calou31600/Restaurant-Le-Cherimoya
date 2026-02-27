# SOP: Booking Rules & Inventory Management (`sop_booking_rules.md`)

## Objectif
Assurer un flux de réservation fluide tout en protégeant les opérations du restaurant contre les réservations de dernière minute imprévues.

## Règles Métier

### 1. Protection du Service (La règle des 2h)
- **Interdiction Formelle** : Aucune réservation en ligne n'est acceptée à moins de **2 heures** du début du service.
- **Logique** : 
  - Service Midi (12h00) -> Clôture des réservations à 10h00.
  - Service Soir (19h30) -> Clôture des réservations à 17h30.
- **Action UI** : Afficher un message "Pour une réservation immédiate, merci de nous appeler au [Téléphone]".

### 2. Gestion de l'Inventaire (Airtable)
- Avant d'afficher le formulaire de réservation, le système vérifie la table `Inventory`.
- **Condition de Disponibilité** : `capacite_totale` - `reservations_confirmées` > 0.
- **Complet** : Si la différence est nulle, le statut devient `Complet` et le formulaire est désactivé.

### 3. Fonction "Table Habituelle"
- **Visiteurs Récurrents** (détectés via LocalStorage ou Cookie):
  - Afficher un bouton prioritaire "Réserver ma table habituelle".
  - Pré-remplir les champs : Nom, Nombre de couverts habituel, Allergies connues.

## Flux de Données
1. Utilisateur choisit une date/heure.
2. Script vérifie `Inventory` + Règle des 2h.
3. Si OK, enregistre le record dans Airtable.
4. n8n (futur) envoie une confirmation.
