/**
 * Setup Verification Tests for TASK-FE-001
 *
 * These tests verify the Vite + React + TypeScript project setup is complete
 * with all required dependencies, configurations, and directory structure.
 *
 * Test Scenarios:
 * 1. Vite Configuration Test
 * 2. Dependency Verification Test
 * 3. Directory Structure Test
 * 4. TypeScript Configuration Test
 * 5. shadcn/ui Installation Test
 */

import { describe, test, expect } from 'vitest';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

const PROJECT_ROOT = join(__dirname, '..');

describe('TASK-FE-001: Project Setup Verification', () => {
  describe('Vite Configuration', () => {
    test('vite.config.ts exists', () => {
      const configPath = join(PROJECT_ROOT, 'vite.config.ts');
      expect(existsSync(configPath)).toBe(true);
    });

    test('vite.config.ts has React plugin configured', () => {
      const configPath = join(PROJECT_ROOT, 'vite.config.ts');
      const configContent = readFileSync(configPath, 'utf-8');

      // Verify React plugin import
      expect(configContent).toContain('@vitejs/plugin-react');

      // Verify React plugin usage
      expect(configContent).toContain('react()');
    });

    test('vite.config.ts has path aliases configured (@/* → src/*)', () => {
      const configPath = join(PROJECT_ROOT, 'vite.config.ts');
      const configContent = readFileSync(configPath, 'utf-8');

      // Verify path import
      expect(configContent).toContain('path');

      // Verify alias configuration
      expect(configContent).toContain('resolve');
      expect(configContent).toContain('alias');
      expect(configContent).toContain('@');
    });
  });

  describe('Dependency Verification', () => {
    test('package.json exists', () => {
      const packagePath = join(PROJECT_ROOT, 'package.json');
      expect(existsSync(packagePath)).toBe(true);
    });

    test('all required dependencies are installed', () => {
      const packagePath = join(PROJECT_ROOT, 'package.json');
      const packageContent = JSON.parse(readFileSync(packagePath, 'utf-8'));

      const requiredDeps = {
        // Core dependencies
        'zustand': '^4.5.0',
        'react-hook-form': '^7.51.0',
        '@hookform/resolvers': '^3.3.0',
        'zod': '^3.22.0',
        'axios': '^1.6.0',
        '@nivo/core': '^0.85.0',
        '@nivo/sankey': '^0.85.0',
      };

      const dependencies = packageContent.dependencies || {};

      Object.entries(requiredDeps).forEach(([dep, version]) => {
        expect(dependencies[dep]).toBeDefined();
        // Check major version matches
        const installedVersion = dependencies[dep].replace(/[\^~]/, '');
        const requiredVersion = version.replace(/[\^~]/, '');
        const installedMajor = installedVersion.split('.')[0];
        const requiredMajor = requiredVersion.split('.')[0];
        expect(installedMajor).toBe(requiredMajor);
      });
    });

    test('@types/node is installed as dev dependency', () => {
      const packagePath = join(PROJECT_ROOT, 'package.json');
      const packageContent = JSON.parse(readFileSync(packagePath, 'utf-8'));

      const devDependencies = packageContent.devDependencies || {};
      expect(devDependencies['@types/node']).toBeDefined();
    });
  });

  describe('Directory Structure', () => {
    test('src/ directory exists', () => {
      const srcPath = join(PROJECT_ROOT, 'src');
      expect(existsSync(srcPath)).toBe(true);
    });

    test('src/components/ directory structure exists', () => {
      const componentsDirs = [
        'src/components',
        'src/components/ui',
        'src/components/calculator',
        'src/components/forms',
        'src/components/visualizations',
      ];

      componentsDirs.forEach(dir => {
        const dirPath = join(PROJECT_ROOT, dir);
        expect(existsSync(dirPath)).toBe(true);
      });
    });

    test('src/lib/ directory exists', () => {
      const libPath = join(PROJECT_ROOT, 'src/lib');
      expect(existsSync(libPath)).toBe(true);
    });

    test('src/store/ directory structure exists', () => {
      const storeDirs = [
        'src/store',
        'src/store/slices',
      ];

      storeDirs.forEach(dir => {
        const dirPath = join(PROJECT_ROOT, dir);
        expect(existsSync(dirPath)).toBe(true);
      });
    });

    test('src/services/ directory exists', () => {
      const servicesPath = join(PROJECT_ROOT, 'src/services');
      expect(existsSync(servicesPath)).toBe(true);
    });

    test('src/types/ directory exists', () => {
      const typesPath = join(PROJECT_ROOT, 'src/types');
      expect(existsSync(typesPath)).toBe(true);
    });

    test('src/hooks/ directory exists', () => {
      const hooksPath = join(PROJECT_ROOT, 'src/hooks');
      expect(existsSync(hooksPath)).toBe(true);
    });
  });

  describe('TypeScript Configuration', () => {
    test('tsconfig.json exists', () => {
      const tsconfigPath = join(PROJECT_ROOT, 'tsconfig.json');
      expect(existsSync(tsconfigPath)).toBe(true);
    });

    test('tsconfig.json has strict mode enabled', () => {
      const tsconfigPath = join(PROJECT_ROOT, 'tsconfig.json');
      const tsconfigContent = readFileSync(tsconfigPath, 'utf-8');
      const tsconfig = JSON.parse(tsconfigContent);

      expect(tsconfig.compilerOptions?.strict).toBe(true);
    });

    test('tsconfig.json has path aliases configured', () => {
      const tsconfigPath = join(PROJECT_ROOT, 'tsconfig.json');
      const tsconfigContent = readFileSync(tsconfigPath, 'utf-8');
      const tsconfig = JSON.parse(tsconfigContent);

      expect(tsconfig.compilerOptions?.baseUrl).toBeDefined();
      expect(tsconfig.compilerOptions?.paths).toBeDefined();
      expect(tsconfig.compilerOptions?.paths?.['@/*']).toBeDefined();
    });
  });

  describe('shadcn/ui Installation', () => {
    test('components.json exists', () => {
      const componentsJsonPath = join(PROJECT_ROOT, 'components.json');
      expect(existsSync(componentsJsonPath)).toBe(true);
    });

    test('components.json has correct configuration', () => {
      const componentsJsonPath = join(PROJECT_ROOT, 'components.json');
      const componentsJson = JSON.parse(readFileSync(componentsJsonPath, 'utf-8'));

      // Verify style is "new-york"
      expect(componentsJson.style).toBe('new-york');

      // Verify base color is zinc
      expect(componentsJson.tailwind?.baseColor).toBe('zinc');

      // Verify CSS variables are enabled
      expect(componentsJson.tailwind?.cssVariables).toBe(true);
    });

    test('lib/utils.ts exists with cn() helper', () => {
      const utilsPath = join(PROJECT_ROOT, 'src/lib/utils.ts');
      expect(existsSync(utilsPath)).toBe(true);

      const utilsContent = readFileSync(utilsPath, 'utf-8');

      // Verify cn function exists
      expect(utilsContent).toContain('cn');
      expect(utilsContent).toContain('clsx');
      expect(utilsContent).toContain('twMerge');
    });

    test('all required shadcn/ui components are installed', () => {
      const requiredComponents = [
        'button',
        'card',
        'input',
        'label',
        'select',
        'form',
        'checkbox',
        'textarea',
        'alert',
        'toast',
        'dialog',
        'progress',
        'tabs',
        'separator',
      ];

      const componentsUiPath = join(PROJECT_ROOT, 'src/components/ui');

      requiredComponents.forEach(component => {
        const componentPath = join(componentsUiPath, `${component}.tsx`);
        expect(existsSync(componentPath)).toBe(true);
      });
    });

    test('tailwind.config.ts exists', () => {
      const tailwindConfigPath = join(PROJECT_ROOT, 'tailwind.config.ts');
      expect(existsSync(tailwindConfigPath)).toBe(true);
    });

    test('tailwind.config.ts has shadcn/ui theme configuration', () => {
      const tailwindConfigPath = join(PROJECT_ROOT, 'tailwind.config.ts');
      const tailwindConfig = readFileSync(tailwindConfigPath, 'utf-8');

      // Verify darkMode is configured
      expect(tailwindConfig).toContain('darkMode');

      // Verify content paths include src
      expect(tailwindConfig).toContain('content');
      expect(tailwindConfig).toContain('./src/**/*.{ts,tsx}');
    });
  });

  describe('Build and Development', () => {
    test('package.json has required scripts', () => {
      const packagePath = join(PROJECT_ROOT, 'package.json');
      const packageContent = JSON.parse(readFileSync(packagePath, 'utf-8'));

      const scripts = packageContent.scripts || {};

      // Verify dev script exists
      expect(scripts.dev).toBeDefined();
      expect(scripts.dev).toContain('vite');

      // Verify build script exists
      expect(scripts.build).toBeDefined();

      // Verify test script exists
      expect(scripts.test).toBeDefined();
    });
  });
});
