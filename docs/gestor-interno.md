# Gestor privado de consultas

Acceso: https://www.lafabricadeclientes.es/gestor/
Un solo usuario (Javier), con la contraseña guardada en el secreto de GitHub Actions `GESTOR_PASSWORD`. No se necesita nombre de usuario. No guardar contraseñas en el repositorio ni enviarlas por chat.

## Primera versión

- Recepción real del formulario de contacto, con respuesta de éxito únicamente después de guardar.
- Bandeja, búsqueda, filtros y paginación (25 consultas por página).
- Datos de empresa, contacto, inversión y mensaje original.
- Estados: nuevo, contactado, propuesta enviada, ganado y no encaja.
- Notas privadas, protección frente a cambios simultáneos entre pestañas y eliminación con confirmación.
- Enlaces para responder desde el correo o llamar. No envía emails ni notificaciones automáticas.
- Botón de WhatsApp en la web al +34 662 434 611. No importa conversaciones de WhatsApp ni correos anteriores.

Los mensajes antiguos del formulario anterior se enviaban desde la aplicación de correo del visitante: no existe una bandeja histórica que podamos importar de la web.

## Datos y despliegues

El backend es PHP (8.1 o superior), sin frameworks ni dependencias de base de datos. La web sigue compilándose con Astro.

En Sered el fichero de datos es `/home/lafabricadeclien/.fabrica-manager/store.json`, **fuera de public_html**. Las sesiones y el bloqueo de escritura están en el mismo directorio (0700; datos 0600). Se emplea bloqueo exclusivo, escritura temporal y renombrado atómico. Un fichero corrupto causa error; nunca se reinicia automáticamente. Límite inicial: 10.000 consultas; al alcanzarlo el formulario devuelve error explícito.

El despliegue FTP no mueve ni reemplaza este directorio. Las copias de la web en `_fabrica-backups` **no incluyen las consultas**: incluir `.fabrica-manager` en las copias de la cuenta de cPanel. Una restauración debe hacerse fuera del horario de recepción, guardando previamente el fichero actual. No subir copias de datos personales a GitHub ni al directorio público.

El hash de contraseña (PBKDF2-SHA256, 600.000 iteraciones y sal aleatoria) está en `public_html/_fabrica-private/auth.json`. La carpeta está bloqueada por Apache, se verifica HTTP 403 antes de subirlo y se excluye expresamente del cambio de versión. No se publica la contraseña original. GitHub solo pasa el secreto al proceso de publicación. Cada despliegue genera una nueva sal y cierra las sesiones anteriores.

Cambiar o recuperar contraseña: actualizar `GESTOR_PASSWORD` (mínimo 14 caracteres) y ejecutar **Publicar web en Sered** en Actions. No existe un registro público ni una página de activación sin contraseña.

## Seguridad y funcionamiento

- HTTPS en producción; cookie Secure, HttpOnly y SameSite=Strict.
- Sesión: una hora de inactividad; ocho horas de duración máxima.
- CSRF en acceso, cambios y cierre de sesión; validación de origen.
- Límite por dirección: 8 intentos de acceso / 15 minutos; 5 envíos / hora. La dirección no se guarda: solo su hash con clave, eliminado al caducar durante la siguiente operación del limitador.
- Honeypot y validación de campos en servidor, salida escapada y cabeceras CSP/no-store/noindex.
- Reintento del mismo correo, empresa y mensaje en 10 minutos: una sola consulta.
- El gestor no se incluye en el sitemap ni en el menú público.
- La política de privacidad refleja el nuevo tratamiento. Revisar periódicamente y eliminar consultas que ya no deban conservarse; las copias de seguridad tienen su propio ciclo de retención.

## Desarrollo y comprobaciones

Astro dev no ejecuta PHP. Para probar el backend aislado:

```
python3 tests/test-manager.py
python3 tests/test-cutover.py
```

La primera prueba levanta un servidor PHP temporal, usa una contraseña ficticia y borra sus datos al terminar. Comprueba formulario, persistencia, duplicados, validación, acceso, CSRF, escape de HTML, estados/notas, conflictos, eliminación, cierre de sesión, límites e integridad. Nunca contacta con producción.

La segunda prueba simula el despliegue y su reversión por FTPS y verifica que se preserve la carpeta privada. Ejecutar después de `npm run build`. La vista previa antigua de Sites/preview-astro no incorpora el backend PHP.
