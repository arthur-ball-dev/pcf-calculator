/**
 * StepProgress accessible names contain their visible text (TASK-FE-FIX-006, issue #133)
 *
 * WCAG 2.5.3 Label in Name: a control's accessible name must contain its visible label, so a voice
 * control user who says "click 2. Edit BOM" reaches the button. The step buttons showed
 * "2. Edit BOM" but were named "Step 2 of 3: Edit BOM (current)", which axe reports as
 * label-content-name-mismatch (visual-ux-flow e2e Scenario 6).
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen } from '../../testUtils';
import { describe, test, expect, beforeEach } from 'vitest';
import StepProgress from '@/components/calculator/StepProgress';
import { WIZARD_STEPS } from '@/config/wizardSteps';
import { useWizardStore } from '@/store/wizardStore';

describe('StepProgress label in name (TASK-FE-FIX-006)', () => {
  beforeEach(() => {
    useWizardStore.setState({ currentStep: 'edit', completedSteps: ['select'] });
  });

  test('each step button\'s accessible name starts with its visible text', () => {
    render(<StepProgress steps={WIZARD_STEPS} currentStep="edit" />);
    const nav = screen.getByRole('navigation', { name: 'Wizard progress' });
    const buttons = Array.from(nav.querySelectorAll('button'));
    expect(buttons).toHaveLength(WIZARD_STEPS.length);

    for (const button of buttons) {
      const visible = (button.textContent ?? '').trim();
      const name = button.getAttribute('aria-label') ?? visible;
      expect(name.startsWith(visible), `"${name}" should start with "${visible}"`).toBe(true);
    }
  });

  test('the names still give position and state', () => {
    render(<StepProgress steps={WIZARD_STEPS} currentStep="edit" />);
    expect(screen.getByRole('button', { name: /^1\. Select Product, step 1 of 3 \(completed\)$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^2\. Edit BOM, step 2 of 3 \(current\)$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^3\. Results, step 3 of 3$/ })).toBeInTheDocument();
  });
});
