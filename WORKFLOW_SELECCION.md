# WORKFLOW_SELECCION.md — Reglas Operativas B2B (Concierge Empresas y Partners)

Este documento define el procedimiento estándar del **lado B2B** que debe ejecutar el agente cada vez que el usuario escriba:
> **"Procesa los candidatos pendientes de `<empresa>/<vacante>`"** *(indicando la ruta dentro de `clientes_b2b/`)*

---

## 1. Lectura inicial obligatoria
1. Verificar la carpeta del proceso `<vacante_dir> = clientes_b2b/<empresa_slug>/<vacante_slug>/`.
2. Leer `<vacante_dir>/config.json` (pesos de puntuación, `top_shortlist_max`, `modo_servicio`, `marca_blanca_partner`).
3. Leer `<vacante_dir>/vacante_maestra.md` para obtener contexto de negocio, *must-have / dealbreakers*, *nice-to-have*, banderas rojas y criterios de puntuación.
4. Leer `<vacante_dir>/candidatos.json` y filtrar todas las entradas cuyo campo `"estado"` sea exactamente `"pendiente_ia"`.
   - Si el campo `"texto_cv"` está vacío pero existe `"archivo_cv"`, leer primero el archivo correspondiente dentro de `<vacante_dir>/entrada_cvs/`.
5. Leer la plantilla base `plantilla_dossier_candidato.html` en la raíz (o `<vacante_dir>/plantilla_dossier_candidato.html` si existe una personalizada).

Si no hay candidatos con `estado == "pendiente_ia"`, informar al usuario y finalizar sin modificar archivos.

---

## 2. Evaluación y Scoring según `vacante_maestra.md`

Analizar cada candidato pendiente con criterio **basado en evidencias** (no por simple coincidencia de palabras clave):

### A. Filtro eliminatorio (`estado = "descartado"`)
Descartar inmediatamente y rellenar `"motivo_descarte"` de forma objetiva y trazable si incumple alguno de los **Requisitos Eliminatorios (*Dealbreakers*)** definidos en `vacante_maestra.md`.
- Asignar `score_total` calculado igualmente (o `0` si el descarte es puramente logístico/eliminatorio previo) y `veredicto = "Descartado"`.

### B. Evaluación por 4 ejes (para candidatos que superan el filtro eliminatorio)
Puntuar respetando los pesos de `config.json` / `vacante_maestra.md` (suma máxima = 100):
1. `evidencia_tecnica` (por defecto `/40`): ¿Muestra proyectos concretos, arquitectura, decisiones técnicas o métricas reales, o solo lista *buzzwords*?
2. `experiencia_relevante` (por defecto `/25`): ¿Ha trabajado en un entorno, escala o tipo de producto/negocio comparable al del cliente?
3. `estabilidad_trayectoria` (por defecto `/20`): Coherencia temporal, progresión y ausencia de saltos injustificados.
4. `encaje_logistico_salarial` (por defecto `/15`): Ubicación, modalidad, idiomas y alineación con la banda.

### C. Clasificación de corte
Ordenar los candidatos evaluados por `score_total` descendente y asignar:
- **`shortlist_top`** (`veredicto = "Recomendado"` o `"Top Finalista"`): Los mejores perfiles hasta el límite `top_shortlist_max` (habitualmente 5–7), siempre que superen un umbral mínimo razonable (≥ 65/100).
- **`reserva`** (`veredicto = "Reserva"`): Candidatos sólidos (habitualmente 50–64/100 o fuera del cupo Top) útiles como respaldo.
- **`descartado`** (`veredicto = "No encaja"`): Resto por debajo del umbral, indicando el motivo principal en `"motivo_descarte"`.

---

## 3. Generación de Entregables para cada candidato en `shortlist_top`

Por cada candidato clasificado en `shortlist_top`, generar en orden:

1. **Bloque "Por qué sí" (`fortalezas_clave`, 3–4 puntos):**
   - Cada punto debe citar una **evidencia real del CV** y explicar su impacto para el negocio en lenguaje claro (especialmente en `modo_servicio = "directo_pyme"`, traduciendo la jerga técnica a valor práctico para el fundador/manager).
2. **Bloque "Banderas rojas e Incógnitas" (`banderas_rojas`, 2–4 puntos):**
   - Señalar gaps respecto a `vacante_maestra.md`, saltos temporales, falta de métricas o **datos críticos no declarados** (p. ej. `"Expectativa salarial no indicada en CV — validar en el primer contacto"`).
3. **Guion de Entrevista Personalizado (`preguntas_entrevista`, exactamente 5 preguntas):**
   - Preguntas diseñadas específicamente sobre proyectos, huecos o afirmaciones del CV de *ese* candidato (nunca preguntas genéricas de manual).
   - Cada pregunta incluye:
     - La pregunta literal para el entrevistador.
     - **Qué buscar:** qué responde un candidato sólido frente a una respuesta superficial o evasiva.
4. **Crear carpeta y maquetar `dossier.html`:**
   - Carpeta: `<vacante_dir>/salidas_b2b/dossier_<slug-candidato>/` (minúsculas, ASCII sin tildes).
   - Basado en `plantilla_dossier_candidato.html`.
   - Mantener estrictamente **1 sola página A4 (`210mm x 297mm`, `overflow: hidden`)**.
   - Si `marca_blanca_partner` tiene valor en `config.json`, usarlo en la firma/pie del documento.
5. **Compilar PDF y verificar:**
   - Ejecutar desde la raíz del workspace:
     ```bat
     compilar_pdf.bat "<vacante_dir>\salidas_b2b\dossier_<slug-candidato>\dossier.html" "<vacante_dir>\salidas_b2b\dossier_<slug-candidato>\Dossier_<slug-candidato>.pdf"
     ```
   - Comprobar que el PDF existe y cabe en **1 sola página A4** sin texto cortado.
6. **Actualizar `<vacante_dir>/candidatos.json`:**
   - Guardar `estado`, `score_total`, `desglose_score`, `veredicto`, `motivo_descarte`, `fortalezas_clave`, `banderas_rojas`, `preguntas_entrevista` y `ruta_pdf_dossier` (ruta relativa POSIX respecto a `<vacante_dir>`).

---

## 4. Reglas de Integridad
- **No inventar nunca** experiencia, años, tecnologías, empresas ni expectativas salariales que no figuren en el CV o en notas verificadas del proceso.
- **No modificar** candidatos que ya estén en estado `"entrevista_agendada"` o `"finalista"`, salvo indicación explícita del usuario.
- **No sobrescribir** `"notas_cliente"` si ya contiene texto.
- Al terminar el lote, presentar un resumen ejecutivo al usuario con: total evaluados, listado ordenado del `shortlist_top` (nombre, score y titular), reservas y resumen de descartes con motivo.
