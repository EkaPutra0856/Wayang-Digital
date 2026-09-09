import { chromium } from '@playwright/test';
const browser=await chromium.launch({args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
try{
 const page=await browser.newPage({permissions:['camera']});
 page.on('pageerror',e=>console.log('Page error:',e.message));
 await page.goto('http://localhost:5173');
 await page.waitForFunction(()=>!document.querySelector('#start').disabled);
 await page.locator('#start').click();
 await page.waitForFunction(()=>['Kamera aktif','Aktifkan kamera'].includes(document.querySelector('#camera-button-text').textContent),{},{timeout:50000});
 const result=await page.locator('#camera-button-text').textContent();
 console.log('Development camera:',result);
 if(result!=='Kamera aktif')throw new Error(await page.locator('#toast').textContent());
}finally{await browser.close();}
