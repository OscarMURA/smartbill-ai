# Contribuir a SmartBill AI

Gracias por contribuir. SmartBill AI es un prototipo personal e independiente para explorar la lectura y explicación de facturas de gas con datos estructurados.

## Antes de proponer un cambio

- Revisa [la especificación](docs/SMARTBILL_SPEC.md), el plan de implementación y las decisiones registradas en [docs/DECISIONS.md](docs/DECISIONS.md).
- Para cambios de alcance o de contrato, abre primero una discusión o issue y describe el problema y la solución propuesta.
- Mantén los cambios acotados y documenta las limitaciones relevantes.

## Privacidad de datos de ejemplo

Usa exclusivamente datos y documentos sintéticos, claramente rotulados como demostración. No subas facturas reales, nombres, direcciones, números de cuenta, identificadores ni otros datos personales a issues, pull requests, fixtures, capturas o logs. Las contribuciones a parsers deben incluir un ejemplo sintético y pruebas que no dependan de información de clientes.

## Pull requests

1. Crea una rama para el cambio y explica qué problema resuelve.
2. Incluye pruebas o actualiza las existentes cuando el cambio afecte comportamiento.
3. Ejecuta las comprobaciones pertinentes disponibles en el proyecto y anota los comandos y resultados reales. No declares pruebas exitosas si no las ejecutaste.
4. Actualiza la documentación afectada y señala cualquier decisión o limitación nueva.
5. Envía el pull request con un resumen, validación ejecutada y riesgos conocidos.

No envíes secretos, claves de API, PDFs originales ni archivos `.env` con credenciales. No publiques ni despliegues cambios en nombre del proyecto.

## Alcance y seguridad

Las variaciones son heurísticas de demostración y no constituyen criterios oficiales de Gases de Occidente (GdO), diagnóstico técnico ni detección de fugas. No atribuyas causas que los datos no demuestran. Para vulnerabilidades, sigue [SECURITY.md](SECURITY.md); no las reportes públicamente.

Se espera que toda participación respete el [Código de conducta](CODE_OF_CONDUCT.md).
