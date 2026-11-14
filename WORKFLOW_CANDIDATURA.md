# WORKFLOW_CANDIDATURA.md — Reglas Operativas del Núcleo para Antigravity

Este documento define el procedimiento estándar del **núcleo del negocio** que debe ejecutar el agente cada vez que el usuario escriba:
> **"Procesa las ofertas pendientes"** *(o indique procesar un perfil concreto en `perfiles/<cliente>/`)*

---

## 1. Lectura inicial obligatoria
1. Leer la configuración activa del workspace:
   - `config.local.json` si existe (o la ruta indicada por el usuario en `perfiles/<cliente>/config.json`); en su defecto, `config.example.json`.
   - Extraer `data_dir` (por defecto `.`), `cv_pdf_filename` (por defecto `CV_Adaptado.pdf`) y `owner_name`.
2. Leer `<data_dir>/candidaturas.json` y filtrar todas las entradas cuyo campo `"estado"` sea exactamente `"pendiente_ia"`.
3. Leer el perfil maestro del candidato (`perfil_maestro.md` en la raíz o `<data_dir>/perfil_maestro.md` si el perfil tiene uno propio) para contrastar experiencia real, stack, ubicación, idiomas, disponibilidad y criterios salariales/de descarte.
4. Leer la plantilla de CV (`plantilla_cv.html` en la raíz o `<data_dir>/plantilla_cv.html` si existe) como base única para maquetar los CVs adaptados.

Si no hay ofertas con `estado == "pendiente_ia"`, informar al usuario y finalizar sin modificar archivos.

---

## 2. Evaluación de viabilidad según `perfil_maestro.md`
Analizar la descripción, empresa, puesto y modalidad de cada oferta pendiente aplicando **estrictamente** los criterios y restricciones definidos en el `perfil_maestro.md` activo:

### Descarte automático (`estado = "descartada"`, `viabilidad = "Descartada"`)
Descartar inmediatamente y rellenar `motivo_descarte` de forma concreta cuando ocurra cualquiera de los supuestos marcados en `perfil_maestro.md` (por ejemplo: nivel junior/prácticas si el perfil es senior, presencialidad incompatible sin encaje que justifique propuesta remota, stacks núcleo sin solapamiento real, o banda salarial publicada por debajo del mínimo aceptable).
- **Excepción por authwall:** Si `descripcion` indica bloqueo de login/información insuficiente y la empresa o puesto prometen, dejar constancia antes de descartar salvo indicación del usuario.

### Ofertas viables (`viabilidad = "Alta"` o `"Media"`)
- **`Alta`:** Modalidad y ubicación compatibles según `perfil_maestro.md`, con encaje directo en los roles objetivo y stack principal del candidato.
- **`Media`:**
  - Solapamiento sólido con el núcleo del perfil aunque pida herramientas secundarias complementarias o presupueste una banda moderada dentro del rango flexible definido en `perfil_maestro.md`.
  - **Estrategia Propuesta Remoto (si aplica según el perfil):** Si una oferta presencial/híbrida fuera de la ciudad del candidato cumple claramente su perfil técnico y el `perfil_maestro.md` contempla proponer remoto, no descartarla: clasificarla como `Media` y argumentar en `carta_presentacion` y `respuesta_situacion` la colaboración **100 % remota** respaldada por su experiencia remota previa.

---

## 3. Generación de materiales para cada oferta viable (`Alta` o `Media`)
Por cada oferta viable, ejecutar en orden:

1. **Calcular horquilla salarial (`horquilla_salarial`)**:
   - Usar las referencias y tramos salariales definidos en `perfil_maestro.md` (adaptados a mercado nacional vs. internacional/remoto o dedicación parcial si aplica).
   - Si la oferta publica una horquilla superior compatible, alinear la propuesta con ella sin infravalorarse.

2. **Redactar respuesta de situación actual (`respuesta_situacion`)**:
   - Texto breve en primera persona (3–5 líneas) listo para pegar en formularios de LinkedIn/ATS, basado exclusivamente en la sección de disponibilidad, situación actual, ubicación e idiomas de `perfil_maestro.md`, y alineado con la vacante.

3. **Redactar carta de presentación (`carta_presentacion`)**:
   - Concisa, directa, sin tópicos vacíos (150–220 palabras).
   - Conecta 2–3 necesidades explícitas de la oferta con logros reales de `perfil_maestro.md` (sin inventar experiencia ni tecnologías no cursadas).

4. **Crear carpeta de salida única**:
   - Formato: `<data_dir>/salidas/YYYY-MM-DD_<slug-empresa>-<slug-puesto>/` (todo en minúsculas, ASCII sin tildes ni caracteres especiales, guiones simples).

5. **Generar `cv_adaptado.html`**:
   - Basado en la `plantilla_cv.html` activa.
   - Mantener estrictamente **1 sola página A4 (`210mm x 297mm`, `overflow: hidden`)**.
   - Adaptar:
     - El titular bajo el nombre para reflejar el rol objetivo de la oferta.
     - El resumen ejecutivo (3–4 líneas) destacando las palabras clave exactas de la vacante.
     - El orden de las especialidades y las viñetas de experiencia para priorizar lo que busca el reclutador (manteniendo 100 % veracidad con `perfil_maestro.md`).

6. **Compilar `<cv_pdf_filename>` y verificar**:
   - Ejecutar desde la raíz del workspace usando el nombre definido en `cv_pdf_filename` de la configuración activa (p. ej. `CV_Jimmy_Pazos.pdf` o `CV_Adaptado.pdf`):
     ```bat
     compilar_pdf.bat "<data_dir>\salidas\YYYY-MM-DD_empresa-puesto\cv_adaptado.html" "<data_dir>\salidas\YYYY-MM-DD_empresa-puesto\<cv_pdf_filename>"
     ```
   - Comprobar que el PDF existe y, si el lector de archivos está disponible, verificar visualmente que cabe en **1 sola página A4** sin texto cortado ni desbordamientos.

7. **Actualizar `<data_dir>/candidaturas.json`**:
   - Cambiar `"estado"` a `"lista_para_aplicar"`.
   - Rellenar `"viabilidad"` (`"Alta"` o `"Media"`), `"motivo_descarte"` (`""`), `"horquilla_salarial"`, `"respuesta_situacion"`, `"carta_presentacion"`, y `"ruta_pdf_cv"` con la ruta relativa exacta **respecto a `data_dir`** en formato POSIX:
     `salidas/YYYY-MM-DD_empresa-puesto/<cv_pdf_filename>`.

---

## 4. Reglas de integridad
- **No inventar nunca** experiencia, títulos, empresas, métricas ni dominio de herramientas que no figuren en `perfil_maestro.md`.
- **No modificar** candidaturas que ya estén en estado `"aplicada"`, `"cerrada"` o `"descartada"`, salvo indicación explícita del usuario.
- **No sobrescribir** el campo `"notas"` del usuario si ya contiene texto; en todo caso conservarlo intacto.
- Al terminar el lote, presentar al usuario un resumen claro con las ofertas listas para aplicar, las descartadas (con su motivo) y recordar que ya puede revisarlas y copiar todo en 1 clic desde el dashboard local.
