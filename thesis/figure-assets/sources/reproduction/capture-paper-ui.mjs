import { chromium } from '../frontend/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'thesis/figure-assets');await fs.mkdir(path.join(out,'ui'),{recursive:true});
const env=await fs.readFile(path.join(root,'.env'),'utf8');
const password=process.env.DEMO_PASSWORD||env.match(/^DEMO_PASSWORD=(.*)$/m)?.[1]?.replace(/^["']|["']$/g,'');
if(!password)throw Error('Demo password unavailable');
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:2,timezoneId:'Asia/Shanghai'});
const page=await context.newPage();const errors=[],captures=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
const base='http://localhost:5173';
async function settle(){await page.waitForLoadState('networkidle');await page.locator('.el-loading-mask').waitFor({state:'hidden'}).catch(()=>{});await page.evaluate(()=>document.fonts.ready);}
async function shot(id,title,{selector,chapter=4,note=''}={}){await settle();const target=path.join(out,'ui',id+'.png');if(selector)await page.locator(selector).screenshot({path:target,animations:'disabled'});else await page.screenshot({path:target,fullPage:true,animations:'disabled'});captures.push({id,title,chapter,type:'ui',files:['ui/'+id+'.png'],source:'frontend/src/views/'+(page.url().includes('/login')?'LoginView.vue':'WorkspaceView.vue'),url:page.url(),note,capturedAt:new Date().toISOString()});console.log('Captured',id);}
async function view(v){await page.goto(base+'/?view='+v);await settle();}
async function login(user){await context.clearCookies();await page.goto(base+'/login');await settle();await page.locator('#username').fill(user);await page.locator('#password').fill(password);await page.getByRole('button',{name:'Sign in to Shelfwise'}).click();await page.waitForURL(u=>u.pathname!='/login');await settle();checks.push(user+' signs in successfully');}
async function dialog(name){await page.getByRole('dialog',{name,exact:true}).waitFor();await settle();}
async function close(){await page.getByRole('dialog').getByRole('button',{name:'Cancel',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});}
try{
 await page.goto(base+'/login');await shot('01-login-desktop','Desktop sign-in interface',{note:'Left-hand preview is illustrative UI, not measured inventory.'});
 await login('admin');
 for(const [v,id,title] of [['overview','02-dashboard','Administrator dashboard'],['inventory','03-inventory','Inventory search and stock status'],['products','04-catalogue','Product catalogue'],['categories','05-categories','Category management'],['suppliers','06-suppliers','Supplier directory'],['transactions','07-history','Attributed stock movement history'],['warnings','08-warnings','Open warning board'],['reports','09-reports','Inventory reporting'],['team','10-team','Staff and role administration'],['settings','11-settings','Store settings']]){await view(v);await shot(id,title);}
 await view('inventory');await page.getByPlaceholder('Search product, SKU or barcode').fill('milk');await shot('12-inventory-search','Product search by text',{chapter:2});
 await page.getByPlaceholder('Search product, SKU or barcode').fill('zz-paper-no-match');await page.getByText('No products match those filters').waitFor();await shot('13-empty-search','Empty-search recovery state',{chapter:5});checks.push('empty search renders expected state');
 await view('products');await page.getByRole('button',{name:'Add product',exact:true}).click();await dialog('Add a product');await shot('14-add-product','Product creation form',{selector:'.el-dialog'});await close();
 await page.getByRole('button',{name:'Product actions',exact:true}).first().click();await page.locator('.el-dropdown-menu__item:visible').filter({hasText:'Edit details'}).click();await dialog('Edit product');await shot('15-edit-product','Existing product and threshold edit form',{selector:'.el-dialog'});await close();
 await view('transactions');await page.getByRole('button',{name:'Record activity',exact:true}).click();await dialog('Record stock activity');
 const modal=page.getByRole('dialog');await modal.locator('.el-select__wrapper').first().click();await page.getByRole('option').first().click();await modal.locator('.el-dialog__header').click();
 const modes=[['Receive stock','16-stock-receipt','Stock receipt form'],['Dispatch stock','17-stock-dispatch','Stock dispatch form'],['Adjust quantity','18-stock-adjustment','Signed stock adjustment form'],['Record stock count','19-stocktake','Absolute stocktake form']];
 for(const [label,id,title] of modes){await modal.locator('.el-select__wrapper').nth(1).click();await page.getByRole('option',{name:label,exact:true}).click();await modal.locator('textarea').fill('Example reason — form demonstration only');await shot(id,title,{selector:'.el-dialog',note:'Draft form only; no stock movement was submitted.'});}
 await close();
 await view('categories');await page.getByRole('button',{name:'Add category'}).click();await dialog('Add a category');await shot('20-category-form','Category creation form',{selector:'.el-dialog'});await close();
 await view('suppliers');await page.getByRole('button',{name:'Add supplier'}).click();await dialog('Add a supplier');await shot('21-supplier-form','Supplier creation form',{selector:'.el-dialog'});await close();
 await view('team');await page.getByRole('button',{name:'Add team member'}).click();await dialog('Add team member');await shot('22-account-form','Staff account creation form',{selector:'.el-dialog'});await close();
 await login('manager');await view('inventory');await page.getByRole('button',{name:'Product actions',exact:true}).first().click();await page.locator('.el-dropdown-menu__item:visible').filter({hasText:'Edit thresholds'}).click();await dialog('Edit stock thresholds');await shot('23-manager-thresholds','Manager threshold-only edit form',{selector:'.el-dialog'});await close();
 await view('warnings');await shot('24-manager-workspace','Manager warning-review workspace');await view('team');if(new URL(page.url()).searchParams.get('view')!=='inventory')throw Error('Manager guard failed');checks.push('manager cannot reach staff administration');
 await view('batches');await shot('28-batches','Batch inventory with sellable balances and expiry state');
 await view('purchases');await shot('29-purchasing','Replenishment suggestions and purchasing workflow');
 await view('reviews');await shot('30-stock-reviews','Snapshot-based stock review queue');
 await login('clerk');await view('transactions');await shot('25-clerk-workspace','Clerk stock-activity workspace');await view('warnings');if(new URL(page.url()).searchParams.get('view')!=='inventory')throw Error('Clerk guard failed');checks.push('clerk cannot reach warning board');
 await context.clearCookies();await page.setViewportSize({width:390,height:844});await page.goto(base+'/login');await shot('26-mobile-login','Responsive Web sign-in on a phone',{note:'Responsive Web interface, not a native mobile application.'});await login('manager');await view('inventory');await shot('27-mobile-inventory','Responsive Web inventory on a phone',{note:'Responsive Web interface, not a native mobile application.'});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('Mobile page horizontal overflow');checks.push('390px responsive page has no document overflow');
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(path.join(out,'sources/ui-manifest.json'),JSON.stringify(captures,null,2));await fs.writeFile(path.join(out,'sources/ui-verification.json'),JSON.stringify({capturedAt:new Date().toISOString(),checks,consoleErrors:errors,durableWrites:0,screenshots:captures.length},null,2));
}finally{await browser.close();}
