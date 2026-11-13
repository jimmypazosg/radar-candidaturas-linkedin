# WORKFLOW_CANDIDATURA.md — Reglas Operativas para Antigravity

Este documento define el procedimiento estándar que debe ejecutar el agente cada vez que el usuario escriba:
> **"Procesa las ofertas pendientes"**

---

## 1. Lectura inicial obligatoria
1. Leer `candidaturas.json` y filtrar todas las entradas cuyo campo `"estado"` sea exactamente `"pendiente_ia"`.
2. Leer `perfil_maestro.md` para contrastar experiencia real, stack, ubicación, idiomas y criterios salariales.
3. Leer `plantilla_cv.html` como base única para maquetar los CVs adaptados.

Si no hay ofertas con `estado == "pendiente_ia"`, informar al usuario y finalizar sin modificar archivos.

---

## 2. Evaluación de viabilidad real en España
Analizar la descripción, empresa, puesto y modalidad de cada oferta pendiente aplicando las reglas de `perfil_maestro.md`:

### Descarte automático (`estado = "descartada"`, `viabilidad = "Descartada"`)
Descartar inmediatamente y rellenar `motivo_descarte` de forma concreta cuando ocurra cualquiera de estos supuestos:
- Becas, prácticas universitarias o perfiles junior/entry-level.
- Puestos **100 % presenciales** (o híbridos de alta presencialidad) **fuera de Salamanca** con salario bajo o estándar que no justifique traslado.
- Stacks técnicos incompatibles sin solapamiento real con el perfil (ej. SAP/ABAP, COBOL, C++ embebido, desarrollo móvil nativo exclusivo, Java/Spring o .NET puro sin componente UX/UI/Frontend/Web).
- Ofertas a **jornada completa** con banda salarial publicada manifiestamente precaria (**< 22.000 € brutos/año**). *(No descartar automáticamente presupuestos moderados de 24.000 € – 35.000 € ni opciones part-time/mañanas si son 100 % remotos y compatibles con la disponibilidad de mañana de 08:30 a 16:30/17:00 CET).*
- Ofertas sin información suficiente por authwall que el usuario aún no haya completado (si `descripcion` indica bloqueo de login, dejar constancia o pedir texto antes de descartar si la empresa/puesto prometen).

### Ofertas viables (`viabilidad = "Alta"` o `"Media"`)
- **`Alta`:** 100 % remoto (España, UE o EE. UU.) o Salamanca, con encaje directo en UX/UI Design Technologist, Frontend HTML5/CSS3/JS, Design Systems, WordPress/PHP Senior, CRO/SEO técnico o Automatización IA/Web.
- **`Media`:** Remoto o híbrido compatible donde exista solapamiento sólido en UX/Frontend/Producto, aunque pida un framework secundario complementario (p. ej. React/Vue/TypeScript) que no invalide el valor senior del perfil.

---

## 3. Generación de materiales para cada oferta viable (`Alta` o `Media`)
Por cada oferta viable, ejecutar en orden:

1. **Calcular horquilla salarial (`horquilla_salarial`)** en **€ brutos/año** realista para España en 2026:
   - Nacional España (presupuesto ajustado/flexible o entrada): `26.000 € – 36.000 € brutos/año` (o proporcional si es part-time/mañanas).
   - Nacional España (Senior): `38.000 € – 52.000 € brutos/año` según tamaño de empresa y responsabilidad.
   - Internacional / SaaS remoto: `48.000 € – 65.000 € brutos/año`.
   - Si la oferta publica una horquilla superior compatible, alinear la propuesta con ella sin infravalorarse.

2. **Redactar respuesta de situación actual (`respuesta_situacion`)**:
   - Texto breve en primera persona (3–5 líneas) listo para pegar en formularios de LinkedIn/ATS:
     - Explica la situación actual en activo en **Land Gorilla Inc.** (entorno SaaS B2B internacional en modalidad 100 % remota, horario EE. UU. a partir de las 17:00–18:00 hora de Madrid, con disponibilidad completa por las mañanas) y consultoría web/IA propia (`apisdev.com`).
     - Indica residencia estable en Salamanca (España), disponibilidad para remoto 100 %, nivel profesional en inglés y español, y motivación alineada con la empresa/vacante.

3. **Redactar carta de presentación (`carta_presentacion`)**:
   - Concisa, directa, sin tópicos vacíos (150–220 palabras).
   - Conecta 2–3 necesidades explícitas de la oferta con logros reales de `perfil_maestro.md` (sin inventar experiencia ni tecnologías no cursadas).

4. **Crear carpeta de salida única**:
   - Formato: `salidas/YYYY-MM-DD_<slug-empresa>-<slug-puesto>/` (todo en minúsculas, ASCII sin tildes ni caracteres especiales, guiones simples).

5. **Generar `cv_adaptado.html`**:
   - Basado en `plantilla_cv.html`.
   - Mantener estrictamente **1 sola página A4 (`210mm x 297mm`, `overflow: hidden`)**.
   - Adaptar:
     - El titular bajo el nombre para reflejar el rol objetivo de la oferta.
     - El resumen ejecutivo (3–4 líneas) destacando las palabras clave exactas de la vacante.
     - El orden de las especialidades y las viñetas de experiencia de Land Gorilla Inc. y `apisdev.com` para priorizar lo que busca el reclutador (manteniendo 100 % veracidad con `perfil_maestro.md`).

6. **Compilar `CV_Jimmy_Pazos.pdf` y verificar**:
   - Ejecutar desde la raíz del workspace:
     ```bat
     compilar_pdf.bat "salidas\YYYY-MM-DD_empresa-puesto\cv_adaptado.html" "salidas\YYYY-MM-DD_empresa-puesto\CV_Jimmy_Pazos.pdf"
     ```
   - Comprobar que `CV_Jimmy_Pazos.pdf` existe y, si el lector de archivos está disponible, verificar visualmente que cabe en **1 sola página A4** sin texto cortado ni desbordamientos.

7. **Actualizar `candidaturas.json`**:
   - Cambiar `"estado"` a `"lista_para_aplicar"`.
   - Rellenar `"viabilidad"` (`"Alta"` o `"Media"`), `"motivo_descarte"` (`""`), `"horquilla_salarial"`, `"respuesta_situacion"`, `"carta_presentacion"`, y `"ruta_pdf_cv"` con la ruta relativa exacta en formato POSIX:
     `salidas/YYYY-MM-DD_empresa-puesto/CV_Jimmy_Pazos.pdf`.

---

## 4. Reglas de integridad
- **No inventar nunca** experiencia, títulos, empresas, métricas ni dominio de frameworks que no figuren en `perfil_maestro.md`.
- **No modificar** candidaturas que ya estén en estado `"aplicada"` o `"descartada"`, salvo indicación explícita del usuario.
- **No sobrescribir** el campo `"notas"` del usuario si ya contiene texto; en todo caso conservarlo intacto.
- Al terminar el lote, presentar al usuario un resumen claro con las ofertas listas para aplicar, las descartadas (con su motivo) y recordar que ya puede revisarlas y copiar todo en 1 clic desde `http://localhost:8090`.
