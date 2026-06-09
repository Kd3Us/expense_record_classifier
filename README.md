# Expense Agent — Gestion Agentique des Notes de Frais

Application web agentique permettant à un salarié de photographier une note de frais, d'en extraire automatiquement les informations via un modèle de vision, de les corriger manuellement si besoin, puis de les synchroniser dans un Google Sheet partagé avec le service comptabilité. L'image est archivée sur Supabase Storage.

## Stack technique

| Composant | Technologie |
|---|---|
| Modèle IA | meta-llama/llama-4-scout-17b-16e-instruct via SDK Groq |
| Backend | Python · FastAPI |
| Frontend | HTML · HTMX · CSS · JS Vanilla |
| Stockage images | Supabase Storage |
| Intégration données | Google Sheets API via gspread |

## Structure du projet

```
expense-agent/
├── backend.py        # Classe ExpenseAgent — logique IA
├── app.py            # Serveur FastAPI — routes et orchestration
├── sheets.py         # Classe GoogleSheetsClient — Sheets + Supabase
├── context.txt       # Prompt système du modèle
├── prompt.txt        # Prompt utilisateur envoyé avec l'image
├── requirements.txt
├── .env.example
├── .env              # Non commité
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## Installation

```bash
git clone <url-du-repo>
cd expense-agent
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Configuration

Copie `.env.example` en `.env` et renseigne les variables :

```
GROQ_API_KEY=""
GOOGLE_SHEET_ID=""
GOOGLE_SERVICE_ACCOUNT_JSON=""
SUPABASE_URL=""
SUPABASE_ANON_KEY=""
```

### Google Cloud

1. Créer un projet sur [console.cloud.google.com](https://console.cloud.google.com)
2. Activer **Google Sheets API**
3. Créer un compte de service et télécharger la clé JSON
4. Partager le Google Sheet avec l'email du compte de service (rôle Éditeur)
5. Copier l'ID du Sheet depuis l'URL et le mettre dans `GOOGLE_SHEET_ID`

### Supabase

1. Créer un projet sur [supabase.com](https://supabase.com) (région Europe)
2. Créer un bucket nommé `expense-receipts` en **public**
3. Récupérer `SUPABASE_URL` et la clé depuis **Project Settings → API Keys**

## Lancer l'application

```bash
uvicorn app:app --reload
```

L'application est accessible sur `http://localhost:8000`.

## Exemple de JSON retourné par le modèle

```json
{
  "type_document": "restaurant",
  "fournisseur": "Bistrot Paul",
  "date": "09/06/2026",
  "montant_ttc": 24.50,
  "tva": 2.45,
  "devise": "EUR",
  "description": "Déjeuner d'équipe au restaurant Bistrot Paul",
  "confiance": "haute"
}
```