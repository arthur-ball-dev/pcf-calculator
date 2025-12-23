/**
 * TypeScript Any Elimination Validation Script Tests
 *
 * TASK-FE-P7-026: Script-based tests to verify TypeScript `any` types have been eliminated.
 *
 * These tests use file system checks to audit the codebase for `any` usage and verify
 * TypeScript strict mode is enabled and passing.
 *
 * Validation Categories:
 * 1. Source file audit for any patterns (excluding test files)
 * 2. TypeScript strict mode compilation check
 * 3. Specific file validation for known any usages
 * 4. Required type definition files existence check
 */

import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

// =============================================================================
// Configuration
// =============================================================================

// Get the frontend root directory (src/__tests__ -> src -> frontend)
const FRONTEND_ROOT = path.resolve(__dirname, '../..');

/**
 * Files that are known to have `any` types before the fix.
 * After TASK-FE-P7-026 is complete, these should have proper types.
 */
const FILES_WITH_KNOWN_ANY_TYPES = [
  'src/components/visualizations/SankeyDiagram.tsx',
  'src/components/forms/BOMTableRow.tsx',
];

/**
 * Patterns that indicate `any` usage in TypeScript.
 * These should not exist in source files.
 */
const ANY_TYPE_PATTERNS = [
  /:\s*any\b/,         // Direct any type annotation (: any)
  /:\s*any\[\]/,       // Any array
  /<any>/,             // Generic any
  /as\s+any\b/,        // Type assertion to any
];

/**
 * Check if a line is an eslint-disable comment that allows the next line.
 */
