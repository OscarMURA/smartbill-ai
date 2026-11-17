# Guion de demostración — 180 segundos

## Preparación

Inicia backend y frontend con las instrucciones del [README](../README.md). Para el recorrido local que incluye una cuenta, deja `PUBLIC_DEMO=false` y `VITE_PUBLIC_DEMO=false`; deja `LLM_API_KEY` vacía para usar el chat determinista sin proveedor externo. Confirma `http://localhost:8000/health` y abre `http://localhost:5173`. No se necesita una cuenta precargada.

Para una presentación solo de datos sintéticos, configura juntos `PUBLIC_DEMO=true` en `backend/.env` y `VITE_PUBLIC_DEMO=true` en `frontend/.env`, y reinicia los servicios. Ese modo no admite la carga de facturas privadas.

## Recorrido cronometrado

### 0:00–0:20 | Landing e independencia

**Mostrar:** `/`.

**Decir:** «SmartBill AI es un proyecto personal independiente, no oficial de GdO, sin integración ni aval de la empresa. La página ofrece una demo sintética y un espacio separado para facturas de una cuenta».

### 0:20–0:45 | Demo sintética pública

**Mostrar:** pulsa **Explorar demo** para abrir `/demo`. Enseña la serie junio–noviembre: 19, 21, 20, 23, 22 y 32 m³.

**Decir:** «El consumo pasa de 22 a 32 m³: +45,45 %. Es una heurística ilustrativa, no demuestra la causa ni indica una fuga. Los valores de factura son ficticios».

La demo se mantiene en la colección sintética aunque el navegador ya tenga una cookie de sesión.

### 0:45–1:05 | Crear una cuenta local

**Mostrar:** **Crear cuenta**, ruta `/registro`. Registra un correo de prueba válido y una contraseña de al menos 8 caracteres. La aplicación lleva a `/app`.

**Decir:** «Las facturas propias quedan vinculadas a la cuenta. La contraseña se almacena con hash; la sesión usa una cookie protegida y no se guarda en localStorage».

### 1:05–1:35 | Cargar y validar documentos

**Mostrar:** desde Facturas, selecciona `samples/synthetic_invoices/archivo_invalido_sintetico.pdf` y procésalo. Observa el rechazo. Después carga `factura_2026-10_22m3.pdf` y `factura_2026-11_32m3.pdf`.

**Resultado esperado:** PDF inválido rechazado; las dos facturas válidas se procesan. La primera crea una colección privada y la segunda conserva esa colección.

**Decir:** «La aplicación valida el PDF, lo procesa de forma temporal y conserva campos estructurados asociados a la cuenta».

### 1:35–2:05 | Privacidad, persistencia y chat

**Mostrar:** selecciona noviembre, revisa los valores y pregunta `¿Por qué aumentó mi consumo?`.

**Resultado esperado:** análisis local de 22 a 32 m³ (+45,45 %) y respuesta determinista que no inventa una causa. Recarga la página y confirma que la sesión y facturas siguen disponibles.

**Decir:** «El chat trabaja con la factura seleccionada y sus datos estructurados. Sin clave de proveedor, el modo demo sigue funcionando. Una recarga conserva la sesión por cookie y las facturas por cuenta».

### 2:05–2:25 | Logout y separación de demo

**Mostrar:** cierra sesión y visita `/demo` de nuevo. Debe seguir mostrando únicamente datos sintéticos. Al volver a `/app`, se solicita autenticación.

**Decir:** «La cookie se invalida al cerrar sesión. El historial público permanece sintético y separado de las facturas privadas».

### 2:25–3:00 | Seguridad y cierre

**Mostrar:** si queda tiempo, abre `/docs` y menciona las rutas de autenticación y facturas.

**Decir:** «Las mutaciones privadas usan protección CSRF y validación de origen. No ofrecemos todavía recuperación de contraseña, verificación de correo o rate limiting; el proyecto no se ha desplegado públicamente ni se presenta como servicio listo para facturas reales».

## Comprobaciones reportadas

El equipo reportó 31 pruebas backend aprobadas y build frontend aprobado. El recorrido E2E en navegador verificó registro, carga, persistencia tras recarga, demo sintética aun con cookie presente, logout y chat privado con CSRF. Las cuentas temporales de verificación se eliminaron. No se ha verificado un despliegue público ni una llamada real a DigitalOcean Inference; en esta demo deja `LLM_API_KEY` vacía. No se declaró verificado el build Docker.

## Variación del modo público

Para mostrar solo la demo, configura y reinicia ambos lados con:

- `backend/.env`: `PUBLIC_DEMO=true`
- `frontend/.env`: `VITE_PUBLIC_DEMO=true`

La interfaz oculta los controles de carga y el backend rechaza cargas y lecturas privadas mientras ese modo está activo. El flag del frontend es visual; el backend aplica la restricción efectiva.
