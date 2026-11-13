from __future__ import annotations

import asyncio
import base64
from datetime import date, datetime
import html as html_lib
import json
from pathlib import Path
import re
import threading
from typing import Any
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pydantic import BaseModel, Field
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
CANDIDATURAS_PATH = BASE_DIR / "candidaturas.json"
DASHBOARD_PATH = BASE_DIR / "dashboard.html"
BROWSER_SESSION_DIR = BASE_DIR / "browser_session"
SALIDAS_DIR = BASE_DIR / "salidas"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GMAIL_QUERY = "from:linkedin.com newer_than:5d"

VALID_ESTADOS = {"pendiente_ia", "lista_para_aplicar", "aplicada", "descartada"}

_DATA_LOCK = threading.Lock()
_OAUTH_LOCK = threading.Lock()

LINKEDIN_JOB_RE = re.compile(
    r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:comm/)?jobs/view/(?:[^/?#\s\"'<>]*-)?(\d+)",
    re.IGNORECASE,
)
LINKEDIN_TRACKED_REDIRECT_RE = re.compile(
    r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/[^\s\"'<>]+",
    re.IGNORECASE,
)


app = FastAPI(title="Radar de Candidaturas", version="1.0.0")


class OfertaManualPayload(BaseModel):
    empresa: str = Field(default="", max_length=200)
    puesto: str = Field(default="", max_length=240)
    modalidad: str = Field(default="Por confirmar", max_length=120)
    url_oferta: str = Field(default="", max_length=1000)
    descripcion: str = Field(default="", max_length=30000)
    notas: str = Field(default="", max_length=4000)


class ActualizarPayload(BaseModel):
    estado: str | None = None
    notas: str | None = None
    motivo_descarte: str | None = None


def _ensure_storage() -> None:
    if not CANDIDATURAS_PATH.exists():
        CANDIDATURAS_PATH.write_text("[]\n", encoding="utf-8")


def _load_candidaturas() -> list[dict[str, Any]]:
    _ensure_storage()
    with _DATA_LOCK:
        raw = CANDIDATURAS_PATH.read_text(encoding="utf-8-sig").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return data


def _save_candidaturas(items: list[dict[str, Any]]) -> None:
    with _DATA_LOCK:
        tmp = CANDIDATURAS_PATH.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(CANDIDATURAS_PATH)


def _slugify(value: str, max_len: int = 40) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (cleaned[:max_len].strip("-")) or "oferta"


def _normalize_offer_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    match = LINKEDIN_JOB_RE.search(raw)
    if match:
        return f"https://www.linkedin.com/jobs/view/{match.group(1)}/"
    return raw.split("#")[0].strip()


def _extract_linkedin_job_id(url: str) -> str | None:
    match = LINKEDIN_JOB_RE.search(url or "")
    return match.group(1) if match else None


def _build_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "todas": len(items),
        "lista_para_aplicar": 0,
        "pendiente_ia": 0,
        "aplicada": 0,
        "descartada": 0,
    }
    for item in items:
        estado = item.get("estado", "pendiente_ia")
        if estado in counts:
            counts[estado] += 1
    return counts


def _new_candidatura(
    *,
    empresa: str,
    puesto: str,
    modalidad: str,
    url_oferta: str,
    descripcion: str = "",
    notas: str = "",
    origen: str = "manual",
) -> dict[str, Any]:
    now = datetime.now()
    slug = _slugify(f"{empresa}-{puesto}")
    return {
        "id": f"{now.strftime('%Y%m%d-%H%M%S-%f')[:19]}-{slug}",
        "fecha": now.strftime("%Y-%m-%d"),
        "empresa": empresa.strip() or "Empresa por confirmar",
        "puesto": puesto.strip() or "Puesto por analizar",
        "modalidad": modalidad.strip() or "Por confirmar",
        "url_oferta": _normalize_offer_url(url_oferta),
        "estado": "pendiente_ia",
        "viabilidad": "",
        "motivo_descarte": "",
        "horquilla_salarial": "",
        "carta_presentacion": "",
        "respuesta_situacion": "",
        "ruta_pdf_cv": "",
        "notas": notas.strip(),
        "descripcion": descripcion.strip(),
        "origen": origen,
        "fecha_aplicacion": "",
    }


def _check_gmail_credentials() -> tuple[str, str, Credentials | None]:
    if not CREDENTIALS_PATH.exists():
        return (
            "NO_CREDENTIALS",
            "Falta credentials.json en la raíz del proyecto.",
            None,
        )
    if not TOKEN_PATH.exists():
        return (
            "TOKEN_EXPIRED",
            "Sesión de Gmail no iniciada o expirada (token.json no encontrado).",
            None,
        )

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception:
        return (
            "TOKEN_EXPIRED",
            "El archivo token.json no es válido. Reactiva la sesión de Gmail.",
            None,
        )

    if creds.valid:
        return ("ACTIVO", "Sesión de Gmail activa (solo lectura).", creds)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            return ("ACTIVO", "Sesión de Gmail renovada y activa.", creds)
        except RefreshError:
            return (
                "TOKEN_EXPIRED",
                "El token OAuth en modo prueba (7 días) ha expirado o fue revocado.",
                None,
            )
        except Exception as exc:
            return (
                "TOKEN_EXPIRED",
                f"No se pudo renovar el token de Gmail ({exc}).",
                None,
            )

    return (
        "TOKEN_EXPIRED",
        "El token de Gmail ha caducado. Reactiva la sesión manualmente.",
        None,
    )


def _run_oauth_flow_sync() -> tuple[bool, str]:
    if not CREDENTIALS_PATH.exists():
        return False, "Falta credentials.json en la raíz del workspace."

    with _OAUTH_LOCK:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(
                port=0,
                prompt="consent",
                access_type="offline",
                open_browser=True,
            )
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            return True, "Sesión de Gmail reactivada correctamente."
        except Exception as exc:
            return False, f"No se completó la autenticación OAuth: {exc}"


def _decode_b64url(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode(
        "utf-8", errors="replace"
    )


def _extract_bodies(payload: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    mime = payload.get("mimeType", "")
    body_data = (payload.get("body") or {}).get("data")
    if body_data and mime in {"text/html", "text/plain", ""}:
        texts.append(_decode_b64url(body_data))

    for part in payload.get("parts") or []:
        texts.extend(_extract_bodies(part))
    return texts


def _extract_linkedin_urls_from_text(raw_text: str) -> list[str]:
    unescaped = html_lib.unescape(unquote(raw_text))
    found_ids: list[str] = []
    seen: set[str] = set()

    for match in LINKEDIN_JOB_RE.finditer(unescaped):
        job_id = match.group(1)
        if job_id not in seen:
            seen.add(job_id)
            found_ids.append(f"https://www.linkedin.com/jobs/view/{job_id}/")

    for match in LINKEDIN_TRACKED_REDIRECT_RE.finditer(unescaped):
        candidate = unquote(match.group(0))
        sub = LINKEDIN_JOB_RE.search(candidate)
        if sub:
            job_id = sub.group(1)
            if job_id not in seen:
                seen.add(job_id)
                found_ids.append(f"https://www.linkedin.com/jobs/view/{job_id}/")

    return found_ids


def _launch_persistent_browser(p: Any):
    """Abre el perfil persistente usando Google Chrome real si está disponible."""
    BROWSER_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    common_kwargs = {
        "user_data_dir": str(BROWSER_SESSION_DIR),
        "headless": False,
        "viewport": {"width": 1280, "height": 860},
        "ignore_default_args": ["--enable-automation"],
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    try:
        return p.chromium.launch_persistent_context(channel="chrome", **common_kwargs)
    except Exception:
        return p.chromium.launch_persistent_context(**common_kwargs)


def _scrape_linkedin_jobs_sync(urls: list[str]) -> tuple[list[dict[str, Any]], bool]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright no está instalado. Ejecuta 'pip install -r requirements.txt' y 'playwright install chromium'."
        ) from exc

    results: list[dict[str, Any]] = []
    authwall_detected = False

    with sync_playwright() as p:
        context = _launch_persistent_browser(p)
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(18000)

        try:
            for url in urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2200)

                    current_url = page.url.lower()
                    if any(
                        token in current_url
                        for token in ("/login", "/authwall", "/checkpoint", "/uas/")
                    ):
                        authwall_detected = True
                        results.append(
                            {
                                "url_oferta": url,
                                "puesto": "Oferta LinkedIn (requiere iniciar sesión)",
                                "empresa": "LinkedIn",
                                "modalidad": "Por confirmar",
                                "descripcion": (
                                    "LinkedIn solicitó inicio de sesión al abrir la oferta. "
                                    "Inicia sesión en la ventana del navegador persistente (./browser_session) "
                                    "o pega el texto manualmente desde el botón '+ Añadir oferta manual'."
                                ),
                                "authwall": True,
                            }
                        )
                        continue

                    data = page.evaluate(
                        """() => {
                          const pick = (selectors) => {
                            for (const sel of selectors) {
                              const el = document.querySelector(sel);
                              if (el && el.innerText && el.innerText.trim()) {
                                return el.innerText.trim();
                              }
                            }
                            return "";
                          };

                          const title = pick([
                            ".job-details-jobs-unified-top-card__job-title h1",
                            ".job-details-jobs-unified-top-card__job-title",
                            "h1.top-card-layout__title",
                            "h1.t-24",
                            "h1"
                          ]);

                          const company = pick([
                            ".job-details-jobs-unified-top-card__company-name a",
                            ".job-details-jobs-unified-top-card__company-name",
                            "a.topcard__org-name-link",
                            ".topcard__flavor-row .topcard__flavor"
                          ]);

                          const meta = pick([
                            ".job-details-jobs-unified-top-card__primary-description-container",
                            ".job-details-jobs-unified-top-card__tertiary-description-container",
                            ".topcard__flavor-row",
                            ".job-details-fit-level-preferences"
                          ]);

                          const description = pick([
                            ".jobs-description__content .jobs-box__html-content",
                            ".jobs-description-content__text",
                            ".jobs-description__content",
                            ".show-more-less-html__markup",
                            ".description__text"
                          ]);

                          return {
                            title,
                            company,
                            meta,
                            description,
                            docTitle: document.title || ""
                          };
                        }"""
                    )

                    puesto = data.get("title") or data.get("docTitle") or "Puesto LinkedIn"
                    empresa = data.get("company") or "Empresa por confirmar"
                    meta_text = data.get("meta") or ""
                    descripcion = data.get("description") or ""

                    modalidad = "Por confirmar"
                    meta_lower = f"{meta_text} {descripcion}".lower()
                    if any(w in meta_lower for w in ("en remoto", "100% remoto", "remoto", "remote")):
                        modalidad = "Remoto"
                    elif any(w in meta_lower for w in ("híbrido", "hibrido", "hybrid")):
                        modalidad = "Híbrido"
                    elif any(w in meta_lower for w in ("presencial", "on-site", "onsite")):
                        modalidad = "Presencial"

                    if meta_text and meta_text not in modalidad:
                        first_line = meta_text.splitlines()[0].strip()
                        if first_line and len(first_line) <= 70:
                            modalidad = f"{modalidad} · {first_line}" if modalidad != "Por confirmar" else first_line

                    results.append(
                        {
                            "url_oferta": url,
                            "puesto": puesto,
                            "empresa": empresa,
                            "modalidad": modalidad,
                            "descripcion": descripcion or meta_text,
                            "authwall": False,
                        }
                    )
                except Exception as exc:
                    results.append(
                        {
                            "url_oferta": url,
                            "puesto": "Oferta LinkedIn (error de lectura)",
                            "empresa": "LinkedIn",
                            "modalidad": "Por confirmar",
                            "descripcion": f"No se pudo extraer la descripción automáticamente: {exc}",
                            "authwall": False,
                        }
                    )
        finally:
            context.close()

    return results, authwall_detected


def _scan_gmail_and_linkedin_sync(creds: Credentials) -> dict[str, Any]:
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    list_resp = (
        service.users()
        .messages()
        .list(userId="me", q=GMAIL_QUERY, maxResults=25)
        .execute()
    )
    messages = list_resp.get("messages") or []

    discovered_urls: list[str] = []
    seen_urls: set[str] = set()

    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="full")
            .execute()
        )
        bodies = _extract_bodies(msg.get("payload") or {})
        for body in bodies:
            for url in _extract_linkedin_urls_from_text(body):
                if url not in seen_urls:
                    seen_urls.add(url)
                    discovered_urls.append(url)

    candidaturas = _load_candidaturas()
    existing_job_ids = {
        jid
        for item in candidaturas
        if (jid := _extract_linkedin_job_id(item.get("url_oferta", "")))
    }
    existing_urls = {
        _normalize_offer_url(item.get("url_oferta", ""))
        for item in candidaturas
        if item.get("url_oferta")
    }

    new_urls: list[str] = []
    for url in discovered_urls:
        jid = _extract_linkedin_job_id(url)
        if (jid and jid in existing_job_ids) or url in existing_urls:
            continue
        new_urls.append(url)

    if not new_urls:
        return {
            "ok": True,
            "correos_revisados": len(messages),
            "urls_detectadas": len(discovered_urls),
            "nuevas_anadidas": 0,
            "duplicadas_omitidas": len(discovered_urls),
            "authwall_detectado": False,
            "candidaturas": candidaturas,
        }

    scraped, authwall_detected = _scrape_linkedin_jobs_sync(new_urls)
    added_count = 0
    for item in scraped:
        entry = _new_candidatura(
            empresa=item["empresa"],
            puesto=item["puesto"],
            modalidad=item["modalidad"],
            url_oferta=item["url_oferta"],
            descripcion=item["descripcion"],
            origen="gmail+linkedin",
        )
        candidaturas.insert(0, entry)
        added_count += 1

    _save_candidaturas(candidaturas)

    return {
        "ok": True,
        "correos_revisados": len(messages),
        "urls_detectadas": len(discovered_urls),
        "nuevas_anadidas": added_count,
        "duplicadas_omitidas": len(discovered_urls) - len(new_urls),
        "authwall_detectado": authwall_detected,
        "candidaturas": candidaturas,
    }


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> HTMLResponse:
    if not DASHBOARD_PATH.exists():
        raise HTTPException(status_code=404, detail="No se encuentra dashboard.html")
    return HTMLResponse(DASHBOARD_PATH.read_text(encoding="utf-8"))