function isEslintDisableComment(line: string): boolean {
  return line.includes('eslint-disable') && line.includes('@typescript-eslint/no-explicit-any');
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Search for any types INCLUDING those disabled by eslint.
 * This shows ALL any types that need proper typing.
 */
function findAllAnyTypesInFile(filePath: string): Array<{ line: number; content: string; disabled: boolean }> {
  const fullPath = path.join(FRONTEND_ROOT, filePath);

  if (!fs.existsSync(fullPath)) {
    console.log(`File not found: ${fullPath}`);
    return [];
  }

  const content = fs.readFileSync(fullPath, 'utf-8');
  const lines = content.split('\n');
  const matches: Array<{ line: number; content: string; disabled: boolean }> = [];

  lines.forEach((line, index) => {
    // Skip if this line is an eslint-disable comment
    if (line.includes('eslint-disable')) {
      return;
    }

    // Check if the previous line is an eslint-disable-next-line comment
    const prevLine = index > 0 ? lines[index - 1] : '';
    const isDisabledByPrevLine = isEslintDisableComment(prevLine ?? '');

    // Check for any type patterns
    for (const pattern of ANY_TYPE_PATTERNS) {
      if (pattern.test(line)) {
        matches.push({
          line: index + 1,
          content: line.trim(),
          disabled: isDisabledByPrevLine,
        });
        break; // Only add once per line
      }
    }
  });

  return matches;
}

/**
 * Execute a shell command and return output.
 */
function execCommand(command: string): { stdout: string; stderr: string; exitCode: number } {
  try {
    const stdout = execSync(command, {
      cwd: FRONTEND_ROOT,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { stdout, stderr: '', exitCode: 0 };
  } catch (error: unknown) {
    const execError = error as { stdout?: string; stderr?: string; status?: number };
    return {
      stdout: execError.stdout || '',
      stderr: execError.stderr || '',
      exitCode: execError.status || 1,
    };
  }
}

// =============================================================================
// Test Suite: Any Type Audit
// =============================================================================

describe('TypeScript Any Elimination Audit', () => {
  describe('Source File Any Type Search', () => {
    /**
     * Test that searches for any patterns in SOURCE files (excluding tests).
     * This test counts ALL any types in non-test source files.
     * After fix, there should be ZERO any types.
     */
    it('should find zero any patterns in source files (excluding tests)', () => {
      // Use grep to find any patterns, excluding test files
      const result = execCommand(
        'grep -rn ": any" --include="*.ts" --include="*.tsx" ' +
        '--exclude-dir="__tests__" --exclude-dir="test" --exclude-dir="tests" ' +
        'src/ 2>/dev/null || true'
      );

      const lines = result.stdout.split('\n').filter(line => line.trim());

      // Filter out lines that are just comments (not actual any types)
      const anyTypeLines = lines.filter(line => {
        // Skip eslint-disable comment lines themselves
        if (line.includes('eslint-disable')) return false;
        // Skip test files that might have slipped through
        if (line.includes('__tests__') || line.includes('.test.') || line.includes('.spec.')) return false;
        // Must contain `: any` pattern (actual code, not comments about any)
        return /:\s*any\b/.test(line);
      });

      // Document what was found
      if (anyTypeLines.length > 0) {
        console.log(`Found ${anyTypeLines.length} any type usages in source files:`);
        anyTypeLines.forEach(v => console.log(`  ${v}`));
      }

      // This assertion will FAIL if any types exist
      // After TASK-FE-P7-026 is complete, this should PASS
      expect(anyTypeLines.length).toBe(0);
    });

    /**
     * Test that specifically checks the known files with any types.
     * This test finds ALL any types including those with eslint-disable.
     */
    it('should have zero any types in SankeyDiagram.tsx (including disabled)', () => {
      const matches = findAllAnyTypesInFile('src/components/visualizations/SankeyDiagram.tsx');

      if (matches.length > 0) {
        console.log('SankeyDiagram.tsx any type usages:');
        matches.forEach(m => console.log(`  Line ${m.line}: ${m.content} ${m.disabled ? '(eslint-disabled)' : ''}`));
      }

      // This will FAIL until SankeyDiagram is fixed with proper types
      expect(matches.length).toBe(0);
    });

    /**
     * Test that specifically checks BOMTableRow for any types.
     * This test finds ALL any types including those with eslint-disable.
     */
    it('should have zero any types in BOMTableRow.tsx (including disabled)', () => {
      const matches = findAllAnyTypesInFile('src/components/forms/BOMTableRow.tsx');

      if (matches.length > 0) {
        console.log('BOMTableRow.tsx any type usages:');
        matches.forEach(m => console.log(`  Line ${m.line}: ${m.content} ${m.disabled ? '(eslint-disabled)' : ''}`));
      }

      // This will FAIL until BOMTableRow is fixed with proper types
      expect(matches.length).toBe(0);
    });
  });

  describe('TypeScript Strict Mode Validation', () => {
    /**
     * Test that tsconfig.json has strict mode enabled.
     */
    it('should have strict: true in tsconfig.json', () => {
      const tsconfigPath = path.join(FRONTEND_ROOT, 'tsconfig.json');
      expect(fs.existsSync(tsconfigPath)).toBe(true);

      const content = fs.readFileSync(tsconfigPath, 'utf-8');
      const config = JSON.parse(content);

      expect(config.compilerOptions?.strict).toBe(true);
    });

    /**
     * Test that tsconfig.app.json has strict mode enabled.
     * Note: tsconfig.app.json may contain comments, so we check for the string.
     */
    it('should have strict: true in tsconfig.app.json', () => {
      const tsconfigPath = path.join(FRONTEND_ROOT, 'tsconfig.app.json');
      expect(fs.existsSync(tsconfigPath)).toBe(true);

      const content = fs.readFileSync(tsconfigPath, 'utf-8');

      // Check for strict: true pattern in the file (handles comments in JSON)
      expect(content).toMatch(/"strict"\s*:\s*true/);
    });

    /**
     * Test that TypeScript compilation passes without errors.
     * This validates that the codebase compiles with strict mode.
     */
    it('should pass TypeScript compilation check', () => {
      // Run tsc --noEmit to check for type errors
      const result = execCommand('npx tsc --noEmit 2>&1 || true');

      // Count the number of error lines
      const errorLines = result.stdout.split('\n').filter(
        line => line.includes('error TS')
      );

      if (errorLines.length > 0) {
        console.log('TypeScript errors found:');
        errorLines.slice(0, 10).forEach(e => console.log(`  ${e}`)); // Show first 10
        if (errorLines.length > 10) {
          console.log(`  ... and ${errorLines.length - 10} more`);
        }
      }

      // This will FAIL if there are TypeScript errors
      expect(errorLines.length).toBe(0);
    });
  });

  describe('Specific Type Definition Validation', () => {
    /**
     * Test that Nivo type definitions exist.
     * After fix, frontend/src/types/nivo.d.ts should exist.
     */
    it('should have Nivo type definitions file', () => {
      const nivoTypesPath = path.join(FRONTEND_ROOT, 'src/types/nivo.d.ts');

      // This will FAIL until nivo.d.ts is created
      expect(fs.existsSync(nivoTypesPath)).toBe(true);
    });

    /**
     * Test that Nivo type definitions have required types.
     */
    it('should have PCFSankeyNode type in nivo.d.ts', () => {
      const nivoTypesPath = path.join(FRONTEND_ROOT, 'src/types/nivo.d.ts');

      if (!fs.existsSync(nivoTypesPath)) {
        // Skip if file doesn't exist yet (will fail in previous test)
        expect.fail('nivo.d.ts does not exist');
        return;
      }

      const content = fs.readFileSync(nivoTypesPath, 'utf-8');

      // Check for required type definitions
      expect(content).toContain('PCFSankeyNode');
      expect(content).toContain('SankeyNodeClickEvent');
    });

    /**
     * Test that BOMTableRow has proper field types (not any).
     */
    it('should have proper field type in BOMTableRow.tsx (not any)', () => {
      const bomTableRowPath = path.join(FRONTEND_ROOT, 'src/components/forms/BOMTableRow.tsx');
      expect(fs.existsSync(bomTableRowPath)).toBe(true);

      const content = fs.readFileSync(bomTableRowPath, 'utf-8');

      // After fix, field prop should NOT be `any`
      // This checks for the literal string "field: any"
      const hasAnyFieldType = content.includes('field: any');

      // This will FAIL until BOMTableRow is fixed
      expect(hasAnyFieldType).toBe(false);
    });
  });

  describe('ESLint Configuration Validation', () => {
    /**
     * Test that ESLint config exists in the frontend.
     */
    it('should have ESLint configuration', () => {
      // Check for eslint config files
      const configPaths = [
        path.join(FRONTEND_ROOT, 'eslint.config.js'),
        path.join(FRONTEND_ROOT, 'eslint.config.mjs'),
        path.join(FRONTEND_ROOT, '.eslintrc.js'),
        path.join(FRONTEND_ROOT, '.eslintrc.json'),
      ];

      let foundConfig = false;

      for (const configPath of configPaths) {
        if (fs.existsSync(configPath)) {
          foundConfig = true;
          break;
        }
      }

      expect(foundConfig).toBe(true);
    });
  });
});

// =============================================================================
// Summary Report
// =============================================================================

describe('TypeScript Any Audit Summary', () => {
  it('should generate comprehensive audit report', () => {
    console.log('\n=== TypeScript Any Audit Report ===\n');

    let totalAnyTypes = 0;
    let totalDisabled = 0;
    const fileResults: Array<{ file: string; count: number; disabled: number; lines: number[] }> = [];

    // Check all known files
    for (const file of FILES_WITH_KNOWN_ANY_TYPES) {
      const matches = findAllAnyTypesInFile(file);
      const disabledCount = matches.filter(m => m.disabled).length;
      totalAnyTypes += matches.length;
      totalDisabled += disabledCount;
      fileResults.push({
        file,
        count: matches.length,
        disabled: disabledCount,
        lines: matches.map(m => m.line),
      });
    }

    console.log('Files audited for any types:');
    for (const result of fileResults) {
      console.log(`  ${result.file}:`);
      console.log(`    Total any types: ${result.count}`);
      console.log(`    Eslint-disabled: ${result.disabled}`);
      console.log(`    Non-disabled:    ${result.count - result.disabled}`);
      if (result.lines.length > 0) {
        console.log(`    Lines: ${result.lines.join(', ')}`);
      }
    }

    console.log(`\n--- Summary ---`);
    console.log(`Total any types found: ${totalAnyTypes}`);
    console.log(`  - Eslint-disabled: ${totalDisabled}`);
    console.log(`  - Non-disabled: ${totalAnyTypes - totalDisabled}`);
    console.log('\n=== End of Report ===\n');

    // This report test always passes - it's for documentation
    // The actual assertions are in the individual tests above
    expect(true).toBe(true);
  });
});
