# Seguridad

SmartBill AI es un prototipo de portafolio. La demo está pensada para datos sintéticos. El soporte de cuenta y propiedad de facturas no constituye una auditoría ni una aprobación para desplegar un servicio que trate facturas reales.

## Reportar una vulnerabilidad

No publiques vulnerabilidades, credenciales, PDFs ni datos personales en issues o pull requests. Usa la función **Private vulnerability reporting** del repositorio, si está habilitada. Si no está disponible, contacta en privado al propietario del repositorio por un canal que este haya publicado y solicita un canal seguro. No envíes detalles sensibles por un issue público.

Incluye descripción, pasos para reproducir, impacto observado y un medio seguro de contacto. Evita divulgar la vulnerabilidad públicamente hasta que se pueda evaluar y coordinar una corrección.

## Controles implementados

- Contraseñas con hash Argon2; el texto de la contraseña no se conserva.
- Sesiones aleatorias de 14 días mediante cookie `HttpOnly`, `SameSite=Lax` y `Secure` en producción. La tabla de sesiones guarda el hash del token opaco.
- Token CSRF en memoria del cliente; las operaciones privadas de carga/logout/chat requieren sesión, origen permitido y `X-CSRF-Token`.
- Acceso a facturas y colecciones locales filtrado por `user_id`; los datos ajenos responden como no encontrados.
- PDF limitado a 10 MB, validado y procesado temporalmente. Se guardan campos estructurados, no el archivo original ni el texto extraído.
- La colección sintética es pública; con `PUBLIC_DEMO=true`, la API limita los datos a esa colección y bloquea la carga. La interfaz se configura en paralelo con `VITE_PUBLIC_DEMO=true`.
- DigitalOcean Inference es opcional. `LLM_API_KEY` debe existir solo en el entorno backend; el modo determinista funciona sin clave. Una llamada real autenticada al proveedor no se ha verificado.

## Migración y operación

En una base SQLite anterior, el arranque añade `user_id` de forma aditiva. Facturas legacy sin propietario permanecen inaccesibles y no se transfieren automáticamente a cuentas nuevas. Conserva un respaldo de la base antes de actualizaciones operativas.

Antes de cualquier servicio público para facturas reales hacen falta, como mínimo, revisión de privacidad y retención, gestión de correo, recuperación de cuenta, rate limiting, controles antiabuso y despliegue HTTPS. La revisión E2E del producto no es una auditoría de seguridad. No se ha verificado un despliegue público.

No incluyas claves, contraseñas, cookies, tokens CSRF, PDFs reales o información personal en el repositorio, capturas, fixtures, logs, issues ni pull requests. No pegues secretos de DigitalOcean en `.env.example`; usa `backend/.env` local o un gestor de secretos del entorno.
