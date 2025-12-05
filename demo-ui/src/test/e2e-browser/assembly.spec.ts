import { test, expect } from '@playwright/test';

test('assembly specifications page loads', async ({ page }) => {
  await page.goto('/specifications');
  await expect(page.getByRole('heading', { name: 'Assembly Specifications' })).toBeVisible();
});
