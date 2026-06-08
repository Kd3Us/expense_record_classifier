import os
import base64
import uuid

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv

from backend import ExpenseAgent
from sheets import GoogleSheetsClient

load_dotenv()

app = FastAPI()
agent = ExpenseAgent()
sheets_client = GoogleSheetsClient()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...)):
    # Validation du type MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        return HTMLResponse(
            content=_error_html(f"Type de fichier non supporté : {file.content_type}. Utilisez JPG, PNG ou WebP."),
            status_code=400
        )

    image_bytes = await file.read()

    # Validation de la taille
    if len(image_bytes) > MAX_FILE_SIZE:
        return HTMLResponse(
            content=_error_html("Image trop volumineuse (maximum 10 Mo)."),
            status_code=400
        )

    try:
        data = agent.extract_from_bytes(image_bytes, file.content_type)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        return HTMLResponse(content=_build_form_html(data, image_b64, file.content_type))
    except Exception as e:
        return HTMLResponse(
            content=_error_html(f"Erreur lors de l'analyse : {str(e)}"),
            status_code=500
        )


@app.post("/api/submit", response_class=HTMLResponse)
async def submit(
    type_document: str = Form(default=""),
    fournisseur: str = Form(default=""),
    date: str = Form(default=""),
    montant_ttc: str = Form(default=""),
    tva: str = Form(default=""),
    devise: str = Form(default="EUR"),
    description: str = Form(default=""),
    confiance: str = Form(default=""),
    image_data: str = Form(default=""),
    image_media_type: str = Form(default="image/jpeg"),
):
    try:
        data = {
            "type_document": type_document or None,
            "fournisseur": fournisseur or None,
            "date": date or None,
            "montant_ttc": float(montant_ttc) if montant_ttc else None,
            "tva": float(tva) if tva else None,
            "devise": devise or "EUR",
            "description": description or None,
            "confiance": confiance or None,
        }

        image_url = None
        if image_data:
            image_bytes = base64.b64decode(image_data)
            image_url = sheets_client.upload_image(image_bytes, image_media_type)

        sheets_client.append_expense(data, image_url)

        return HTMLResponse(content=_success_html(fournisseur, montant_ttc))

    except Exception as e:
        return HTMLResponse(
            content=_error_html(f"Erreur lors de la soumission : {str(e)}"),
            status_code=500
        )


def _build_form_html(data: dict, image_b64: str, media_type: str) -> str:
    """Construit le fragment HTML du formulaire pré-rempli retourné à HTMX."""

    type_options = ["restaurant", "transport", "hôtel", "autre"]
    confiance_options = ["haute", "moyen", "basse"]

    def make_select(name: str, options: list, selected: str | None) -> str:
        opts = "".join(
            f'<option value="{o}" {"selected" if o == selected else ""}>{o}</option>'
            for o in options
        )
        return f'<select name="{name}">{opts}</select>'

    def field_value(key: str) -> str:
        val = data.get(key)
        return str(val) if val is not None else ""

    return f"""
    <form hx-post="/api/submit"
          hx-target="#confirmation-container"
          hx-encoding="application/x-www-form-urlencoded">

        <div class="form-group">
            <label>Type de document</label>
            {make_select("type_document", type_options, data.get("type_document"))}
        </div>
        <div class="form-group">
            <label>Fournisseur</label>
            <input type="text" name="fournisseur" value="{field_value("fournisseur")}">
        </div>
        <div class="form-group">
            <label>Date</label>
            <input type="text" name="date" value="{field_value("date")}" placeholder="JJ/MM/AAAA">
        </div>
        <div class="form-group">
            <label>Montant TTC (€)</label>
            <input type="number" step="0.01" name="montant_ttc" value="{field_value("montant_ttc")}">
        </div>
        <div class="form-group">
            <label>TVA (€)</label>
            <input type="number" step="0.01" name="tva" value="{field_value("tva")}">
        </div>
        <div class="form-group">
            <label>Devise</label>
            <input type="text" name="devise" value="{field_value("devise")}">
        </div>
        <div class="form-group">
            <label>Description</label>
            <input type="text" name="description" value="{field_value("description")}">
        </div>
        <div class="form-group">
            <label>Confiance</label>
            {make_select("confiance", confiance_options, data.get("confiance"))}
        </div>

        <input type="hidden" name="image_data" value="{image_b64}">
        <input type="hidden" name="image_media_type" value="{media_type}">

        <button type="submit" class="btn-submit">
            Envoyer vers le Google Sheet
        </button>
    </form>
    """


def _success_html(fournisseur: str, montant: str) -> str:
    return f"""
    <div class="alert alert-success">
        ✅ Note de frais <strong>{fournisseur}</strong> ({montant} €) enregistrée avec succès !
        <br><br>
        <button onclick="resetApp()" class="btn-reset">Nouvelle note de frais</button>
    </div>
    """


def _error_html(message: str) -> str:
    return f'<div class="alert alert-error">❌ {message}</div>'