import React from 'react';

export const SourceChip = ({ label, icon, onClick }) => (
    <button className="source-chip" onClick={onClick}>
        {icon && <span className="source-icon">{icon}</span>}
        <span>{label}</span>
    </button>
);

export const CardAction = ({ label, onClick, primary = false }) => (
    <button className={`card-action ${primary ? 'primary' : ''}`} onClick={onClick}>
        {label}
    </button>
);
