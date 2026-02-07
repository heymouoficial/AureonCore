/**
 * 🎴 ResponseCard Component
 * Displays structured AI responses as visual cards.
 * Inspired by Manus AI & GenSpark patterns.
 */
import React from 'react';
import ReasoningSteps from './ReasoningSteps';
import { SourceChip, CardAction } from './UIActions';
import { Search, Brain, Zap, BarChart2, Link, MessageSquare, Clock, Check, AlertCircle, X } from 'lucide-react';

const CardIcon = ({ type }) => {
  const icons = {
    research: <Search size={20} />,
    reasoning: <Brain size={20} />,
    action: <Zap size={20} />,
    data: <BarChart2 size={20} />,
    integration: <Link size={20} />,
    chat: <MessageSquare size={20} />
  };
  return <span className="card-type-icon">{icons[type] || <MessageSquare size={20} />}</span>;
};

const StatusBadge = ({ status }) => {
  const statusConfig = {
    pending: { color: 'var(--text-muted)', label: 'Pendiente', icon: <Clock size={12} /> },
    active: { color: 'var(--color-cyan)', label: 'Procesando', icon: <div className="spinner-small" /> },
    complete: { color: 'var(--color-emerald)', label: 'Completo', icon: <Check size={12} /> },
    failed: { color: 'var(--color-warm)', label: 'Error', icon: <AlertCircle size={12} /> }
  };

  const config = statusConfig[status] || statusConfig.complete;

  return (
    <span className="status-badge" style={{ color: config.color, borderColor: config.color }}>
      {config.icon} {config.label}
    </span>
  );
};

const ConfidenceMeter = ({ value }) => {
  if (!value) return null;
  const percentage = Math.round(value * 100);

  return (
    <div className="confidence-meter">
      <div className="confidence-bar" style={{ width: `${percentage}%` }} />
      <span className="confidence-label">{percentage}% confianza</span>
    </div>
  );
};

const SourceList = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="source-list">
      <span className="source-label">Fuentes ({sources.length}):</span>
      <div className="source-chips">
        {sources.map((source, i) => (
          <SourceChip
            key={i}
            label={source.title.length > 30 ? source.title.slice(0, 30) + '...' : source.title}
            icon="📄"
            onClick={() => window.open(source.url, '_blank')}
          />
        ))}
      </div>
    </div>
  );
};

const KeyPoints = ({ points }) => {
  if (!points || points.length === 0) return null;

  return (
    <ul className="key-points">
      {points.map((point, i) => (
        <li key={i} className="key-point">
          <span className="point-icon">{point.icon}</span>
          <span className="point-text">{point.text}</span>
        </li>
      ))}
    </ul>
  );
};

const ResponseCard = ({ card }) => {
  if (!card) return null;

  const {
    type,
    title,
    status,
    summary,
    content,
    key_points,
    sources,
    reasoning_steps,
    confidence,
    duration_ms
  } = card;

  return (
    <div className={`response-card card-${type}`}>
      {/* Header */}
      <div className="card-header">
        <div className="card-title-row">
          <CardIcon type={type} />
          <h3 className="card-title">{title}</h3>
        </div>
        <div className="card-meta">
          <StatusBadge status={status} />
          {duration_ms > 0 && (
            <span className="duration">⏱️ {(duration_ms / 1000).toFixed(1)}s</span>
          )}
        </div>
      </div>

      {/* Confidence */}
      {confidence && <ConfidenceMeter value={confidence} />}

      {/* Reasoning Steps (for reasoning cards) */}
      {type === 'reasoning' && reasoning_steps && (
        <ReasoningSteps steps={reasoning_steps} compact={true} title="Proceso de Razonamiento" />
      )}

      {/* Content */}
      <div className="card-body">
        {summary && <p className="card-summary">{summary}</p>}
        {content && <div className="card-content">{content}</div>}
        <KeyPoints points={key_points} />
      </div>

      {/* Sources */}
      <SourceList sources={sources} />

      {/* Actions */}
      <div className="card-actions">
        {type === 'research' && (
          <>
            <CardAction label="📖 Ver completo" />
            <CardAction label="🔗 Fuentes" />
          </>
        )}
        <CardAction label="💬 Preguntar más" primary />
      </div>
    </div>
  );
};

export default ResponseCard;
