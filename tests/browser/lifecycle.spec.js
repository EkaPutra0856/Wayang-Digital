import {test,expect} from '@playwright/test';
test('natural video ending preserves scene song; ending the session releases everything',async({page})=>{
 await page.goto('/');await expect(page.locator('#start')).toBeEnabled();await page.locator('#start').click();await expect(page.locator('#welcome')).toBeHidden({timeout:50000});
 await page.keyboard.press('Digit6');
 await expect(page.locator('#play-video')).toContainText('Sedang diputar');
 await expect(page.locator('#play-video')).toBeEnabled({timeout:15000});
 await expect(page.locator('#media-status')).toContainText('Lagu Taman');
 expect(await page.locator('#soundtrack').evaluate(a=>!a.paused)).toBe(true);
 await page.locator('#stage').focus();await page.keyboard.press('KeyQ');
 await expect(page.locator('#welcome')).toBeVisible();
 expect(await page.locator('#soundtrack').evaluate(a=>a.paused)).toBe(true);
 await page.locator('#start').click();await expect(page.locator('#welcome')).toBeHidden({timeout:50000});await page.locator('[data-action="salam"]').click();
 await expect(page.locator('#stage')).toHaveAttribute('data-nando','10');
});
test('all application resources are served locally and missing asset requests are absent',async({page})=>{
 const failures=[],external=[];
 page.on('requestfailed',r=>failures.push(r.url()));
 page.on('response',r=>{if(r.status()>=400)failures.push(r.url());});
 page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:4173'))external.push(r.url());});
 await page.goto('/');await expect(page.locator('#start')).toBeEnabled();await page.locator('#start').click();await expect(page.locator('#welcome')).toBeHidden({timeout:50000});
 await page.locator('[data-action="salam"]').click();
 await page.waitForTimeout(300);
 expect(failures).toEqual([]);expect(external).toEqual([]);
});
