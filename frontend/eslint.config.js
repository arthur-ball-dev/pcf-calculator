import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Files that export a component plus its cva variants, config object or hook are the shadcn
      // and context patterns used throughout src; these named exports are fine for Fast Refresh.
      'react-refresh/only-export-components': [
        'error',
        {
          allowConstantExport: true,
          allowExportNames: [
            'badgeVariants',
            'buttonVariants',
            'DATA_DISCLAIMER_TEXT',
            'SOURCE_CONFIG',
            'useFormField',
            'useTour',
          ],
        },
      ],
      // Underscore-prefixed parameters and variables are intentionally unused.
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
      // vite.config.ts needs ts-nocheck for the Vite/Vitest plugin type clash; require a reason.
      '@typescript-eslint/ban-ts-comment': ['error', { 'ts-nocheck': 'allow-with-description' }],
    },
  },
])
