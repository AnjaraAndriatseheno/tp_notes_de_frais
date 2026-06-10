import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime

class GoogleSheetsClient:
    def __init__(self):
        load_dotenv()

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        credentials_path = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
        self.credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=scopes
        )

        self.client = gspread.authorize(self.credentials)

        sheet_id = os.environ["GOOGLE_SHEET_ID"]
        self.spreadsheet = self.client.open_by_key(sheet_id)
        self.sheet = self.spreadsheet.worksheet("Notes de frais")

    def append_expense(self, data: dict, image_url: str = None) -> None:
        row = [
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            data.get("type_document"),
            data.get("fournisseur"),
            data.get("date"),
            data.get("montant_ttc"),
            data.get("tva"),
            data.get("devise"),
            data.get("description"),
            data.get("confiance"),
            image_url if image_url else ""
        ]

        self.sheet.append_row(row)


if __name__ == "__main__":
    client = GoogleSheetsClient()

    fake_data = {
        "type_document": "restaurant",
        "fournisseur": "Bistrot Test",
        "date": "10/06/2025",
        "montant_ttc": 24.50,
        "tva": 2.18,
        "devise": "EUR",
        "description": "Test d'intégration",
        "confiance": "haute"
    }

    client.append_expense(fake_data)
    print("Ligne ajoutée avec succès !")