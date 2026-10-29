/**
 * PWA Setup Tests for TASK-FE-P7-012
 *
 * These tests verify the PWA configuration is complete including:
 * - Meta tags in index.html
 * - Apple mobile web app support
 * - Theme color configuration
 * - Vite PWA plugin configuration
 *
 * Test Scenarios:
 * 1. Theme color meta tag present
 * 2. Apple mobile web app meta tags present
 * 3. Manifest link tag present
 * 4. Viewport meta tag configured for PWA
 * 5. Vite config has PWA plugin
 */

import { describe, test, expect } from 'vitest';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { JSDOM } from 'jsdom';

const PROJECT_ROOT = join(__dirname, '../..');
const INDEX_HTML_PATH = join(PROJECT_ROOT, 'index.html');
const VITE_CONFIG_PATH = join(PROJECT_ROOT, 'vite.config.ts');

describe('TASK-FE-P7-012: PWA Setup Configuration', () => {
  describe('index.html Meta Tags', () => {
    let dom: JSDOM;
    let document: Document;

    // Parse index.html before running tests
    const getDocument = () => {
      if (!document) {
        const htmlContent = readFileSync(INDEX_HTML_PATH, 'utf-8');
        dom = new JSDOM(htmlContent);
        document = dom.window.document;
      }
      return document;
    };

    test('theme-color meta tag is present', () => {
      const doc = getDocument();
      const themeColor = doc.querySelector('meta[name="theme-color"]');

      expect(themeColor).toBeTruthy();
    });

    test('theme-color meta tag has correct Emerald Night color (#0B1026)', () => {
      const doc = getDocument();
      const themeColor = doc.querySelector('meta[name="theme-color"]');

      expect(themeColor).toBeTruthy();
      expect(themeColor?.getAttribute('content')).toBe('#0B1026');
    });

    test('manifest link tag is present', () => {
      const doc = getDocument();
      const manifestLink = doc.querySelector('link[rel="manifest"]');

      expect(manifestLink).toBeTruthy();
    });

    test('manifest link points to /manifest.json', () => {
      const doc = getDocument();
      const manifestLink = doc.querySelector('link[rel="manifest"]');

      expect(manifestLink).toBeTruthy();
      expect(manifestLink?.getAttribute('href')).toBe('/manifest.json');
    });

    test('viewport meta tag includes viewport-fit=cover', () => {
      const doc = getDocument();
      const viewport = doc.querySelector('meta[name="viewport"]');

      expect(viewport).toBeTruthy();
      const content = viewport?.getAttribute('content') || '';
      expect(content).toContain('viewport-fit=cover');
    });
  });

  describe('Apple Mobile Web App Support', () => {
    let document: Document;

    const getDocument = () => {
      if (!document) {
        const htmlContent = readFileSync(INDEX_HTML_PATH, 'utf-8');
        const dom = new JSDOM(htmlContent);
        document = dom.window.document;
      }
      return document;
    };

    test('apple-mobile-web-app-capable meta tag is present', () => {
      const doc = getDocument();
      const appleMeta = doc.querySelector('meta[name="apple-mobile-web-app-capable"]');

      expect(appleMeta).toBeTruthy();
    });

    test('apple-mobile-web-app-capable is set to "yes"', () => {
      const doc = getDocument();
      const appleMeta = doc.querySelector('meta[name="apple-mobile-web-app-capable"]');

      expect(appleMeta).toBeTruthy();
      expect(appleMeta?.getAttribute('content')).toBe('yes');
    });

    test('apple-mobile-web-app-title meta tag is present', () => {
      const doc = getDocument();
      const appleTitle = doc.querySelector('meta[name="apple-mobile-web-app-title"]');

      expect(appleTitle).toBeTruthy();
    });

    test('apple-mobile-web-app-title is "PCF Calculator"', () => {
      const doc = getDocument();
      const appleTitle = doc.querySelector('meta[name="apple-mobile-web-app-title"]');

      expect(appleTitle).toBeTruthy();
      expect(appleTitle?.getAttribute('content')).toBe('PCF Calculator');
    });

    test('apple-mobile-web-app-status-bar-style meta tag is present', () => {
      const doc = getDocument();
      const statusBar = doc.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');

      expect(statusBar).toBeTruthy();
    });

    test('apple-touch-icon link is present', () => {
      const doc = getDocument();
      const touchIcon = doc.querySelector('link[rel="apple-touch-icon"]');

      expect(touchIcon).toBeTruthy();
    });

    test('apple-touch-icon points to correct path', () => {
      const doc = getDocument();
      const touchIcon = doc.querySelector('link[rel="apple-touch-icon"]');

      expect(touchIcon).toBeTruthy();
      const href = touchIcon?.getAttribute('href') || '';
      expect(href).toContain('apple-touch-icon');
    });
  });

  describe('Windows/Edge PWA Support', () => {
    let document: Document;

    const getDocument = () => {
      if (!document) {
        const htmlContent = readFileSync(INDEX_HTML_PATH, 'utf-8');
        const dom = new JSDOM(htmlContent);
        document = dom.window.document;
      }
      return document;
    };

    test('msapplication-TileColor meta tag is present', () => {
      const doc = getDocument();
      const tileColor = doc.querySelector('meta[name="msapplication-TileColor"]');

      expect(tileColor).toBeTruthy();
    });

    test('msapplication-TileColor matches theme color', () => {
      const doc = getDocument();
      const tileColor = doc.querySelector('meta[name="msapplication-TileColor"]');

      expect(tileColor).toBeTruthy();
      expect(tileColor?.getAttribute('content')).toBe('#0B1026');
    });
  });

  describe('Vite PWA Plugin Configuration', () => {
    test('vite.config.ts exists', () => {
      expect(existsSync(VITE_CONFIG_PATH)).toBe(true);
    });

    test('vite.config.ts imports VitePWA', () => {
      const viteConfig = readFileSync(VITE_CONFIG_PATH, 'utf-8');

      expect(viteConfig).toContain('vite-plugin-pwa');
    });

    test('vite.config.ts has VitePWA in plugins array', () => {
      const viteConfig = readFileSync(VITE_CONFIG_PATH, 'utf-8');

      expect(viteConfig).toContain('VitePWA');
    });

    test('vite.config.ts configures registerType as autoUpdate', () => {
      const viteConfig = readFileSync(VITE_CONFIG_PATH, 'utf-8');

      expect(viteConfig).toContain('registerType');
      expect(viteConfig).toContain('autoUpdate');
    });

    test('vite.config.ts configures workbox caching strategies', () => {
      const viteConfig = readFileSync(VITE_CONFIG_PATH, 'utf-8');

      expect(viteConfig).toContain('workbox');
      expect(viteConfig).toContain('runtimeCaching');
    });

    test('vite.config.ts uses NetworkFirst for API calls', () => {
      const viteConfig = readFileSync(VITE_CONFIG_PATH, 'utf-8');

      expect(viteConfig).toContain('NetworkFirst');
    });

    test('vite.config.ts uses CacheFirst for static assets', () => {
      const viteConfig = readFileSync(VITE_CONFIG_PATH, 'utf-8');

      expect(viteConfig).toContain('CacheFirst');
    });
  });

  describe('PWA Dev Dependency', () => {
    test('vite-plugin-pwa is installed as dev dependency', () => {
      const packageJsonPath = join(PROJECT_ROOT, 'package.json');
      const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));

      expect(packageJson.devDependencies).toHaveProperty('vite-plugin-pwa');
    });
  });

  describe('Icon Files Existence', () => {
    test('icons directory exists in public folder', () => {
      const iconsDir = join(PROJECT_ROOT, 'public/icons');
      expect(existsSync(iconsDir)).toBe(true);
    });

    test('192x192 icon file exists', () => {
      const iconPath = join(PROJECT_ROOT, 'public/icons/icon-192x192.png');
      expect(existsSync(iconPath)).toBe(true);
    });

    test('512x512 icon file exists', () => {
      const iconPath = join(PROJECT_ROOT, 'public/icons/icon-512x512.png');
      expect(existsSync(iconPath)).toBe(true);
    });

    test('apple-touch-icon exists', () => {
      const iconPath = join(PROJECT_ROOT, 'public/icons/apple-touch-icon.png');
      expect(existsSync(iconPath)).toBe(true);
    });

    test('maskable 192x192 icon file exists', () => {
      const iconPath = join(PROJECT_ROOT, 'public/icons/icon-maskable-192x192.png');
      expect(existsSync(iconPath)).toBe(true);
    });

    test('maskable 512x512 icon file exists', () => {
      const iconPath = join(PROJECT_ROOT, 'public/icons/icon-maskable-512x512.png');
      expect(existsSync(iconPath)).toBe(true);
    });
  });
});
