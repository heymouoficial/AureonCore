import React, { useState, useEffect } from 'react';
import { Bot, Loader2, Zap, Brain, Code, PenTool, BarChart3, RefreshCw } from 'lucide-react';
import { apiFetch } from '../lib/api';

const NANO_ICONS = {
    researcher: Brain,
    coder: Code,
    writer: PenTool,
    analyst: BarChart3
};

const NANO_COLORS = {
    researcher: '#8b5cf6',
    coder: '#10b981',
    writer: '#f59e0b',
    analyst: '#3b82f6'
};

export default function NanoAureons() {
    const [fleet, setFleet] = useState([]);
    const [loading, setLoading] = useState(true);
    const [executing, setExecuting] = useState(null);
    const [taskInput, setTaskInput] = useState('');
    const [selectedNano, setSelectedNano] = useState(null);
    const [result, setResult] = useState(null);

    const fetchFleet = async () => {
        setLoading(true);
        try {
            const response = await apiFetch('/api/v1/nanoaureons');
            const data = await response.json();
            setFleet(data.fleet || []);
        } catch (error) {
            console.error('Fleet fetch failed:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFleet();
    }, []);

    const executeTask = async (nanoType) => {
        if (!taskInput.trim()) return;

        setExecuting(nanoType);
        setResult(null);

        try {
            const response = await apiFetch(`/api/v1/nanoaureons/${nanoType}/execute`, {
                method: 'POST',
                body: JSON.stringify({ task: taskInput })
            });
            const data = await response.json();
            setResult({
                nanoType,
                content: data.result || 'Sin resultado',
                success: data.status === 'success'
            });
        } catch (error) {
            setResult({
                nanoType,
                content: 'Error ejecutando tarea',
                success: false
            });
        } finally {
            setExecuting(null);
            fetchFleet(); // Refresh status
        }
    };

    const NanoCard = ({ nano }) => {
        const Icon = NANO_ICONS[nano.type] || Bot;
        const color = NANO_COLORS[nano.type] || '#8b5cf6';
        const isWorking = nano.status === 'working' || executing === nano.type;

        return (
            <div
                className={`nano-card ${isWorking ? 'working' : ''} ${selectedNano === nano.type ? 'selected' : ''}`}
                onClick={() => setSelectedNano(nano.type === selectedNano ? null : nano.type)}
                style={{ '--nano-color': color }}
            >
                <div className="nano-icon" style={{ background: `${color}20`, color }}>
                    {isWorking ? <Loader2 size={24} className="spin" /> : <Icon size={24} />}
                </div>
                <div className="nano-info">
                    <h4 className="nano-name">{nano.name}</h4>
                    <span className="nano-type">{nano.type}</span>
                </div>
                <div className={`nano-status ${nano.status}`}>
                    <span className="status-indicator"></span>
                    {isWorking ? 'Working...' : nano.status}
                </div>
            </div>
        );
    };

    return (
        <div className="nanoaureons-panel">
            <div className="panel-header">
                <div className="panel-title">
                    <Zap size={20} className="text-violet-400" />
                    <span>NanoAureons Fleet</span>
                </div>
                <button className="btn-icon" onClick={fetchFleet} disabled={loading}>
                    <RefreshCw size={16} className={loading ? 'spin' : ''} />
                </button>
            </div>

            {loading ? (
                <div className="panel-loading">
                    <Loader2 size={32} className="spin" />
                    <span>Conectando con la Fleet...</span>
                </div>
            ) : (
                <>
                    <div className="nano-grid">
                        {fleet.map((nano) => (
                            <NanoCard key={nano.id} nano={nano} />
                        ))}
                    </div>

                    {selectedNano && (
                        <div className="nano-executor">
                            <h4>Ejecutar tarea con NanoAureon.{selectedNano}</h4>
                            <div className="executor-input">
                                <input
                                    type="text"
                                    value={taskInput}
                                    onChange={(e) => setTaskInput(e.target.value)}
                                    placeholder="Describe la tarea..."
                                    disabled={executing}
                                />
                                <button
                                    onClick={() => executeTask(selectedNano)}
                                    disabled={executing || !taskInput.trim()}
                                    className="btn-execute"
                                >
                                    {executing ? <Loader2 size={18} className="spin" /> : <Zap size={18} />}
                                    Ejecutar
                                </button>
                            </div>
                        </div>
                    )}

                    {result && (
                        <div className={`nano-result ${result.success ? 'success' : 'error'}`}>
                            <h4>Resultado de {result.nanoType}:</h4>
                            <pre>{result.content}</pre>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
