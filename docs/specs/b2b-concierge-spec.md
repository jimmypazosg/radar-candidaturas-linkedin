# Especificación Funcional y Técnica — Módulo Concierge B2B (`clientes_b2b/`)

> **Objetivo:** Habilitar el flujo inverso de [radar-candidaturas](../../README.md) para evaluar lotes de candidatos frente a una vacante real y entregar un *Shortlist* ejecutivo con fichas PDF A4 y guiones de entrevista personalizados, sin afectar el flujo B2C actual (`app.py`, `candidaturas.json`).

---

## 1. Estructura Aislada por Proceso B2B

Cada empresa y vacante opera en su propia carpeta bajo `clientes_b2b/` (excluida de Git en `.gitignore`):

```text
clientes_b2b/
└── <empresa_slug>/
    └── <vacante_slug>/
        ├── config.json              # Metadatos del cliente, marca blanca, idioma y pesos
        ├── vacante_maestra.md       # Requisitos, dealbreakers, cultura y criterios de dominio
        ├── candidatos.json          # Registro de candidatos evaluables (esquema definido abajo)
        ├── entrada_cvs/             # CVs originales en PDF/TXT/MD o texto capturado de LinkedIn
        └── salidas_b2b/             # Carpetas por finalista (dossier HTML + PDF A4) y shortlist_cliente.html
```

---

## 2. Contrato de `config.json` (Proceso B2B)

```json
{
  "cliente_nombre": "Empresa o Partner",
  "vacante_titulo": "Backend Python Senior",
  "modo_servicio": "directo_pyme",
  "marca_blanca_partner": "",
  "idioma_entregable": "es",
  "top_shortlist_max": 7,
  "pesos_score": {
    "evidencia_tecnica": 40,
    "experiencia_relevante": 25,
    "estabilidad_trayectoria": 20,
    "encaje_logistico_salarial": 15
  }
}
```

- `modo_servicio`: `"directo_pyme"` (evaluación para fundador/manager no técnico) o `"partner_consultor"` (co-evaluación con consultor/coach de negocio que aporta criterio de dominio).
- `marca_blanca_partner`: Si tiene valor, sustituye la firma del dossier por el nombre del consultor/agencia partner.

---

## 3. Contrato de `candidatos.json`

Array de objetos (inicializado desde [candidatos.example.json](../../candidatos.example.json)):

### Ciclo de estados (`estado`)
| Estado | Significado |
| :--- | :--- |
| `pendiente_ia` | Candidato recién ingerido (CV en texto/PDF o perfil LinkedIn) pendiente de evaluación. |
| `shortlist_top` | Finalista recomendado para entrevista (cuenta con Dossier PDF A4 generado). |
| `reserva` | Perfil viable con algún gap secundario; útil si caen finalistas del Top. |
| `descartado` | No supera los criterios eliminatorios (*dealbreakers*) o queda lejos del corte. |
| `entrevista_agendada` | El cliente ha citado al candidato (actualización manual de seguimiento). |
| `finalista` | Candidato avanzado tras entrevista con el cliente. |

### Campos por registro
```json
{
  "id": "20261114-143000-001-ana-lopez",
  "fecha_ingesta": "2026-11-14",
  "nombre": "Ana López",
  "titular_actual": "Senior Python Engineer",
  "ubicacion_modalidad": "Madrid · Híbrido / Remoto",
  "fuente": "pdf_local",
  "archivo_cv": "entrada_cvs/ana_lopez.pdf",
  "url_perfil": "https://www.linkedin.com/in/ejemplo/",
  "estado": "pendiente_ia",
  "score_total": 0,
  "desglose_score": {
    "evidencia_tecnica": 0,
    "experiencia_relevante": 0,
    "estabilidad_trayectoria": 0,
    "encaje_logistico_salarial": 0
  },
  "veredicto": "",
  "motivo_descarte": "",
  "fortalezas_clave": [],
  "banderas_rojas": [],
  "preguntas_entrevista": [],
  "ruta_pdf_dossier": "",
  "notas_cliente": "",
  "texto_cv": ""
}
```

---

## 4. Reglas de Evaluación y Principios de Calidad

1. **Separación estricta entre Evidencia y Afirmación:** Un CV que solo lista palabras clave sin contexto de proyectos, responsabilidades o métricas reales no puede puntuar alto en `evidencia_tecnica` ni `experiencia_relevante`.
2. **Lenguaje accionable para el decisor:** En `modo_servicio: "directo_pyme"`, explicar cada fortaleza y riesgo en impacto de negocio comprensible para un fundador no técnico (evitar jerga sin traducir).
3. **Veracidad total:** No inferir ni inventar logros, salarios o fechas que no figuren en el CV o notas de pre-screening. Si falta información crítica (p. ej. expectativa salarial o nivel real de inglés), marcarlo explícitamente en `banderas_rojas` como **"Incógnita a validar en entrevista"**.
4. **Dossier de 1 sola página A4:** Todo finalista en `shortlist_top` recibe su ficha HTML→PDF (`210mm x 297mm`, `overflow: hidden`) compilada mediante [compilar_pdf.bat](../../compilar_pdf.bat) a partir de [plantilla_dossier_candidato.html](../../plantilla_dossier_candidato.html).

---

## 5. Evolución por Fases (sin sobre-ingeniería)

1. **Iteración 1 (Actual — Operación Agéntica):** Plantillas base (`vacante_maestra.example.md`, `WORKFLOW_SELECCION.md`, `plantilla_dossier_candidato.html`, `candidatos.example.json`) ejecutadas por el agente en workspace para validar con los primeros procesos reales.
2. **Iteración 2 (Ingesta + Empaquetado):** Extractor automático de carpeta de PDFs (`entrada_cvs/` → `candidatos.json`) y generador estático `shortlist_cliente.html` + ZIP exportable.
3. **Iteración 3 (Dashboard B2B / SaaS):** Vista dedicada o pestaña B2B en el dashboard web y ejecución vía LLM API.
