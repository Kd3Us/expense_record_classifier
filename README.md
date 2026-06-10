# Expense Tracker — Application Agentique de Gestion des Notes de Frais

Application web agentique permettant à un salarié de photographier une note de frais (ticket de restaurant, billet de train, facture d'hôtel...), d'en extraire automatiquement les informations via un modèle de vision, de les corriger dans un formulaire éditable, puis de les synchroniser dans un Google Sheet partagé avec le service comptabilité. L'image du justificatif est archivée sur Google Drive et référencée dans le Sheet.

Projet réalisé dans la continuité du TP *Handcrafted Google Lens*.

## Fonctionnement

1. **Upload** — L'utilisateur dépose ou photographie un justificatif (JPG, PNG, WebP — 10 Mo max).
2. **Extraction IA** — Le backend envoie l'image au modèle de vision `meta-llama/llama-4-scout-17b-16e-instruct` (via l'API Groq) qui retourne un JSON structuré.
3. **Édition** — Les champs extraits sont affichés dans un formulaire pré-rempli et entièrement modifiable.
4. **Soumission** — À la validation, l'image est uploadée sur Google Drive et une ligne est ajoutée au Google Sheet avec les valeurs (éventuellement corrigées) et la formule `=IMAGE(url)`.

## Stack technique

| Composant   | Technologie                                          |
|-------------|------------------------------------------------------|
| Modèle IA   | `meta-llama/llama-4-scout-17b-16e-instruct` via SDK Groq |
| Backend     | Python · FastAPI                                     |
| Frontend    | HTML · HTMX · CSS · JS Vanilla                       |
| Intégration | Google Sheets API (`gspread`) · Google Drive API     |

## Structure du projet

```
expense-tracker/
├── backend.py        # Classe ExpenseAgent — logique IA (extraction vision)
├── app.py            # Serveur FastAPI — routes et orchestration
├── sheets.py         # Classe GoogleSheetsClient — Google Sheets + Drive
├── context.txt       # Prompt système du modèle
├── prompt.txt        # Prompt utilisateur envoyé avec l'image
├── requirements.txt
├── .env.example
├── .env              # Non commité
└── static/
    ├── index.html    # Interface HTMX
    ├── style.css     # Feuille de style
    └── app.js        # JS Vanilla (prévisualisation, events HTMX)
```

## Installation

### 1. Cloner et installer les dépendances

```bash
git clone <url-du-depot>
cd expense-tracker

python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configuration Google Cloud

1. Créer un projet sur [console.cloud.google.com](https://console.cloud.google.com) (ex : `expense-tracker-tp`).
2. Dans **API et services > Bibliothèque**, activer :
   - **Google Sheets API**
   - **Google Drive API**
3. Dans **API et services > Identifiants**, créer un **compte de service** (ex : `expense-agent`) avec le rôle Éditeur, puis télécharger sa **clé JSON**.
   ⚠️ Ne jamais commiter ce fichier — il est exclu par le `.gitignore` (`*.json`).

### 3. Préparation du Google Sheet

1. Créer un nouveau Google Sheet et renommer la première feuille en `Notes de frais`.
2. Sur la première ligne, créer les en-têtes dans cet ordre :
   `Horodatage`, `Type`, `Fournisseur`, `Date`, `Montant TTC (€)`, `TVA (€)`, `Devise`, `Description`, `Confiance`, `Image`
3. **Partager le Sheet** avec l'adresse email du compte de service (du type `expense-agent@expense-tracker-tp.iam.gserviceaccount.com`) en rôle **Éditeur**.
4. Copier l'ID du Sheet depuis l'URL (la chaîne entre `/d/` et `/edit`).

### 4. Variables d'environnement

Copier `.env.example` vers `.env` et renseigner :

```env
GROQ_API_KEY="votre_cle_groq"
GOOGLE_SHEET_ID="id_du_google_sheet"
GOOGLE_SERVICE_ACCOUNT_JSON="chemin/vers/credentials.json"
```

### 5. Lancer l'application

```bash
uvicorn app:app --reload
```

L'application est disponible sur [http://localhost:8000](http://localhost:8000).

## Tests en ligne de commande

Tester l'extraction seule (sans le frontend) :

```bash
python backend.py chemin/vers/ticket.jpg
```

Tester l'intégration Google Sheets de manière isolée (pousse une ligne factice) :

```bash
python sheets.py
```

## Exemple de JSON retourné par le modèle

```json
{
  "type_document": "restaurant",
  "fournisseur": "Bistrot Paul",
  "date": "12/03/2026",
  "montant_ttc": 24.50,
  "tva": 2.23,
  "devise": "EUR",
  "description": "Déjeuner d'affaires au Bistrot Paul",
  "confiance": "haute"
}
```

Si un champ est illisible ou absent du document, le modèle retourne `null` pour ce champ et ajuste le niveau de `confiance` (`haute`, `moyen`, `basse`). Le backend valide systématiquement la présence des 8 champs attendus.

## Routes de l'API

| Méthode | Route          | Description                                                        |
|---------|----------------|--------------------------------------------------------------------|
| GET     | `/`            | Sert l'interface (`static/index.html`)                             |
| POST    | `/api/analyze` | Reçoit l'image en multipart, retourne le formulaire HTML pré-rempli |
| POST    | `/api/submit`  | Reçoit les champs du formulaire, upload l'image sur Drive, ajoute la ligne au Sheet |

Les routes retournent des **fragments HTML** (pattern HTMX), jamais de JSON brut — y compris pour les erreurs.

## Sécurité

- `.env` et les clés JSON de compte de service sont exclus du dépôt via `.gitignore`.
- Validation du type MIME (`image/jpeg`, `image/png`, `image/webp`) et de la taille (10 Mo max) côté serveur.
- En cas de fuite de credentials : révoquer et régénérer la clé depuis la Google Cloud Console.