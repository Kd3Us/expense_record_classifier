import os
import uuid
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleSheetsClient:

    SHEET_NAME = "Notes de frais"
    COLUMNS = [
        "Horodatage", "Type", "Fournisseur", "Date",
        "Montant TTC (€)", "TVA (€)", "Devise",
        "Description", "Confiance", "Image"
    ]

    def __init__(self):
        creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not creds_path:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON manquante dans le .env")

        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID manquant dans le .env")

        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        self.sheet = spreadsheet.worksheet(self.SHEET_NAME)

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL ou SUPABASE_ANON_KEY manquante dans le .env")

        self.supabase = create_client(supabase_url, supabase_key)

    def upload_image(self, image_bytes: bytes, media_type: str) -> str:
        extension = media_type.split("/")[-1]
        filename = f"notes/{uuid.uuid4().hex[:8]}.{extension}"

        self.supabase.storage.from_("expense-receipts").upload(
            filename,
            image_bytes,
            {"content-type": media_type}
        )

        return self.supabase.storage.from_("expense-receipts").get_public_url(filename)

    @staticmethod
    def _build_row(data: dict, image_url: str | None) -> list:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        image_cell = f'=IMAGE("{image_url}")' if image_url else ""

        return [
            timestamp,
            data.get("type_document") or "",
            data.get("fournisseur") or "",
            data.get("date") or "",
            data.get("montant_ttc") or "",
            data.get("tva") or "",
            data.get("devise") or "EUR",
            data.get("description") or "",
            data.get("confiance") or "",
            image_cell
        ]

    def append_expense(self, data: dict, image_url: str | None = None) -> None:
        row = self._build_row(data, image_url)
        self.sheet.append_row(row, value_input_option="USER_ENTERED")


if __name__ == "__main__":
    client = GoogleSheetsClient()

    test_data = {
        "type_document": "restaurant",
        "fournisseur": "Bistrot Test",
        "date": "01/01/2025",
        "montant_ttc": 25.50,
        "tva": 2.55,
        "devise": "EUR",
        "description": "Test intégration Supabase + Google Sheets",
        "confiance": "haute"
    }

    client.append_expense(test_data, image_url=None)
    print("✅ Ligne ajoutée avec succès !")