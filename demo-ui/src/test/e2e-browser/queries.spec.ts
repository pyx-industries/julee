import { test, expect } from '@playwright/test';

test('queries page loads', async ({ page }) => {
  await page.goto('/queries');
  await expect(page.getByRole('heading', { name: 'Knowledge Service Queries' })).toBeVisible();
});