@app.get("/api/estado")
async def get_estado() -> JSONResponse:
    gmail_estado, gmail_mensaje, _ = await asyncio.to_thread(_check_gmail_credentials)
    candidaturas = _load_candidaturas()
    return JSONResponse(
        {
            "gmail_estado": gmail_estado,
            "gmail_mensaje": gmail_mensaje,
            "candidaturas": candidaturas,
            "conteos": _build_counts(candidaturas),
        }
    )


@app.post("/api/reauth")
async def post_reauth() -> JSONResponse:
    ok, message = await asyncio.to_thread(_run_oauth_flow_sync)
    if not ok:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "gmail_estado": "TOKEN_EXPIRED", "error": message},
        )
    return JSONResponse(
        {"ok": True, "gmail_estado": "ACTIVO", "gmail_mensaje": message}
    )


@app.post("/api/escanear-gmail")
async def post_escanear_gmail() -> JSONResponse:
    gmail_estado, gmail_mensaje, creds = await asyncio.to_thread(
        _check_gmail_credentials
    )
    if gmail_estado != "ACTIVO" or creds is None:
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "gmail_estado": gmail_estado,
                "error": gmail_mensaje,
            },
        )

    try:
        result = await asyncio.to_thread(_scan_gmail_and_linkedin_sync, creds)
        result["conteos"] = _build_counts(result["candidaturas"])
        return JSONResponse(result)
    except RefreshError:
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "gmail_estado": "TOKEN_EXPIRED",
                "error": "El token OAuth expiró durante la consulta. Pulsa 'Reactivar sesión de Gmail'.",
            },
        )
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "gmail_estado": "ACTIVO", "error": str(exc)},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "gmail_estado": gmail_estado,
                "error": f"Error al escanear Gmail/LinkedIn: {exc}",
            },
        )


