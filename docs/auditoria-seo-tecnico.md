# Auditoría técnica · 25 de septiembre de 2026

## Resultado

La compilación estática y los controles automatizados pasan: 33 HTML, 27 páginas indexables y exactamente 27 URLs en el sitemap. Quedan seis páginas con `noindex`: el error 404 y cinco artículos introductorios pendientes de ampliar. La versión privada sirve para revisión, no permite verificar indexación pública.

La web está preparada para continuar el trabajo de código y repositorio. **No está lista para sustituir WordPress sin cerrar los pendientes de migración, páginas legales y recepción de consultas.**

## Corregido en esta revisión

- Se ha declarado la convención de URL con barra final en Astro. El hosting definitivo debe aplicar la redirección correspondiente; la configuración del generador por sí sola no garantiza una redirección HTTP en cualquier servidor.
- El sitemap usa el dominio configurado en Astro, evita duplicados y solo incluye los tres artículos completos.
- Se ha añadido `BreadcrumbList` a las páginas indexables interiores, con URL final coherente con el canonical.
- La organización tiene un identificador estable, reutilizado por el publisher de los artículos.
- Se han añadido idioma y nombre del sitio a Open Graph y conexiones anticipadas a los servidores de fuentes.
- Se han ampliado las comprobaciones de compilación y el comando `npm run check:seo`.
- `.gitignore` ahora excluye variantes de `.env`, registros y archivos de macOS, además de dependencias y salida de compilación.

## Verificaciones realizadas

| Área | Evidencia y resultado |
|---|---|
| Compilación | Astro termina correctamente y genera 33 HTML. |
| Títulos y descripciones | Un título y descripción por página; sin títulos duplicados ni descripciones duplicadas entre páginas indexables. |
| H1 e idioma | Un H1 y `lang="es"` en todos los HTML. |
| Canonical | Se comprueba coincidencia exacta con la ruta y dominio final, no solo el prefijo. La 404 generada usa la ruta interna `/404/` y está excluida. |
| Sitemap | Conjunto idéntico a las 27 páginas indexables; sin duplicados, 404 ni borradores. |
| Robots | Permite rastreo en producción y referencia el sitemap correcto. La revisión de Sites permanece privada. |
| Enlaces | Destinos locales, recursos y fragmentos existentes; IDs sin duplicados. |
| Imágenes | Atributos alt y dimensiones presentes; imagen social existente para cada página. Esto no acredita que todos los atributos representen la proporción intrínseca: algunas tarjetas usan un marco visual común. |
| Datos estructurados | JSON válido, Organization, BreadcrumbList y BlogPosting en las tres guías; coherencia de las URLs. Sin estrellas, reseñas o métricas inventadas. No se ha ejecutado el Rich Results Test de Google. |
| Compartir | Open Graph, imagen, URL, idioma y Twitter summary_large_image. |
| Error HTTP | Una URL inexistente en el servidor local responde 404. Pendiente repetir contra el hosting definitivo. |
| Navegación | Blog presente en menú; portada revisada a 808 px sin desbordamiento horizontal. Las plantillas móviles se verificaron en las iteraciones anteriores. |
| Archivos | Revisión de patrones comunes de credenciales en textos publicables sin coincidencias. No sustituye una auditoría de seguridad completa. |
| Cambios | `git diff --check` sin errores. No se ha creado ni conectado un repositorio de GitHub. |

## Hallazgo de migración: 51 URLs existentes

Se consultaron el robots.txt y el índice Yoast del dominio público, junto a sus cinco sitemaps: artículos, páginas, servicios, ciudades y sectores. Contienen 51 URLs únicas. Solo 8 tienen la misma ruta en la nueva web; quedan **43 pendientes de decisión**, incluidas cuatro páginas legales.

El inventario está en [migracion-urls.csv](migracion-urls.csv). No se ha aplicado ninguna redirección masiva ni se ha eliminado contenido del WordPress público.

