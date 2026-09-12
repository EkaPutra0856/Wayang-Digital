import { test, expect } from '@playwright/test';
async function start(page) {
  await page.goto('/');
  await expect(page.locator('#start')).toBeEnabled();
  await page.locator('#start').click();
  await expect(page.locator('#welcome')).toBeHidden({timeout:50000});
}
test('production stage, manual poses, salam, responsive layout and help',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await start(page);
 await expect(page.locator('canvas')).toBeVisible();
 await page.locator('[data-action="salam"]').click();
 await expect(page.locator('#stage')).toHaveAttribute('data-nando','10');
 await expect(page.locator('#stage')).toHaveAttribute('data-costume','sport');
 await page.locator('#stage').focus();
 await page.keyboard.press('KeyY');
 await expect(page.locator('#stage')).toHaveAttribute('data-costume','school');
 await page.keyboard.down('KeyN');await page.keyboard.press('Digit2');await page.keyboard.up('KeyN');
 await expect(page.locator('#stage')).toHaveAttribute('data-nando','7');
 await page.locator('[data-action="help"]').click();
 await expect(page.locator('#help')).toBeVisible();
 await page.locator('#help .primary').click();
 await page.screenshot({path:'test-results/studio-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await expect(page.locator('#canvas')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/studio-mobile.png',fullPage:true});
 expect(errors).toEqual([]);
});
test('every transition key plays real video, changes scene, triggers curtain and resists duplicate',async({page})=>{
 await start(page);
 for(const [index,key] of ['6','7','0','8','9'].entries()) {
   await page.locator('#stage').focus();await page.keyboard.press('Digit'+key);
   await expect(page.locator('#stage')).toHaveAttribute('data-scene',String(index));
   await expect(page.locator('#play-video')).toContainText('Sedang diputar');
  await expect(page.locator('#stage')).toHaveAttribute('data-curtain','idle');
   expect(await page.locator('#cutscene').evaluate(v=>v.videoWidth)).toBeGreaterThan(0);
   const before=await page.locator('#cutscene').evaluate(v=>v.currentTime);
   await page.keyboard.press('Digit'+key);
   expect(await page.locator('#cutscene').evaluate(v=>v.currentTime)).toBeGreaterThanOrEqual(before);
   await page.keyboard.press('Escape');
   await expect(page.locator('#play-video')).toBeEnabled();
 }
 await page.locator('[data-action="stop-sound"]').click();
});
test('curtain holds for 1 second and video waits until curtain opens',async({page})=>{
 await start(page);await page.keyboard.press('Digit0');
 await expect(page.locator('#stage')).toHaveAttribute('data-curtain','closed');
 expect(await page.locator('#cutscene').evaluate(v=>v.currentTime)).toBe(0);
 await page.waitForTimeout(700);
 expect(await page.locator('#cutscene').evaluate(v=>v.currentTime)).toBe(0);
 await expect(page.locator('#stage')).toHaveAttribute('data-curtain','idle',{timeout:5000});
 await expect.poll(()=>page.locator('#cutscene').evaluate(v=>v.currentTime)).toBeGreaterThan(0);
 await page.keyboard.press('Escape');
});
test('camera denial blocks the entire studio and keyboard shortcuts',async({page})=>{
 await page.addInitScript(()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('denied','NotAllowedError');};});
 await page.goto('/');await expect(page.locator('#start')).toBeEnabled();
 await expect(page.locator('.workspace')).toBeHidden();
 await page.locator('#start').click();
 await expect(page.locator('#access-error')).toContainText('Izin kamera');
 await expect(page.locator('#welcome')).toBeVisible();
 await expect(page.locator('.workspace')).toBeHidden();
 await page.keyboard.press('Digit0');await page.keyboard.press('KeyA');
 await page.locator('[data-action="salam"]').evaluate(button=>button.click());
 await expect(page.locator('#stage')).toHaveAttribute('data-nando','1');
 await expect(page.locator('#bank-nando')).toContainText('Set 1');
 expect(await page.locator('#cutscene').evaluate(v=>v.paused)).toBe(true);
});
test('failed video does not close curtain and can be retried',async({page})=>{
 await page.route('**/media/video2-*.mp4',route=>route.abort());
 await start(page);await page.keyboard.press('Digit0');
 await expect(page.locator('#toast')).toContainText(/Video/);
 await expect(page.locator('#stage')).toHaveAttribute('data-curtain','idle');
 await expect(page.locator('#play-video')).toBeEnabled();
 await page.unroute('**/media/video2-*.mp4');
 await page.locator('#stage').focus();await page.keyboard.press('Digit0');
 await expect(page.locator('#play-video')).toContainText('Sedang diputar');
});
test('local hand model initializes in a worker with a simulated webcam',async({browser})=>{
 const context=await browser.newContext({permissions:['camera']});
 const page=await context.newPage();
 try {
  await start(page);
  await expect(page.locator('#camera-button-text')).toHaveText('Kamera aktif',{timeout:50000});
  await expect(page.locator('#stage-mode')).toHaveText('MODE JARI');
  await page.waitForTimeout(1500);
  await expect(page.locator('#camera-button-text')).toHaveText('Kamera aktif');
  await page.locator('#camera-button').click();
  await expect(page.locator('#welcome')).toBeVisible();
  await expect(page.locator('.workspace')).toBeHidden();
 }finally{await context.close();}
});

