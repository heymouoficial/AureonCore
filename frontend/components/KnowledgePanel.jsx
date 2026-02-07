import React, { useState } from 'react';
import { Upload, Search } from 'lucide-react';
import { apiFetch } from '../lib/api';

export default function KnowledgePanel() {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState(null);

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setError(null);
        setUploadResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            const res = await apiFetch('/api/v1/knowledge/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.detail || 'Upload failed');
            setUploadResult(data);
        } catch (err) {
            setError(err.message || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const handleSearch = async () => {
        if (!query.trim()) return;
        setSearching(true);
        setError(null);
        try {
            const res = await apiFetch(`/api/v1/knowledge/search?query=${encodeURIComponent(query)}&k=5`);
            const data = await res.json();
            if (!res.ok) throw new Error(data?.detail || 'Search failed');
            setResults(data.results || []);
        } catch (err) {
            setError(err.message || 'Search failed');
        } finally {
            setSearching(false);
        }
    };

    return (
        <div className="panel-frame">
            <div className="panel-header">
                <div className="panel-title">
                    <Upload size={18} className="text-emerald-400" />
                    <span>Knowledge Vault</span>
                </div>
            </div>

            <div className="panel-body">
                <div className="upload-card glass-panel">
                    <h3>Subir documento</h3>
                    <div className="upload-row">
                        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
                        <button onClick={handleUpload} disabled={uploading || !file}>
                            {uploading ? 'Subiendo...' : 'Ingestar'}
                        </button>
                    </div>
                    {uploadResult && (
                        <div className="upload-result">
                            Ingesta completa · {uploadResult.chunk_count} chunks
                        </div>
                    )}
                </div>

                <div className="search-card glass-panel">
                    <h3>Buscar en conocimiento</h3>
                    <div className="research-input">
                        <input
                            type="text"
                            placeholder="Consulta semántica..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button onClick={handleSearch} disabled={searching || !query.trim()}>
                            {searching ? 'Buscando...' : 'Buscar'}
                        </button>
                    </div>
                    <div className="knowledge-results">
                        {results.map((r, idx) => (
                            <div key={idx} className="knowledge-item">
                                <div className="knowledge-sim">{r.similarity ? `${(r.similarity * 100).toFixed(1)}%` : '—'}</div>
                                <p>{r.chunk_text}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {error && <div className="panel-error">{error}</div>}
            </div>
        </div>
    );
}
