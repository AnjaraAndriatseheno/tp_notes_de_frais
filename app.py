from pathlib import Path
from html import escape
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend import ExpenseAgent
from sheets import GoogleSheetsClient
import base64

BASE_DIR = Path(__file__).parent
MAX_FILE_SIZE = 10 * 1024 * 1024  
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="Notes de Frais")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

agent = ExpenseAgent()
sheets_client = GoogleSheetsClient()

CONFIDENCE_CLASS = {"haute": "confidence-high", "moyen": "confidence-medium", "basse": "confidence-low"}


def build_form_fragment(data: dict, image_data: str, media_type: str) -> str:
    def selected(field, value):
        return "selected" if str(data.get(field) or "").lower() == value else ""

    type_doc = data.get("type_document") or ""
    fournisseur = escape(str(data.get("fournisseur") or ""))
    date = escape(str(data.get("date") or ""))
    montant_ttc = escape(str(data.get("montant_ttc") or ""))
    tva = escape(str(data.get("tva") or ""))
    devise = escape(str(data.get("devise") or "EUR"))
    description = escape(str(data.get("description") or ""))
    confiance_raw = str(data.get("confiance") or "").lower()
    confidence_class = CONFIDENCE_CLASS.get(confiance_raw, "confidence-medium")
    confiance_label = escape(str(data.get("confiance") or "—"))

    return f"""
<form hx-post="/api/submit" hx-target="#confirmation-container" hx-swap="innerHTML">
    <input type="hidden" name="image_data" value="{escape(image_data)}" />
    <input type="hidden" name="image_media_type" value="{escape(media_type)}" />

    <div class="result-grid">

        <div class="result-row">
            <span class="result-label">Type de document</span>
            <select name="type_document">
                <option value="restaurant" {selected("type_document", "restaurant")}>Restaurant</option>
                <option value="transport" {selected("type_document", "transport")}>Transport</option>
                <option value="hôtel" {selected("type_document", "hôtel")}>Hôtel</option>
                <option value="autre" {selected("type_document", "autre")}>Autre</option>
            </select>
        </div>

        <div class="result-row">
            <span class="result-label">Fournisseur</span>
            <input type="text" name="fournisseur" value="{fournisseur}" />
        </div>

        <div class="result-row">
            <span class="result-label">Date</span>
            <input type="text" name="date" value="{date}" placeholder="JJ/MM/AAAA" />
        </div>

        <div class="result-row">
            <span class="result-label">Montant TTC (€)</span>
            <input type="number" step="0.01" name="montant_ttc" value="{montant_ttc}" />
        </div>

        <div class="result-row">
            <span class="result-label">TVA (€)</span>
            <input type="number" step="0.01" name="tva" value="{tva}" />
        </div>

        <div class="result-row">
            <span class="result-label">Devise</span>
            <input type="text" name="devise" value="{devise}" />
        </div>

        <div class="result-row">
            <span class="result-label">Description</span>
            <input type="text" name="description" value="{description}" />
        </div>

        <div class="result-row">
            <span class="result-label">Confiance</span>
            <span class="confidence-badge {confidence_class}">{confiance_label}</span>
            <input type="hidden" name="confiance" value="{confiance_raw}" />
        </div>

    </div>

    <button type="submit" class="btn-submit">Envoyer vers Google Sheets</button>
</form>
"""


@app.exception_handler(HTTPException)
async def htmx_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        content=f'<p class="result-error">Erreur {exc.status_code} : {exc.detail}</p>',
        status_code=exc.status_code,
    )


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(415, detail="Type de fichier non supporté. Veuillez envoyer une image.")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, detail=f"Format non supporté : {file.content_type}. Formats acceptés : JPEG, PNG, WEBP.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, detail="Image trop volumineuse (maximum 10 Mo).")

    try:
        data = agent.extract_from_bytes(image_bytes, media_type=file.content_type)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur du modèle : {str(e)}")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data = f"data:{file.content_type};base64,{image_b64}"

    return HTMLResponse(content=build_form_fragment(data, image_data, file.content_type))


@app.post("/api/submit", response_class=HTMLResponse)
async def submit_expense(
    type_document: str = Form(...),
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
    data = {
        "type_document": type_document,
        "fournisseur": fournisseur or None,
        "date": date or None,
        "montant_ttc": float(montant_ttc) if montant_ttc else None,
        "tva": float(tva) if tva else None,
        "devise": devise or "EUR",
        "description": description or None,
        "confiance": confiance or None,
    }

    try:
        sheets_client.append_expense(data, image_url=None)
    except Exception as e:
        raise HTTPException(500, detail=f"Erreur Google Sheets : {str(e)}")

    return HTMLResponse(content="""
        <p class="result-success">Note de frais enregistrée avec succès dans Google Sheets !</p>
    """)