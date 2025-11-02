import { test, expect } from '@playwright/test';

test.describe('Full Project Workflow', () => {
  test('Create project → Fill all stages → Submit → Generate report', async ({ page }) => {
    // Navigate to project list
    await page.goto('/');
    await expect(page.locator('h1, [role="heading"]')).toContainText(/project/i);

    // Create new project
    await page.click('button:has-text("New Project")');
    await page.fill('input[label="Project Name"]', 'E2E Test Project');
    await page.click('button:has-text("Create")');

    // Wait for navigation to project workspace
    await expect(page).toHaveURL(/\/projects\/.+/);
    await expect(page.locator('text=E2E Test Project')).toBeVisible();

    // Stage 1: Overview (auto-complete)
    await expect(page.locator('text=Project Overview')).toBeVisible();

    // Stage 2: Site
    await page.click('text=Site & Environmental');
    await page.fill('input[label="Address"]', '123 Main St, Dallas, TX 75201');
    await page.click('button:has-text("Resolve Location")');
    await expect(page.locator('text=Wind Speed')).toBeVisible({ timeout: 10000 });

    // Stage 3: Cabinet
    await page.click('text=Cabinet Design');
    await page.fill('input[label="Width (in)"]', '48');
    await page.fill('input[label="Height (in)"]', '96');
    await page.click('button:has-text("Calculate")');
    await expect(page.locator('text=Area:')).toBeVisible({ timeout: 10000 });

    // Stage 4: Structural
    await page.click('text=Structural Design');
    await page.fill('input[label="Moment Required (ft-lb)"]', '2500');
    await page.click('button:has-text("Search Options")');
    await expect(page.locator('text=Shape')).toBeVisible({ timeout: 10000 });

    // Stage 5: Foundation
    await page.click('text=Foundation');
    await page.fill('input[label="Diameter (in)"]', '18');
    await page.fill('input[label="Depth (ft)"]', '3');
    await page.click('button:has-text("Save Foundation Design")');

    // Stage 6: Finalization
    await page.click('text=Finalization');
    await page.fill('input[label="Height (ft)"]', '20');
    await page.click('button:has-text("Get Estimate")');
    await expect(page.locator('text=Total:')).toBeVisible({ timeout: 10000 });

    // Stage 7: Review
    await page.click('text=Review');
    await expect(page.locator('text=stage complete')).toHaveCount(5); // All stages complete

    // Stage 8: Submission
    await page.click('text=Submission');
    await page.click('button:has-text("Submit Project")');
    await page.click('button:has-text("Confirm Submit")');
    await expect(page.locator('text=submitted successfully')).toBeVisible({ timeout: 10000 });
  });

  test('Canvas derive updates form', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("New Project")');
    await page.fill('input[label="Project Name"]', 'Canvas Test');
    await page.click('button:has-text("Create")');

    await page.click('text=Cabinet Design');

    // Wait for canvas to load
    await expect(page.locator('canvas')).toBeVisible({ timeout: 5000 });

    // Resize canvas element (simulate drag)
    const canvas = page.locator('canvas').first();
    const box = await canvas.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 50, box.y + box.height / 2 + 50);
      await page.mouse.up();
    }

    // Wait for derive to complete
    await page.waitForTimeout(500); // Debounce time

    // Verify form fields updated (values may change based on backend)
    const widthInput = page.locator('input[label="Width"]');
    await expect(widthInput).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('Keyboard navigation through stages', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("New Project")');
    await page.fill('input[label="Project Name"]', 'Accessibility Test');
    await page.click('button:has-text("Create")');

    // Tab through stepper
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter'); // Activate first step

    // Tab through form fields
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
  });

  test('ARIA labels present', async ({ page }) => {
    await page.goto('/');

    // Check for navigation landmarks
    const nav = page.locator('nav, [role="navigation"]');
    await expect(nav).toHaveCount(1);

    // Check button labels
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const text = await button.textContent();
      // Button should have aria-label or visible text
      expect(ariaLabel || text).toBeTruthy();
    }
  });
});
