import React, { useState } from 'react';
import { Search, ExternalLink } from 'lucide-react';
import { apiFetch } from '../lib/api';

export default function ResearchPanel() {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const runSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const res = await apiFetch('/api/v1/research', {
                method: 'POST',
                body: JSON.stringify({ query, k: 5 }),
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data?.detail || 'Error de investigación');
            }
            setResult(data);
        } catch (err) {
            setError(err.message || 'Error de investigación');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="panel-frame">
            <div className="panel-header">
                <div className="panel-title">
                    <Search size={18} className="text-cyan-400" />
                    <span>Research Cortex</span>
                </div>
            </div>

            <div className="panel-body">
                <div className="research-input">
                    <input
                        type="text"
                        placeholder="Pregunta con fuentes verificadas..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button onClick={runSearch} disabled={loading || !query.trim()}>
                        {loading ? 'Buscando...' : 'Investigar'}
                    </button>
                </div>

                {error && <div className="panel-error">{error}</div>}

                {result && (
                    <div className="research-result glass-panel">
                        <h3>Respuesta</h3>
                        <p>{result.answer || 'Sin respuesta'}</p>

                        <div className="citation-list">
                            <h4>Fuentes</h4>
                            {(result.citations || []).map((c, idx) => (
                                <div key={idx} className="citation-item">
                                    <div>
                                        <strong>{c.title}</strong>
                                        <p>{c.snippet}</p>
                                    </div>
                                    {c.url && (
                                        <a href={c.url} target="_blank" rel="noreferrer">
                                            <ExternalLink size={14} />
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
