import os
import io
import uuid
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class GoogleSheetsClient:
    """Gère l'écriture dans le Google Sheet et l'upload d'images sur Drive."""

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

        self.drive = build("drive", "v3", credentials=creds)

    def upload_image(self, image_bytes: bytes, media_type: str) -> str:
        """
        Upload une image sur Google Drive et retourne son URL publique.

        Args:
            image_bytes: contenu brut de l'image
            media_type: type MIME (ex: "image/jpeg")

        Returns:
            URL publique de l'image sur Drive
        """
        extension = media_type.split("/")[-1]
        filename = f"note_frais_{uuid.uuid4().hex[:8]}.{extension}"

        file_metadata = {"name": filename}
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=media_type)

        file = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = file.get("id")

        self.drive.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"}
        ).execute()

        return f"https://drive.google.com/uc?id={file_id}"

    @staticmethod
    def _build_row(data: dict, image_url: str | None) -> list:
        """
        Construit la liste de valeurs à insérer dans le Sheet.
        Méthode statique car elle ne dépend pas de l'état de l'instance.
        """
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
        """
        Ajoute une ligne de note de frais dans le Google Sheet.

        Args:
            data: dict avec les champs extraits par ExpenseAgent
            image_url: URL publique de l'image sur Drive, None si pas d'image
        """
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
        "description": "Test intégration Google Sheets",
        "confiance": "haute"
    }

    client.append_expense(test_data, image_url=None)
    print("✅ Ligne ajoutée avec succès !")