# La Fábrica de Clientes

Web corporativa estática con Astro 7. Requiere Node >=22.12 (recomendado Node 24).

```sh
npm ci
npm run dev
npm run build
```

## Contenido

- `src/pages/index.astro`: portada.
- `src/data/pages.ts`: servicios, sectores, perfiles de negocios y artículos.
- `src/layouts/Layout.astro`: navegación, metadatos y pie.
- `src/styles/global.css`: estilos adaptables y movimiento reducido.
- `src/pages/contacto.astro`: formulario que prepara una consulta y permite abrirla en la aplicación de correo del visitante mediante mailto a info@javierchiva.com, o copiarla. El visitante completa el envío desde su correo. No hay backend de envío automático. Teléfono: +34 662 434 611.

## Antes del dominio definitivo

Para envío directo desde la web, configurar un endpoint de recepción autorizado. Confirmar datos legales. Completar casos con acciones, fechas, imágenes y métricas verificadas: los casos recogen actuaciones documentadas en javierchiva.com y omiten métricas sin contexto verificable. Validar especializaciones sectoriales y alcance de los 10.000 €. Revisar exportación de URLs/Search Console y preparar redirecciones reales antes de sustituir WordPress. El dominio actual no se ha modificado.

Canonical y sitemap apuntan al dominio final. La revisión se sirve en local; no hay una publicación de Sites confirmada. No se cargan analítica ni cookies publicitarias.

## Verificación

`python3 scripts/verify-build.py` comprueba los HTML generados, metadatos, imágenes, enlaces locales y sitemap después de `npm run build`. Los detalles de proyectos están en `src/data/case-details.ts`.
