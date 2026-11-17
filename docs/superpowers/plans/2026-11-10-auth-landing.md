# SmartBill AI — Auth y landing

**Objetivo:** una landing pública y acceso por cuenta que proteja las facturas locales sin cerrar la demostración sintética.

**Diseño:** `/` landing, `/demo` historial sintético público, `/login` y `/registro` formularios, `/app` dashboard privado. React Router separa rutas. La landing aplica `landing-page-design` y `ui-ux-pro-max`, usa la marca y tokens existentes, SVG/Lucide, CTA a demo y registro, fundamentos verificables y ninguna prueba social inventada.

**Auth:** usuarios SQLite con correo normalizado y hash Argon2; sesiones opacas aleatorias en tabla, cookie `HttpOnly` + `SameSite=Lax`, `Secure` en producción, vencimiento e invalidación en logout. Token CSRF por sesión enviado en `X-CSRF-Token` para mutaciones autenticadas. La API permite leer únicamente la colección sintética sin sesión; carga y colecciones locales requieren usuario y comprueban propiedad. No almacenar credenciales en frontend ni `localStorage`.

**Contratos:** `POST /api/auth/register {email,password}`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`. Respuesta de registro/login/me: `{id,email,csrf_token}`; el token CSRF se mantiene en memoria del cliente. Errores usan el envelope actual `{error:{code,message}}`. `credentials: 'include'` en fetch; `X-CSRF-Token` en upload y logout. La demo pública no llama rutas privadas.

## Tareas

1. **Backend auth:** modelos `UserRecord`/`SessionRecord`, hash, sesión, endpoints y pruebas de registro/login/logout/cookie/CSRF. Configurar secreto de sesión generado por instalación o variable de entorno, sin valor rastreado. Revisar documentación oficial FastAPI/OWASP.
2. **Propiedad de datos:** agregar `user_id` nullable a `InvoiceRecord` con migración local no destructiva; facturas existentes sin dueño quedan inaccesibles. Proteger upload, factura, análisis, dashboard local y chat local; impedir que un usuario agregue facturas a colección de otro. Pruebas de aislamiento entre dos cuentas y demo anónima.
3. **Landing:** página pública responsive con hero claro, vista ilustrada en SVG, tres beneficios concretos, cómo funciona, nota de independencia de GdO, privacidad y CTA a demo/registro. Sin logos o testimonios ficticios. Revisar 375/768/1024/1440 px, teclado, contraste y movimiento reducido.
4. **Frontend auth/rutas:** formulario registro/login, estado de sesión, logout, errores, redirección a `/app`, cliente API con cookie/CSRF. `DashboardPage` en `/demo` solo sintético y `/app` privado. Limpiar datos de React Query al cerrar sesión. Probar flujo completo con dos usuarios.
5. **Cierre:** actualizar README, API, arquitectura y guion; ejecutar pytest y build, revisar navegador y confirmar que las credenciales no aparecen en repo ni logs. No hacer commits ni despliegues.

**Límites:** sin recuperación de contraseña, verificación de correo, OAuth social ni despliegue público de facturas reales en esta iteración. Para servicio público faltan rate limiting, gestión de correo y revisión de privacidad operacional.
