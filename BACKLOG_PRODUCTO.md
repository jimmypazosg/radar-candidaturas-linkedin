# BACKLOG_PRODUCTO.md — Triaje y Evolución hacia Servicio Gestionado / SaaS

Este documento separa qué mejoras se quedan únicamente en el uso local personal y cuáles forman parte del **núcleo de negocio** para las fases comerciales, operando un **Modelo Dual Concierge** sobre el mismo motor (ver [modelo-dual-concierge.md](docs/intent/modelo-dual-concierge.md)):

- **Fase 1A — Concierge Candidatos (B2C):** Operación asistida para candidatos reales usando perfiles aislados (`perfiles/<cliente>/`) para validar demanda, entregables y disposición a pagar.
- **Fase 1B — Concierge Empresas / Partners (B2B):** Operación asistida inversa para PYMEs sin RRHH técnico y consultores/agencias de selección usando procesos aislados (`clientes_b2b/<empresa>/<vacante>/`), entregando *Shortlist* + dossiers PDF A4 + guiones de entrevista.
- **Fase 2 — SaaS Multi-tenant (y futuro puente B2C↔B2B):** Plataforma web autoservicio para ambos lados del tablero.

---

## Regla de Triaje al desarrollar una nueva característica

Antes de implementar cualquier cambio, clasifícalo en uno de estos 3 cubos:

| Etiqueta | Criterio | Destino |
| :--- | :--- | :--- |
| **`[PERSONAL]`** | Depende de tu máquina, tu horario, tu sesión personal de Chrome/LinkedIn, scripts Windows (`.bat`) o reglas de vida concretas. | Se queda solo en tu entorno local. **No pasa al producto.** |
| **`[CORE / PRODUCTO]`** | Resuelve un problema universal de cualquier candidato (mejor parser, nueva vista, métricas, plantilla CV, flujo de evaluación). | Se implementa aquí desacoplado de datos personales **y se registra abajo** para llevarlo a Concierge/SaaS. |
| **`[EXPERIMENTAL]`** | Idea aún no validada (p. ej. automatización agresiva o integración experimental). | Se prueba primero en local; si aporta valor real tras 2 semanas de uso, se promueve a `[CORE / PRODUCTO]`. |

---

## Features `[CORE / PRODUCTO]` ya validadas en el núcleo

| ID | Capacidad | Estado en Base Actual | Notas para Fase 1 (Concierge) | Notas para Fase 2 (SaaS) |
| :--- | :--- | :--- | :--- | :--- |
| `CORE-01` | Separación de configuración por perfil (`config.local.json` / `RADAR_CONFIG`) | ✅ Implementado | Permite levantar una instancia aislada por cliente en `perfiles/<slug>/` | Equivalente a tabla `users` + `candidate_profiles` |
| `CORE-02` | Normalización y deduplicación de URLs de LinkedIn | ✅ Implementado (`app.py`) | Reutilizable tal cual | Reutilizable en backend Python/TS |
| `CORE-03` | Flujo de estados (`pendiente_ia` → `lista_para_aplicar` → `aplicada` / `cerrada` / `descartada`) con fecha de cierre para métricas de oportunidad | ✅ Implementado | Reutilizable tal cual | Reutilizable en esquema DB + analítica de tiempo de cierre |
| `CORE-04` | Rúbrica de evaluación, horquilla, carta, respuesta ATS y CV 1 pág. A4 | ✅ Implementado (`WORKFLOW_CANDIDATURA.md`) | Ejecutado por agente leyendo `perfil_maestro.md` del cliente | Convertir en *System Prompt* + *Structured Output* vía LLM API |
| `CORE-05` | Dashboard con copia en 1 clic y vista previa de materiales | ✅ Implementado (`dashboard.html`) | Puedes exportar o compartir el acceso/entregables al cliente | Frontend principal del usuario SaaS |
| `CORE-06` | Depuración por fases con `dry_run` (`POST /api/limpiar`) | ✅ Implementado | Mantiene ligero el almacenamiento por cliente | Job programado / retención en almacenamiento objeto (S3/R2) |

---

## Backlog pendiente para escalar (Registrar aquí nuevas ideas `[CORE / PRODUCTO]`)

### Para Fase 1A (Concierge Candidatos — B2C)
- [ ] **Generador de pack de entrega para cliente:** Exportar en 1 clic un ZIP o resumen Markdown/HTML con las ofertas `lista_para_aplicar` del día (enlaces, horquilla, carta, respuesta y PDFs) para enviárselo al cliente sin darle acceso a tu localhost.
- [ ] **Script/comando de alta rápida de cliente:** Crear carpeta `perfiles/<slug>/` con `config.json`, `perfil_maestro.md`, `plantilla_cv.html` y `candidaturas.json` inicializados.
- [ ] **Soporte de múltiples portales en alta manual:** Campos o parsers ligeros para InfoJobs, Manfred, Otta/Welcome to the Jungle, además de LinkedIn.

### Para Fase 1B (Concierge Empresas / Partners — B2B)
- [x] **Especificación y plantillas base B2B:** `docs/specs/b2b-concierge-spec.md`, `vacante_maestra.example.md`, `WORKFLOW_SELECCION.md`, `plantilla_dossier_candidato.html` y `candidatos.example.json`.
- [ ] **Ingesta masiva de CVs en PDF/TXT:** Script o endpoint en `app.py` para extraer texto de una carpeta `entrada_cvs/` hacia `candidatos.json` en estado `pendiente_ia`.
- [ ] **Generador de `shortlist_cliente.html` / Pack ZIP B2B:** Vista HTML estática autocontenida con tabla comparativa del Top 5–8 y enlaces relativos a los dossiers PDF (soporte marca blanca para partners/consultores).
- [ ] **Script de alta rápida de vacante B2B:** Crear carpeta `clientes_b2b/<empresa_slug>/<vacante_slug>/` inicializada desde las plantillas base.

### Para Fase 2 (Transición a SaaS Multi-tenant)
- [ ] **Motor IA en backend (LLM API):** Sustituir la ejecución manual vía agente IDE por llamadas a API (Gemini/OpenAI/Anthropic) con generación JSON estricta y control de coste por usuario.
- [ ] **Ingesta sin scraping desde servidor cloud:** Extensión de navegador (Chrome) o pegado de texto/URL asistido por el usuario (evita bloqueos de IP y riesgos ToS de LinkedIn en servidores compartidos).
- [ ] **Compilador PDF multiplataforma (Linux/Docker):** Reemplazar `compilar_pdf.bat` por Playwright PDF / Chromium headless / WeasyPrint en worker asíncrono.
- [ ] **Persistencia multiusuario + Auth + Billing:** PostgreSQL (o Supabase), autenticación OAuth/Email, almacenamiento de PDFs por usuario y suscripción/créditos (Stripe).
