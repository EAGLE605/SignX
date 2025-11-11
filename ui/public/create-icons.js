/**
 * Simple script to create PWA icons using Canvas
 * Run with: node create-icons.js
 */

const fs = require('fs');
const { createCanvas } = require('canvas');

function createIcon(size) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background gradient
  const gradient = ctx.createLinearGradient(0, 0, size, size);
  gradient.addColorStop(0, '#667eea');
  gradient.addColorStop(1, '#764ba2');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

  // Draw "SignX" text
  ctx.fillStyle = '#ffffff';
  ctx.font = `bold ${size * 0.25}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('SignX', size / 2, size / 2 - size * 0.1);

  // Draw "Studio" text
  ctx.font = `${size * 0.15}px Arial`;
  ctx.fillText('Studio', size / 2, size / 2 + size * 0.15);

  return canvas.toBuffer('image/png');
}

// Create icons
console.log('Creating PWA icons...');

const icon192 = createIcon(192);
fs.writeFileSync('pwa-192x192.png', icon192);
console.log('✓ Created pwa-192x192.png');

const icon512 = createIcon(512);
fs.writeFileSync('pwa-512x512.png', icon512);
console.log('✓ Created pwa-512x512.png');

const iconApple = createIcon(180);
fs.writeFileSync('apple-touch-icon.png', iconApple);
console.log('✓ Created apple-touch-icon.png');

console.log('✓ All icons created successfully!');
