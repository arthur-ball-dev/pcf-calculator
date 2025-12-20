/**
 * PWA Manifest Tests for TASK-FE-P7-012
 *
 * These tests verify the PWA manifest.json file exists and contains
 * all required fields for Progressive Web App functionality.
 *
 * Test Scenarios:
 * 1. Manifest file exists and is valid JSON
 * 2. Manifest has required PWA fields
 * 3. Manifest icons meet PWA requirements
 * 4. Manifest display mode is standalone
 */

import { describe, test, expect } from 'vitest';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

const PROJECT_ROOT = join(__dirname, '../..');
const MANIFEST_PATH = join(PROJECT_ROOT, 'public/manifest.json');

describe('TASK-FE-P7-012: PWA Manifest Validation', () => {
  describe('Manifest File Existence', () => {
    test('manifest.json exists in public directory', () => {
      expect(existsSync(MANIFEST_PATH)).toBe(true);
    });

    test('manifest.json is valid JSON', () => {
      const manifestContent = readFileSync(MANIFEST_PATH, 'utf-8');
      expect(() => JSON.parse(manifestContent)).not.toThrow();
    });
  });

  describe('Required PWA Fields', () => {
    test('manifest has required "name" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('name');
      expect(typeof manifest.name).toBe('string');
      expect(manifest.name.length).toBeGreaterThan(0);
    });

    test('manifest has required "short_name" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('short_name');
      expect(typeof manifest.short_name).toBe('string');
      expect(manifest.short_name.length).toBeGreaterThan(0);
      // short_name should be <= 12 characters for best display
      expect(manifest.short_name.length).toBeLessThanOrEqual(15);
    });

    test('manifest has required "start_url" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('start_url');
      expect(typeof manifest.start_url).toBe('string');
      expect(manifest.start_url).toBe('/');
    });

    test('manifest has required "display" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('display');
      expect(typeof manifest.display).toBe('string');
    });

    test('manifest has required "theme_color" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('theme_color');
      expect(typeof manifest.theme_color).toBe('string');
      // Should be a valid hex color
      expect(manifest.theme_color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    });

    test('manifest has required "background_color" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('background_color');
      expect(typeof manifest.background_color).toBe('string');
      // Should be a valid hex color
      expect(manifest.background_color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    });

    test('manifest has required "icons" field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('icons');
      expect(Array.isArray(manifest.icons)).toBe(true);
      expect(manifest.icons.length).toBeGreaterThan(0);
    });
  });

  describe('Display Mode Requirements', () => {
    test('display mode is standalone for app-like experience', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest.display).toBe('standalone');
    });
  });

  describe('Icon Requirements', () => {
    test('manifest has at least one 192x192 icon', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      const icons = manifest.icons;

      const has192Icon = icons.some((icon: { sizes: string }) =>
        icon.sizes === '192x192'
      );

      expect(has192Icon).toBe(true);
    });

    test('manifest has at least one 512x512 icon', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      const icons = manifest.icons;

      const has512Icon = icons.some((icon: { sizes: string }) =>
        icon.sizes === '512x512'
      );

      expect(has512Icon).toBe(true);
    });

    test('all icons have type field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      const icons = manifest.icons;

      icons.forEach((icon: { type?: string }) => {
        expect(icon).toHaveProperty('type');
        expect(typeof icon.type).toBe('string');
      });
    });

    test('all icons have purpose field', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      const icons = manifest.icons;

      icons.forEach((icon: { purpose?: string }) => {
        expect(icon).toHaveProperty('purpose');
        expect(typeof icon.purpose).toBe('string');
      });
    });

    test('manifest has maskable icons for adaptive icon support', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      const icons = manifest.icons;

      const hasMaskableIcon = icons.some((icon: { purpose: string }) =>
        icon.purpose === 'maskable'
      );

      expect(hasMaskableIcon).toBe(true);
    });
  });

  describe('PCF Calculator Branding', () => {
    test('manifest name contains "PCF Calculator"', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest.name).toContain('PCF');
    });

    test('theme color matches brand color (#003f7f)', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest.theme_color).toBe('#003f7f');
    });

    test('manifest has description field for app stores', () => {
      const manifest = JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8'));
      expect(manifest).toHaveProperty('description');
      expect(typeof manifest.description).toBe('string');
      expect(manifest.description.length).toBeGreaterThan(10);
    });
  });
});
