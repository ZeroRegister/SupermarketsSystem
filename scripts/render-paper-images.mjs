import {chromium} from '../frontend/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const out=path.join(root,'thesis/figure-assets');
const browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:1000,height:900},deviceScaleFactor:2,colorScheme:'light'});const page=await context.newPage();
try{
 for(const folder of ['code','evidence']){
  for(const f of (await fs.readdir(path.join(out,folder))).sort()){
   if(folder==='diagrams'&&!f.endsWith('.svg'))continue;
   if(folder!=='diagrams'&&!f.endsWith('.html'))continue;
   const file=path.join(out,folder,f);let width=1140;
   if(f.endsWith('.svg')){const xml=await fs.readFile(file,'utf8');width=Math.ceil(Number(xml.match(/<svg[^>]*width="([\d.]+)px"/)?.[1]||1400));const height=Math.ceil(Number(xml.match(/<svg[^>]*height="([\d.]+)px"/)?.[1]||1000));await page.setViewportSize({width,height});}
   else await page.setViewportSize({width:folder==='evidence'?1080:1000,height:900});
   await page.goto(pathToFileURL(file).href);await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>{document.documentElement.style.backgroundColor='white';document.documentElement.style.colorScheme='light';});
   await page.locator('body').screenshot({path:file.replace(/\.(svg|html)$/,'.png'),animations:'disabled'});console.log('Rendered',folder,f);
  }
 }
}finally{await browser.close();}
