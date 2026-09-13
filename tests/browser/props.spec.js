import {test,expect} from '@playwright/test';
test('bag and book respond to top-row, numpad and panel',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.locator('#start')).toBeEnabled();await page.locator('#start').click();
 await expect(page.locator('#welcome')).toBeHidden({timeout:50000});
 await page.keyboard.press('Digit1');await expect(page.locator('[data-action="bag"]')).toHaveAttribute('aria-pressed','true');
 await page.keyboard.press('KeyI');await expect(page.locator('#stage')).toHaveAttribute('data-curtain','idle');
 await page.keyboard.press('Digit2');await expect(page.locator('[data-action="book"]')).toHaveAttribute('aria-pressed','true');
 await page.keyboard.press('Numpad1');await expect(page.locator('[data-action="bag"]')).toHaveAttribute('aria-pressed','false');
 await page.keyboard.press('Numpad2');await expect(page.locator('[data-action="book"]')).toHaveAttribute('aria-pressed','false');
 await page.locator('[data-action="book"]').click();await expect(page.locator('[data-action="book"]')).toHaveAttribute('aria-pressed','true');
 await page.locator('[data-action="clear-props"]').click();await expect(page.locator('[data-action="book"]')).toHaveAttribute('aria-pressed','false');
 expect(errors).toEqual([]);
});