@app.post("/api/oferta-manual")
async def post_oferta_manual(payload: OfertaManualPayload) -> JSONResponse:
    if not (payload.puesto.strip() or payload.descripcion.strip() or payload.url_oferta.strip()):
        raise HTTPException(
            status_code=400,
            detail="Debes indicar al menos el puesto, la URL o el texto de la oferta.",
        )

    candidaturas = _load_candidaturas()
    norm_url = _normalize_offer_url(payload.url_oferta)
    if norm_url:
        new_jid = _extract_linkedin_job_id(norm_url)
        for existing in candidaturas:
            existing_url = _normalize_offer_url(existing.get("url_oferta", ""))
            existing_jid = _extract_linkedin_job_id(existing_url)
            if (new_jid and existing_jid == new_jid) or (existing_url and existing_url == norm_url):
                raise HTTPException(
                    status_code=409,
                    detail="Esta URL de oferta ya existe en candidaturas.json.",
                )

    entry = _new_candidatura(
        empresa=payload.empresa,
        puesto=payload.puesto,
        modalidad=payload.modalidad,
        url_oferta=norm_url,
        descripcion=payload.descripcion,
        notas=payload.notas,
        origen="manual",
    )
    candidaturas.insert(0, entry)
    _save_candidaturas(candidaturas)

    return JSONResponse(
        {
            "ok": True,
            "candidatura": entry,
            "candidaturas": candidaturas,
            "conteos": _build_counts(candidaturas),
        }
    )


