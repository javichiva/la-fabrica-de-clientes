import {pages,sectors,cases} from '../data/pages';
import {journal} from '../data/journal';
import type {APIRoute} from 'astro';
export const GET:APIRoute=({site})=>{
 const paths=['','servicios','sectores','casos-reales','blog','contacto',...pages.map(p=>p.slug),...sectors.map(p=>'sectores/'+p.slug),...cases.map(p=>'casos-reales/'+p.slug),...journal.map(p=>'blog/'+p.slug)];
 const escape=(value:string)=>value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 return new Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+[...new Set(paths)].map(p=>'<url><loc>'+escape(new URL(p?p+'/':'/',site).href)+'</loc></url>').join('')+'</urlset>',{headers:{'Content-Type':'application/xml; charset=utf-8'}});
};
