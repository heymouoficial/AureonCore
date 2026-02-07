import React from 'react';

/**
 * ThinkingCard Component
 * Displays the AI's reasoning process in a glassmorphic card.
 * Part of the LiquidGlass UI system.
 */
const ThinkingCard = ({ children, status = 'thinking', title = 'PENSANDO...' }) => {
    return (
        <div className={`thinking-card status-${status}`}>
            <div className="thinking-card-header">
                <div className="status-icon"></div>
                <span className="status-text">{title}</span>
            </div>
            <div className="thinking-content">
                {children}
            </div>
        </div>
    );
};

export default ThinkingCard;
