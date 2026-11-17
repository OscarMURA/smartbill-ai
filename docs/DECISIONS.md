# Registro de decisiones

Este registro recoge decisiones de diseño establecidas en la especificación y el plan del MVP. Describe el fundamento del diseño; no afirma por sí solo que las funciones estén implementadas o validadas.

## D1. Proyecto independiente y demo sintética

SmartBill AI es un proyecto personal de portafolio, independiente y no oficial de Gases de Occidente (GdO). No representa a GdO, no tiene aval ni integración con sus sistemas. La demostración utiliza facturas y cifras sintéticas, rotuladas como tales; no deben usarse facturas reales en ejemplos públicos.

## D2. Alcance acotado al análisis explicable

El objetivo del MVP es extraer campos visibles, comparar consumos y valores, y explicar resultados con evidencia estructurada. Una variación es una heurística configurable de demostración, no una regla oficial ni un indicador de seguridad. El producto no debe inferir causas sin respaldo ni diagnosticar fugas.

## D3. Extracción PDF sin OCR

Se plantea PyMuPDF para documentos con texto seleccionable, separando extracción de texto e interpretación de campos mediante parsers modulares. OCR queda fuera del MVP. Un campo no reconocido debe quedar ausente (`null`) con una advertencia; el parser no debe completar datos por conjetura.

## D4. Persistencia mínima y propiedad explícita

SQLite es suficiente para el prototipo. Se conservan campos estructurados, `user_id`, conceptos y advertencias, nunca el PDF ni texto bruto. Las comparaciones usan una colección asociada explícitamente, y las facturas privadas deben pertenecer a la cuenta que las consulta. Las migraciones antiguas añaden un propietario nullable; los registros legacy ownerless quedan inaccesibles y no se reasignan automáticamente.

## D5. Análisis determinista; DigitalOcean Inference opcional

Los cálculos de variación se hacen de forma determinista en el servidor. DigitalOcean Inference es el proveedor opcional previsto para redactar explicaciones a partir de campos depurados. La configuración es `LLM_BASE_URL=https://inference.do-ai.run/v1`, `LLM_API_KEY` vacía por defecto y `LLM_MODEL=glm-5.3`. Sin clave, el modo de demostración determinista permite usar el chat sin llamada externa. El contexto enviado al proveedor excluye el PDF y su texto completo. No se incluyen RAG ni modelos predictivos en esta versión. La llamada real no se ha verificado sin una clave configurada.

## D6. Demo pública y espacio privado por cuenta

La landing, el registro y el historial sintético son públicos. `/demo` fija la colección sintética, incluso con una cookie de sesión presente. `/app` requiere autenticación para cargar y leer facturas propias. En demo pública, `PUBLIC_DEMO=true` en backend y `VITE_PUBLIC_DEMO=true` en frontend mantienen la interfaz y el API limitados a datos sintéticos y deshabilitan la carga.

## D7. Sesiones por cookie y CSRF

El backend almacena contraseñas con hash Argon2 y usa una cookie opaca `HttpOnly`, `SameSite=Lax`, con expiración de 14 días y atributo `Secure` en producción. La base guarda el hash del token de sesión. El token CSRF se devuelve al autenticar, permanece solo en memoria del cliente y acompaña operaciones privadas mutables junto con la comprobación del origen. Esta opción evita persistir la sesión en `localStorage` y separa el contenido de cada cuenta.

El MVP no incluye recuperación de contraseña, confirmación de correo, OAuth ni rate limiting. La autenticación no se toma como sustituto de una revisión de privacidad y operación antes de ofrecer el procesamiento público de facturas reales.

## Fuentes de fundamento

El plan cita como contexto sobre componentes del servicio y presentación de información de consumo los conceptos de la [CREG](https://gestornormativo.creg.gov.co/gestor/entorno/docs/concepto_creg_0000078_2016.htm) y [Superservicios](https://gestornormativo.creg.gov.co/gestor/entorno/docs/concepto_superservicios_0000570_2021.htm). La [documentación oficial de DigitalOcean Inference](https://docs.digitalocean.com/products/inference/how-to/use-chat-completions-api/) describe la API de chat completions usada como referencia. La propuesta de licencia MIT se basa en la licencia publicada por [Open Source Initiative](https://opensource.org/license/mit). Estas referencias no implican aval de dichas entidades ni constituyen asesoría jurídica.