Antes de cambiar el dominio:

1. Completar el inventario con Search Console, analítica y enlaces externos: el sitemap no demuestra que sean todas las URLs ni indica su tráfico.
2. Leer las páginas antiguas que no tienen correspondencia y decidir si se conservan, se migran o tienen un equivalente real.
3. Crear una tabla final de redirecciones permanentes para equivalentes; no enviar todas las rutas antiguas a la portada.
4. Mantener el acceso al sitemap antiguo o redirigir su ruta a la nueva cuando se sustituya el sitio.
5. Probar HTTP/HTTPS, www/sin www, barras finales, redirecciones sin cadenas y errores 404 en el proveedor elegido.
6. Revisar la URL `/casos-reales/suboney/`: el nombre mostrado ya es Siboney. Antes del lanzamiento conviene decidir si se conserva o cambia a `/casos-reales/siboney/` con redirección según hosting. No se ha cambiado de forma silenciosa.

## Pendientes que no deben confundirse con un resultado correcto

### Páginas legales

El footer y el formulario enlazan a las páginas legales actuales del dominio público, pero esos documentos no están en el nuevo paquete. Hoy dependen del WordPress. Al sustituirlo, habría que conservar o migrar `/aviso-legal/`, `/politica-privacidad/`, `/politica-cookies/` y `/terminos-condiciones/`, revisando que describan el tratamiento real y los proveedores utilizados. No se han inventado datos legales.

### Contacto y medición

El formulario prepara un `mailto:`; no envía directamente al servidor. No debe contarse la preparación del resumen como una consulta recibida. Hay que elegir y configurar recepción, confirmar la entrega y definir medición y consentimiento según las herramientas realmente utilizadas.

### Rendimiento

Se revisó el peso de los archivos: las imágenes más pesadas están aproximadamente entre 202 y 375 KB. Hay imágenes diferidas y prioridad para las principales, pero las fuentes se cargan desde Google Fonts y el mapa incluye un tercero. Convertir capturas a formatos más ligeros y servir tamaños adaptados es una mejora posible.

**No se han medido Core Web Vitals de usuarios reales ni se afirma una puntuación Lighthouse.** Las métricas de campo requieren tráfico público; realizar además una medición de laboratorio sobre el hosting final, especialmente LCP, CLS e INP de campo cuando haya datos.

### Indexación y buscadores

Los canonicals apuntan intencionadamente a `https://www.lafabricadeclientes.es/`. Ese dominio sigue sirviendo el WordPress anterior. La versión privada de Sites no constituye un lanzamiento SEO público. La privacidad debe mantenerse hasta decidir el destino; si se habilita una vista previa pública, añadir protección de indexación antes de abrirla.

No hay acceso verificado a Search Console: pendientes propiedad, sitemap, indexación, acciones manuales, informes de páginas y rendimiento. Ninguna prueba de código permite garantizar indexación ni rankings.

### Borradores

Los cinco artículos breves conservan sus rutas para no romper enlaces de contexto ya existentes, pero llevan `noindex` y no figuran en blog/sitemap. Ampliarlos antes de publicarlos como contenido principal; no usar `robots.txt` para bloquearlos, porque impediría leer el `noindex`.

## Repetir la auditoría

Con Node 24 y Python 3, dentro de `web/`:

```sh
npm ci
npm run build
npm run check:seo
git diff --check
```

La comprobación SEO es local y estructural: no verifica códigos HTTP externos, indexación de Google, métricas de campo ni relevancia editorial. La publicación final exige las comprobaciones adicionales anteriores.

## Fuentes

- [Google: migración de URLs](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes).
- [Google: datos estructurados de artículos](https://developers.google.com/search/docs/appearance/structured-data/article).
- [Robots del dominio actual](https://www.lafabricadeclientes.es/robots.txt) y [sitemap Yoast actual](https://www.lafabricadeclientes.es/sitemap_index.xml), consultados el 25/09/2026 en horario de España.