test('O and A control separate banks regardless of selected character; Tab only navigates',async({page})=>{
 await start(page);
 await expect(page.locator('#bank-nando')).toContainText('O');
 await expect(page.locator('#bank-ibu')).toContainText('A');
 await page.locator('[data-action="character"][data-value="Left"]').click();
 await page.keyboard.press('o');
 await expect(page.locator('#bank-nando')).toContainText('Nando Set 2');
 await expect(page.locator('#bank-ibu')).toContainText('Ibu Set 1');
 await expect(page.locator('#pose-buttons button').first()).toHaveAttribute('aria-label','Pose 1');
 await page.keyboard.press('a');
 await expect(page.locator('#bank-ibu')).toContainText('Ibu Set 2');
 await expect(page.locator('#pose-buttons button').first()).toHaveAttribute('aria-label','Pose 6');
 await page.keyboard.down('o');await page.keyboard.down('o');await page.keyboard.up('o');
 await expect(page.locator('#bank-nando')).toContainText('Nando Set 1');
 await expect(page.locator('#bank-ibu')).toContainText('Ibu Set 2');
 await page.locator('#stage').focus();await page.keyboard.press('Tab');
 await expect(page.locator('#bank-nando')).toContainText('Nando Set 1');
 await expect(page.locator('#bank-ibu')).toContainText('Ibu Set 2');
 await page.locator('#bank-ibu').click();
 await expect(page.locator('#bank-ibu')).toContainText('Ibu Set 1');
 await page.locator('[data-action="salam"]').click();
 await expect(page.locator('#bank-nando')).toContainText('Nando Set 2');
 await expect(page.locator('#bank-ibu')).toContainText('Ibu Set 1');
 await expect(page.locator('#stage')).toHaveAttribute('data-nando','10');
});

test('camera track loss locks access and stops media; regrant restores access',async({page})=>{
 await start(page);await page.keyboard.press('Digit0');
 await expect(page.locator('#play-video')).toContainText('Sedang diputar');
 await page.locator('#webcam').evaluate(video=>video.srcObject.getVideoTracks().forEach(track=>track.stop()));
 await expect(page.locator('#welcome')).toBeVisible();
 await expect(page.locator('.workspace')).toBeHidden();
 expect(await page.locator('#cutscene').evaluate(video=>video.paused)).toBe(true);
 expect(await page.locator('#soundtrack').evaluate(audio=>audio.paused)).toBe(true);
 await page.locator('#start').click();
 await expect(page.locator('#welcome')).toBeHidden({timeout:50000});
 await expect(page.locator('.workspace')).toBeVisible();
});
test('missing camera keeps access locked',async({page})=>{
 await page.addInitScript(()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('missing','NotFoundError');};});
 await page.goto('/');await expect(page.locator('#start')).toBeEnabled();await page.locator('#start').click();
 await expect(page.locator('#access-error')).toContainText('Kamera tidak ditemukan');
 await expect(page.locator('.workspace')).toBeHidden();
 await expect(page.locator('#start')).toBeEnabled();
});

test('scale triggers provide exactly two larger steps and keyboard repeat is ignored',async({page})=>{
 await start(page);
 await expect(page.locator('#scale-label')).toHaveText('Normal 100%');
 await expect(page.locator('#scale-down')).toBeDisabled();
 await page.keyboard.down('Equal');await page.keyboard.down('Equal');await page.keyboard.up('Equal');
 await expect(page.locator('#scale-label')).toHaveText('Besar 125%');
 await page.keyboard.press('NumpadAdd');
 await expect(page.locator('#scale-label')).toHaveText('Paling besar 150%');
 await expect(page.locator('#scale-up')).toBeDisabled();
 await page.keyboard.press('Equal');
 await expect(page.locator('#scale-label')).toHaveText('Paling besar 150%');
 await page.keyboard.press('Minus');await expect(page.locator('#scale-label')).toHaveText('Besar 125%');
 await page.locator('#scale-down').click();await expect(page.locator('#scale-label')).toHaveText('Normal 100%');
 await page.locator('#scale-up').click();await page.keyboard.press('KeyS');
 await expect(page.locator('#scale-label')).toHaveText('Normal 100%');
 await expect(page.locator('#finger-status')).toHaveCount(0);
});
test('B spawns the persistent bouncing ball trigger',async({page})=>{
 await start(page);await page.locator('#stage').focus();await page.keyboard.press('KeyB');
 await expect(page.locator('[data-action="ball"]')).toHaveAttribute('aria-pressed','true');
});
test('Nando pose 7 remains a normal pose on every background',async({page})=>{
 await start(page);
 await page.locator('#bank-nando').click();
 await expect(page.locator('#pose-buttons button').nth(1)).toHaveAttribute('data-action','pose');
 await expect(page.locator('#pose-buttons button').nth(1)).toHaveAttribute('aria-label','Pose 7');
 await page.locator('[data-action="scene"][data-value="1"]').click();
 await expect(page.locator('#pose-buttons button').nth(1)).toHaveAttribute('data-action','pose');
 await expect(page.locator('#pose-buttons button').nth(1)).toHaveAttribute('aria-label','Pose 7');
});
