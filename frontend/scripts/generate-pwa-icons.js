/**
 * PWA Icon Generator Script
 * Generates minimal valid PNG icons for PWA manifest
 *
 * This creates simple solid-color PNG files with the brand color (#003f7f)
 * For production, replace these with properly designed icons.
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const ICONS_DIR = path.join(__dirname, '../public/icons');
const BRAND_COLOR = { r: 0, g: 63, b: 127 }; // #003f7f

// Icon sizes to generate
const ICON_SIZES = [
  { name: 'icon-192x192.png', size: 192 },
  { name: 'icon-512x512.png', size: 512 },
  { name: 'icon-maskable-192x192.png', size: 192 },
  { name: 'icon-maskable-512x512.png', size: 512 },
  { name: 'apple-touch-icon.png', size: 180 },
];

/**
 * Create a minimal PNG file with the given dimensions and solid color
 * PNG format specification: https://www.w3.org/TR/PNG/
 */
function createPNG(width, height, color) {
  // Create raw image data (RGBA format)
  const rawData = Buffer.alloc(height * (1 + width * 4)); // +1 for filter byte per row

  for (let y = 0; y < height; y++) {
    const rowStart = y * (1 + width * 4);
    rawData[rowStart] = 0; // Filter byte (None)

    for (let x = 0; x < width; x++) {
      const pixelStart = rowStart + 1 + x * 4;
      rawData[pixelStart] = color.r;     // Red
      rawData[pixelStart + 1] = color.g; // Green
      rawData[pixelStart + 2] = color.b; // Blue
      rawData[pixelStart + 3] = 255;     // Alpha (fully opaque)
    }
  }

  // Compress the raw data
  const compressedData = zlib.deflateSync(rawData, { level: 9 });

  // Build PNG file
  const chunks = [];

  // PNG signature
  chunks.push(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));

  // IHDR chunk (image header)
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;  // Bit depth
  ihdr[9] = 6;  // Color type (RGBA)
  ihdr[10] = 0; // Compression method
  ihdr[11] = 0; // Filter method
  ihdr[12] = 0; // Interlace method
  chunks.push(createChunk('IHDR', ihdr));

  // IDAT chunk (image data)
  chunks.push(createChunk('IDAT', compressedData));

  // IEND chunk (image end)
  chunks.push(createChunk('IEND', Buffer.alloc(0)));

  return Buffer.concat(chunks);
}

/**
 * Create a PNG chunk with proper length and CRC
 */
function createChunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length, 0);

  const typeBuffer = Buffer.from(type, 'ascii');
  const crcData = Buffer.concat([typeBuffer, data]);
  const crc = calculateCRC(crcData);

  const crcBuffer = Buffer.alloc(4);
  crcBuffer.writeUInt32BE(crc >>> 0, 0);

  return Buffer.concat([length, typeBuffer, data, crcBuffer]);
}

/**
 * Calculate CRC-32 for PNG chunks
 */
function calculateCRC(data) {
  // CRC-32 polynomial used by PNG
  const crcTable = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    crcTable[n] = c;
  }

  let crc = 0xffffffff;
  for (let i = 0; i < data.length; i++) {
    crc = crcTable[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
  }
  return crc ^ 0xffffffff;
}

// Ensure icons directory exists
if (!fs.existsSync(ICONS_DIR)) {
  fs.mkdirSync(ICONS_DIR, { recursive: true });
}

// Generate each icon
console.log('Generating PWA icons...');
for (const icon of ICON_SIZES) {
  const iconPath = path.join(ICONS_DIR, icon.name);
  const pngData = createPNG(icon.size, icon.size, BRAND_COLOR);
  fs.writeFileSync(iconPath, pngData);
  console.log(`  Created: ${icon.name} (${icon.size}x${icon.size})`);
}

console.log('\nPWA icons generated successfully!');
console.log('Note: For production, replace these placeholder icons with properly designed graphics.');