@app.post("/api/actualizar/{item_id}")
async def post_actualizar(item_id: str, payload: ActualizarPayload) -> JSONResponse:
    candidaturas = _load_candidaturas()
    target = next((item for item in candidaturas if item.get("id") == item_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Candidatura no encontrada.")

    if payload.estado is not None:
        if payload.estado not in VALID_ESTADOS:
            raise HTTPException(status_code=400, detail="Estado no válido.")
        target["estado"] = payload.estado
        if payload.estado == "aplicada" and not target.get("fecha_aplicacion"):
            target["fecha_aplicacion"] = date.today().isoformat()
        if payload.estado == "descartada" and not target.get("viabilidad"):
            target["viabilidad"] = "Descartada"

    if payload.notas is not None:
        target["notas"] = payload.notas.strip()

    if payload.motivo_descarte is not None:
        target["motivo_descarte"] = payload.motivo_descarte.strip()

    _save_candidaturas(candidaturas)
    return JSONResponse(
        {
            "ok": True,
            "candidatura": target,
            "candidaturas": candidaturas,
            "conteos": _build_counts(candidaturas),
        }
    )


@app.get("/api/cv/{item_id}")
async def get_cv_pdf(item_id: str) -> FileResponse:
    candidaturas = _load_candidaturas()
    target = next((item for item in candidaturas if item.get("id") == item_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Candidatura no encontrada.")

    ruta_rel = (target.get("ruta_pdf_cv") or "").strip()
    if not ruta_rel:
        raise HTTPException(
            status_code=404, detail="Esta candidatura aún no tiene un CV PDF asignado."
        )

    pdf_path = (BASE_DIR / ruta_rel).resolve()
    salidas_root = SALIDAS_DIR.resolve()
    if not pdf_path.is_relative_to(salidas_root) and pdf_path.parent != BASE_DIR.resolve():
        raise HTTPException(status_code=403, detail="Ruta de PDF no permitida.")

    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=404, detail=f"Archivo PDF no encontrado en {ruta_rel}"
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        content_disposition_type="inline",
    )


if __name__ == "__main__":
    _ensure_storage()
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="info")
