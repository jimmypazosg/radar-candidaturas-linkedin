# Declaración de Intención: Modelo Dual Concierge (`radar-candidaturas`)

**Fecha de confirmación:** 2026-11-14  
**Estado:** Confirmado  

## 1. Resultado (Outcome)
Operar **dos servicios Concierge paralelos** sobre el mismo núcleo tecnológico de [radar-candidaturas](../../README.md):

1. **Concierge Candidatos (B2C — ya iniciado):** Recibir el perfil del candidato (`perfil_maestro.md`), filtrar ofertas y entregarle cada candidatura lista para aplicar (evaluación de viabilidad, horquilla salarial, carta de presentación, respuesta ATS y CV adaptado en PDF A4).
2. **Concierge Empresas / Partners (B2B — expansión):** Recibir una vacante (`vacante_maestra.md`) y los CVs captados por el cliente, y entregar en 48h un *Shortlist* de finalistas con ficha ejecutiva PDF A4 por candidato, banderas rojas y guion de entrevista personalizado.

## 2. Cliente Ideal (ICP)
- **Lado B2C:** Profesionales cualificados en búsqueda activa que priorizan calidad, criterio y personalización sobre el envío masivo.
- **Lado B2B (dos vías complementarias):**
  - *Entrada directa:* PYMEs y startups sin RRHH técnico (5–60 personas) con alto dolor para filtrar perfiles técnicos, digitales o de producto (ticket por vacante: `350–500 €`).
  - *Recurrencia mensual / Alianzas:* Consultores independientes, coaches ejecutivos, agencias y recruiters freelance que ya asesoran a empresarios y nos usan como brazo operativo de triaje y generación de dossiers (retainer mensual `~490 €/mes`, incluyendo puestos de negocio cuando el partner aporta el criterio de dominio).

## 3. Por qué ahora
Ambas caras comparten exactamente la misma arquitectura base ya construida (ingesta estructurada, ciclo de estados en JSON, evaluación agéntica mediante rúbrica en Markdown y compilación HTML→PDF A4), lo que permite monetizar el lado B2B rápidamente antes de invertir en un SaaS multi-tenant.

## 4. Criterio de Éxito
- Validar ambos servicios con primeros clientes reales de pago (packs por proceso y retainers mensuales recurrentes en B2B).
- Mantener la operabilidad ligera desde el repositorio antes de migrar a SaaS, sentando las bases para conectar ambos lados del tablero a medio plazo.

## 5. Restricciones Clave
- Operación aislada por cliente (`perfiles/<cliente>/` en B2C y `clientes_b2b/<empresa>/<vacante>/` en B2B).
- Cero fricción técnica para el cliente final (sin instalarle herramientas locales ni obligarle a migrar su ATS).
- Priorizar recurrencia mensual (partners/agencias/empresas con contratación recurrente) sobre tickets sueltos.

## 6. Fuera de Alcance (por ahora)
- No hacer *sourcing* / búsqueda activa de candidatos en B2B (el cliente aporta los CVs o URLs recibidos).
- No construir un ATS completo ni una plataforma SaaS multi-tenant todavía.
- No evaluar puestos no técnicos (p. ej. gerencia, industrial, ventas puras) sin un partner o cliente que defina y valide el criterio de dominio.
