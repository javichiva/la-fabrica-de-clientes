# Publicación en Sered

GitHub Actions compila y audita Astro antes de publicar por FTPS en host.cpseo16.eu:21. La cuenta info@lafabricadeclientes.es está limitada a public_html y por ello la raíz FTP es `/`. Los únicos secretos usados son FTP_USERNAME y FTP_PASSWORD; no se desactiva la validación TLS.

Los cambios relevantes de `main` disparan `Publicar web en Sered`. La prueba `/preview-astro/` sigue disponible con noindex y solo se actualiza manualmente. La raíz de producción no tiene noindex global; se conservan los noindex individuales de borradores y 404.

## Cambio y respaldo

Se sube todo el build a `/_fabrica-stage/ID-INTENTO/` y se verifica el tamaño de cada archivo. Antes de retirar la versión anterior, se comprueba HTTP 403 en el directorio de respaldo. Se mueven los archivos anteriores a `/_fabrica-backups/ID-INTENTO/original/`, manteniendo preview-astro, .well-known y cgi-bin. El antiguo .htaccess se guarda como original-htaccess para que no sustituya la protección del respaldo. La operación no borra recursivamente archivos ni toca la base de datos.

WordPress deja de ejecutarse en la raíz: wp-admin, wp-includes, wp-content y los PHP se retiran al respaldo protegido. La base de datos permanece en Sered; este respaldo de archivos no es un volcado independiente de la base de datos. El contenido público también se conserva en src/data/legacy-pages.json. No eliminar la base de datos durante el periodo de recuperación.

Si falla la comprobación final de portada, se restauran los archivos movidos. Un corte de conexión durante los renombrados puede requerir restauración manual por cPanel. Para restaurar: detener despliegues, mover la raíz Astro a otro directorio protegido, devolver los archivos de original a public_html y renombrar original-htaccess a .htaccess. No mover las carpetas protegidas dentro de sí mismas. Verificar conexión con la base de datos y portada antes de reabrir.

Cada despliegue conserva la versión anterior. Revisar el espacio de hosting y conservar especialmente el primer respaldo de WordPress; no se configura limpieza automática.

## Migración de URL

Las 51 URL del sitemap anterior siguen existiendo; las 43 sin equivalente en la nueva web se conservan con su texto anterior bajo el diseño Astro. Esos textos breves no se presentan como artículos nuevos ampliados. Los sitemaps antiguos redirigen a /sitemap.xml. HTTPS y www se normalizan mediante .htaccess; las URL inexistentes responden 404.

La política de cookies se ha actualizado para describir la web estática y el mapa bajo petición. El mapa solo contacta con Google cuando el visitante lo carga. Las fuentes continúan sirviéndose desde Google Fonts. No se añaden analítica ni cookies publicitarias.
