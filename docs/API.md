# API de SmartBill AI

En desarrollo local, FastAPI se sirve en `http://localhost:8000`; OpenAPI está en `/docs`. Las respuestas de error usan `{ "error": { "code": "...", "message": "..." } }`.

## Rutas del frontend

| Ruta | Acceso | Descripción |
|---|---|---|
| `/` | Público | Landing |
| `/demo` | Público | Dashboard sintético fijo, sin sesión |
| `/login` | Público | Inicio de sesión |
| `/registro` | Público | Registro |
| `/app` | Requiere sesión | Espacio privado del usuario |

## Autenticación y sesión

| Método | Endpoint | Comportamiento |
|---|---|---|
| POST | `/api/auth/register` | Crea cuenta e inicia sesión; HTTP 201 |
| POST | `/api/auth/login` | Inicia sesión; HTTP 200 |
| GET | `/api/auth/me` | Devuelve el usuario y token CSRF de la sesión actual |
| POST | `/api/auth/logout` | Invalida la sesión y borra la cookie |

Registro y login reciben `{ "email": "...", "password": "..." }`. El correo debe ser válido y se normaliza a minúsculas; contraseña de 8 a 256 caracteres. La respuesta de registro/login/me tiene `{ "id": "uuid", "email": "...", "csrf_token": "..." }`.

La cookie `smartbill_session` es opaca, `HttpOnly`, `SameSite=Lax`, con vigencia de 14 días y `Secure` en producción. El servidor conserva el hash del token de sesión. El cliente debe enviar `credentials: "include"`; el token CSRF vive solo en memoria cliente y se manda como `X-CSRF-Token` para logout, carga de PDF y chat de facturas privadas. Login/registro verifican el encabezado `Origin` contra `FRONTEND_ORIGIN`. Las mutaciones privadas validan tanto `Origin` como CSRF.

## Facturas, análisis, dashboard y chat

| Método | Endpoint | Acceso / resultado |
|---|---|---|
| GET | `/health` | Público; estado del servicio |
| POST | `/api/invoices/upload` | Sesión + Origin + CSRF; PDF multipart, HTTP 201 |
| GET | `/api/invoices/{id}` | Demo sintética pública o dueño autenticado |
| GET | `/api/invoices/{id}/analysis` | Demo sintética pública o dueño autenticado; análisis determinista |
| GET | `/api/dashboard` | Sin sesión: datos sintéticos; con sesión en `/app`: colección propia más reciente |
| GET | `/api/dashboard?collection_id={uuid}` | Colección sintética pública o colección perteneciente al usuario autenticado |
| POST | `/api/chat` | Factura sintética: público; factura privada: sesión + Origin + CSRF |

`/demo` solicita explícitamente la colección sintética. Las facturas de usuario no aparecen en la demo. El endpoint de carga recibe el archivo en `file` y `collection_id` opcional; sin colección crea una nueva. Una colección existente solo se puede reutilizar por su propietario. El UUID reservado a la colección sintética no puede usarse para cargas privadas.

El PDF debe ser válido y de hasta 10 MB. Se procesa mediante un archivo temporal que se elimina al concluir; se persisten campos estructurados, conceptos y advertencias, no el PDF ni el texto extraído. PDF inválido devuelve 400; tamaño excedido, 413; colección o factura sin acceso, 404; CSRF u origen inválidos, 403; sin sesión en una ruta privada, 401. La demo pública (`PUBLIC_DEMO=true`) bloquea la carga con 403 y deja accesible solo la colección sintética.

`ChatRequest` contiene `invoice_id` UUID y `question` (máximo 2.000 caracteres). `ChatResponse` contiene `answer`, `mode` (`digitalocean` o `demo`) y `evidence`. Sin `LLM_API_KEY`, usa respuesta determinista local. Con clave configurada, llama al endpoint compatible de DigitalOcean Inference `/v1/chat/completions` con `LLM_BASE_URL` y `LLM_MODEL`. Solo debe enviarse pregunta y contexto estructurado permitido, nunca PDF, texto bruto ni identificadores privados. La llamada real al proveedor no se ha verificado en esta revisión.

## Colecciones de usuario y migración

Cada factura local nueva guarda `user_id`; los endpoints de lectura, análisis, dashboard y chat verifican propiedad. Un recurso ajeno responde 404 para no revelar su existencia. Las filas previas que no tienen `user_id` se conservan como legacy ownerless, pero no se pueden leer ni asignar automáticamente a una cuenta. En SQLite, el backend agrega la columna nullable e índice al arrancar; no se requiere un comando de migración manual para esa actualización aditiva.

El `collection_id` sintético permanece público y separado. Al usar una base vacía, el backend crea la colección de ejemplo con seis períodos de junio a noviembre de 2026.

## Códigos de error frecuentes

| HTTP | Código | Caso |
|---|---|---|
| 400 | `invalid_file` / validación | Archivo inválido o solicitud no válida |
| 401 | `authentication_required` | Falta sesión o expiró |
| 401 | `invalid_credentials` | Correo/contraseña incorrectos |
| 403 | `origin_rejected` | Origen ausente o no permitido |
| 403 | `csrf_invalid` | Token CSRF ausente o incorrecto |
| 403 | `upload_disabled` | Carga deshabilitada en demo pública |
| 404 | `invoice_not_found` / `collection_not_found` | No existe o no pertenece a la cuenta |
| 409 | `email_exists` | Correo ya registrado |
| 409 | `collection_reserved` | UUID reservado para la demo |
| 413 | `file_too_large` | PDF superior a 10 MB |
| 422 | `validation_error` | JSON o campos inválidos |
| 503 | `ai_unavailable` | Servicio LLM no disponible |

## Variables relacionadas

`FRONTEND_ORIGIN` debe ser el origen exacto que usa el navegador. Para demo pública configura conjuntamente backend `PUBLIC_DEMO=true` y frontend `VITE_PUBLIC_DEMO=true`; el último solo afecta qué controles muestra la UI, y el backend aplica la restricción efectiva. DigitalOcean Inference usa `LLM_BASE_URL=https://inference.do-ai.run/v1`, `LLM_API_KEY` y `LLM_MODEL=glm-5.3`. Los secretos solo se configuran en el servidor. Más detalles de ejecución en el [README](../README.md).
