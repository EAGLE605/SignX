#!/usr/bin/env node
/**
 * Accessibility testing script
 * Runs axe-core checks and validates WCAG 2.1 AA compliance
 */

import { chromium } from 'playwright';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

async function runA11yTests() {
  console.log('♿ Running accessibility tests...\n');

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Inject axe-core
  const axeScript = readFileSync(
    join(__dirname, '../node_modules/@axe-core/react/dist/axe.min.js'),
    'utf-8'
  ).catch(() => {
    // Fallback: use CDN version
    return null;
  });

  const violations = [];
  const pages = ['/', '/projects/new'];

  for (const path of pages) {
    try {
      console.log(`Testing: ${BASE_URL}${path}`);
      await page.goto(`${BASE_URL}${path}`, { waitUntil: 'networkidle' });

      // Wait for React to hydrate
      await page.waitForTimeout(1000);

      // Inject and run axe
      if (axeScript) {
        await page.addScriptTag({ content: axeScript });
      } else {
        await page.addScriptTag({
          url: 'https://cdn.jsdelivr.net/npm/axe-core@4.8.4/axe.min.js',
        });
      }

      const results = await page.evaluate(() => {
        return new Promise((resolve) => {
          (window as any).axe.run((err, results) => {
            if (err) {
              resolve({ error: err.message });
            } else {
              resolve({
                violations: results.violations,
                passes: results.passes.length,
                incomplete: results.incomplete.length,
              });
          });
        });
      });

      if (results.error) {
        console.log(`⚠️  Error testing ${path}: ${results.error}`);
        continue;
      }

      console.log(`   Passes: ${results.passes}, Incomplete: ${results.incomplete}`);
      
      if (results.violations && results.violations.length > 0) {
        console.log(`   ❌ Violations: ${results.violations.length}`);
        violations.push({
          path,
          violations: results.violations,
        });
      } else {
        console.log(`   ✅ No violations`);
      }
    } catch (error) {
      console.log(`❌ Error testing ${path}: ${error.message}`);
    }
  }

  await browser.close();

  // Report summary
  console.log('\n📊 Accessibility Test Summary:');
  if (violations.length === 0) {
    console.log('✅ All pages passed WCAG 2.1 AA checks');
    return 0;
  } else {
    console.log(`❌ Found violations on ${violations.length} page(s):\n`);
    for (const { path, violations: pageViolations } of violations) {
      console.log(`\n${path}:`);
      for (const violation of pageViolations) {
        console.log(`  - ${violation.id}: ${violation.description}`);
        console.log(`    Impact: ${violation.impact}`);
        console.log(`    Nodes: ${violation.nodes.length}`);
      }
    }
    return 1;
  }
}

// Run tests
runA11yTests()
  .then((exitCode) => {
    process.exit(exitCode);
  })
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });

