/**
 * ScenarioComparison Component
 *
 * Main comparison interface for PCF calculation scenarios.
 * Features:
 * - Split-pane layout for side-by-side comparison
 * - Synchronized scrolling between panes
 * - Delta visualization for emissions differences
 * - Alert when fewer than 2 scenarios selected
 */

import { useRef, useCallback, useMemo } from 'react';
import { useScenarioStore } from '@/store/scenarioStore';
import { ScenarioPanel } from './ScenarioPanel';
import { DeltaVisualization, type DeltaData } from './DeltaVisualization';
import { ComparisonHeader } from './ComparisonHeader';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

// ================================================================
// Type Definitions
// ================================================================

export interface ScenarioComparisonProps {
  className?: string;
}

// ================================================================
// Component
// ================================================================

export function ScenarioComparison({ className }: ScenarioComparisonProps) {
  // Get scenarios from store using selectors
  const scenarios = useScenarioStore((state) => state.getComparisonScenarios());
  const baseline = useScenarioStore((state) => state.getBaseline());

  // Refs for synchronized scrolling
  const scrollRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Synchronized scrolling handler
  const handleScroll = useCallback((sourceIndex: number) => {
    const sourceRef = scrollRefs.current[sourceIndex];
    if (!sourceRef) return;

    const scrollTop = sourceRef.scrollTop;
    const scrollLeft = sourceRef.scrollLeft;

    scrollRefs.current.forEach((ref, i) => {
      if (i !== sourceIndex && ref) {
        ref.scrollTop = scrollTop;
        ref.scrollLeft = scrollLeft;
      }
    });
  }, []);

  // Calculate deltas between scenarios
  const deltas = useMemo<DeltaData[] | null>(() => {
    if (scenarios.length < 2) return null;

    const baselineEmissions = baseline?.results?.total_emissions ?? 0;

    return scenarios.map((scenario) => {
      const emissions = scenario.results?.total_emissions ?? 0;
      const absolute = emissions - baselineEmissions;
      const percentage =
        baselineEmissions !== 0
          ? ((emissions - baselineEmissions) / baselineEmissions) * 100
          : 0;

      return {
        scenarioId: scenario.id,
        scenarioName: scenario.name,
        emissions,
        absoluteDelta: absolute,
        percentageDelta: percentage,
        direction:
          absolute > 0 ? 'increase' : absolute < 0 ? 'decrease' : 'same',
      };
    });
  }, [scenarios, baseline]);

  // Show alert when fewer than 2 scenarios
  if (scenarios.length < 2) {
    return (
      <Alert variant="default" className={className} role="alert">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Add at least 2 scenarios to compare. Go to Scenarios and click "Add to
          Comparison".
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div
      className={`h-full flex flex-col ${className || ''}`}
      data-testid="comparison-container"
      data-tour="scenario-compare"
    >
      <ComparisonHeader scenarios={scenarios} deltas={deltas} />

      <div className="flex-1 relative flex">
        {/* Left pane: First scenario */}
        <div
          ref={(el) => {
            scrollRefs.current[0] = el;
          }}
          onScroll={() => handleScroll(0)}
          className="flex-1 h-full overflow-auto p-4 border-r"
          data-testid="scenario-pane-left"
          style={{ overflow: 'auto' }}
          tabIndex={0}
        >
          <ScenarioPanel
            scenario={scenarios[0]}
            isBaseline={scenarios[0].id === baseline?.id}
          />
        </div>

        {/* Resizer - visual indicator */}
        <div className="w-1 bg-gray-200 hover:bg-blue-400 cursor-col-resize Resizer" />

        {/* Right pane: Second scenario */}
        <div
          ref={(el) => {
            scrollRefs.current[1] = el;
          }}
          onScroll={() => handleScroll(1)}
          className="flex-1 h-full overflow-auto p-4"
          data-testid="scenario-pane-right"
          style={{ overflow: 'auto' }}
          tabIndex={0}
        >
          <ScenarioPanel
            scenario={scenarios[1]}
            isBaseline={scenarios[1].id === baseline?.id}
            comparisonDelta={deltas?.find(
              (d) => d.scenarioId === scenarios[1].id
            )}
          />
        </div>
      </div>

      {/* Delta visualization footer */}
      {deltas && <DeltaVisualization deltas={deltas} />}
    </div>
  );
}
