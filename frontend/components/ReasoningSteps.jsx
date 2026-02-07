/**
 * 🧠 ReasoningSteps Component
 * Shows AI thinking process step-by-step.
 * Real-time updates during processing.
 */
import React, { useState, useEffect } from 'react';
import ThinkingCard from './ThinkingCard';

const ReasoningSteps = ({ steps, title = "PROCESANDO...", compact = false }) => {
  const [visibleSteps, setVisibleSteps] = useState([]);

  // Animate steps appearing
  useEffect(() => {
    if (!steps) return;

    const timer = setInterval(() => {
      setVisibleSteps(prev => {
        if (prev.length >= steps.length) {
          clearInterval(timer);
          return prev;
        }
        return [...prev, steps[prev.length]];
      });
    }, 300);

    return () => clearInterval(timer);
  }, [steps]);

  if (!steps || steps.length === 0) return null;

  const displaySteps = compact ? visibleSteps : steps;

  return (
    <ThinkingCard status="thinking" title={title}>
      <div className="reasoning-steps">
        {displaySteps.map((step, index) => (
          <StepItem
            key={step.number || index}
            step={step}
            isLast={index === displaySteps.length - 1}
          />
        ))}

        {visibleSteps.length < steps.length && (
          <div className="step-loading">
            <div className="loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
      </div>
    </ThinkingCard>
  );
};

const StepItem = ({ step, isLast }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete': return '✅';
      case 'active': return '🔄';
      case 'failed': return '❌';
      default: return '○';
    }
  };

  const getStepIcon = (description) => {
    const lower = description.toLowerCase();
    if (lower.includes('analiz')) return '🔍';
    if (lower.includes('busc')) return '🌐';
    if (lower.includes('sintetiz') || lower.includes('proces')) return '🧠';
    if (lower.includes('gener') || lower.includes('escrib')) return '✨';
    if (lower.includes('verific')) return '✓';
    if (lower.includes('ejecut')) return '⚡';
    return '➤';
  };

  return (
    <div className={`step-item status-${step.status || 'pending'} ${isLast ? 'is-last' : ''}`}>
      <div className="step-line">
        <div className="step-dot">
          <span className="step-icon">{getStepIcon(step.description)}</span>
        </div>
        {!isLast && <div className="step-connector" />}
      </div>

      <div className="step-content">
        <div className="step-main">
          <span className="step-description">{step.description}</span>
          <span className="step-status-icon">{getStatusIcon(step.status)}</span>
        </div>

        {step.result && (
          <div className="step-result">{step.result}</div>
        )}

        {step.duration_ms && (
          <span className="step-duration">{step.duration_ms}ms</span>
        )}
      </div>
    </div>
  );
};

export default ReasoningSteps;
