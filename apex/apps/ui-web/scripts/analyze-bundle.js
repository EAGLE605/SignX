#!/usr/bin/env node
/**
 * Bundle size analyzer for production build
 * Validates bundle size <500KB gzipped target
 */

import fs from 'fs';
import { gzipSync } from 'zlib';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const distDir = join(__dirname, '../dist');

const TARGET_SIZE_KB = 500;

function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath);
    return stats.size;
  } catch {
    return 0;
  }
}

function getGzippedSize(filePath) {
  try {
    const content = fs.readFileSync(filePath);
    const gzipped = gzipSync(content);
    return gzipped.length;
  } catch {
    return 0;
  }
}

function formatBytes(bytes) {
  return (bytes / 1024).toFixed(2) + ' KB';
}

function analyzeBundle() {
  if (!fs.existsSync(distDir)) {
    console.error('❌ dist/ directory not found. Run "npm run build" first.');
    process.exit(1);
  }

  console.log('📦 Analyzing production bundle...\n');

  // Find all JS and CSS files
  const files = [];
  function walkDir(dir) {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = join(dir, entry.name);
        if (entry.isDirectory()) {
          walkDir(fullPath);
        } else if (entry.isFile() && (entry.name.endsWith('.js') || entry.name.endsWith('.css'))) {
          files.push(fullPath);
        }
      }
    } catch (err) {
      console.error(`Error reading directory ${dir}:`, err.message);
    }
  }
  walkDir(distDir);

  if (files.length === 0) {
    console.error('❌ No JS/CSS files found in dist/');
    process.exit(1);
  }

  let totalSize = 0;
  let totalGzipped = 0;
  const chunkSizes = [];

  console.log('📊 Bundle Analysis:\n');
  console.log('File'.padEnd(50) + 'Size'.padEnd(15) + 'Gzipped'.padEnd(15));
  console.log('-'.repeat(80));

  for (const file of files) {
    const size = getFileSize(file);
    const gzipped = getGzippedSize(file);
    const relativePath = file.replace(distDir + '/', '');
    
    totalSize += size;
    totalGzipped += gzipped;

    const isChunk = file.includes('.js') && (file.includes('chunk') || file.includes('vendor'));
    if (isChunk) {
      chunkSizes.push({
        file: relativePath,
        size: gzipped,
      });
    }

    console.log(
      relativePath.padEnd(50) +
      formatBytes(size).padEnd(15) +
      formatBytes(gzipped).padEnd(15)
    );
  }

  console.log('-'.repeat(80));
  console.log('\n📈 Summary:');
  console.log(`Total Size: ${formatBytes(totalSize)}`);
  console.log(`Total Gzipped: ${formatBytes(totalGzipped)}`);
  console.log(`Target: <${TARGET_SIZE_KB} KB gzipped\n`);

  // Check code splitting
  console.log('🔀 Code Splitting Check:');
  const vendorChunks = chunkSizes.filter(c => c.file.includes('vendor'));
  const appChunks = chunkSizes.filter(c => !c.file.includes('vendor') && c.file.includes('index'));

  if (vendorChunks.length > 0) {
    console.log(`✅ Vendor chunks detected: ${vendorChunks.length}`);
    vendorChunks.forEach(chunk => {
      console.log(`   - ${chunk.file}: ${formatBytes(chunk.size)}`);
    });
  } else {
    console.log('⚠️  No vendor chunks found (code splitting may not be working)');
  }

  if (appChunks.length > 0) {
    console.log(`✅ App chunks detected: ${appChunks.length}`);
  }

  // Validate bundle size
  const totalKB = totalGzipped / 1024;
  console.log('\n✅ Validation:');
  if (totalKB < TARGET_SIZE_KB) {
    console.log(`✅ Bundle size PASSED: ${totalKB.toFixed(2)} KB < ${TARGET_SIZE_KB} KB`);
  } else {
    console.log(`❌ Bundle size FAILED: ${totalKB.toFixed(2)} KB >= ${TARGET_SIZE_KB} KB`);
    process.exit(1);
  }

  // Check service worker
  const swPath = join(distDir, 'sw.js');
  const swManifestPath = join(distDir, 'manifest.json');
  if (fs.existsSync(swPath) || fs.existsSync(swManifestPath)) {
    console.log('✅ Service worker files detected');
  } else {
    console.log('⚠️  Service worker files not found (PWA may not be configured)');
  }

  console.log('\n✅ Bundle analysis complete!');
}

analyzeBundle();

