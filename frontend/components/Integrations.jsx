import React, { useEffect, useState } from 'react';
import { Key, Save, Loader, Check } from 'lucide-react';
import { apiFetch } from '../lib/api';

const DEFAULT_KEYS = [
    { key: 'TAVILY_API_KEY', description: 'Tavily (research)' },
    { key: 'GEMINI_API_KEY', description: 'Google Gemini' },
    { key: 'GROQ_API_KEY', description: 'Groq' },
    { key: 'MISTRAL_API_KEY', description: 'Mistral' },
    { key: 'WHATSAPP_API_TOKEN', description: 'Meta Cloud API token' },
    { key: 'TELEGRAM_BOT_TOKEN', description: 'Telegram bot token' },
];

export default function Integrations() {
    const [secrets, setSecrets] = useState(DEFAULT_KEYS);
    const [activeKey, setActiveKey] = useState(null);
    const [value, setValue] = useState('');
    const [loading, setLoading] = useState(false);
    const [savedKeys, setSavedKeys] = useState([]);

    useEffect(() => {
        const fetchKeys = async () => {
            const res = await apiFetch('/api/v1/integrations');
            const data = await res.json();
            if (res.ok) {
                setSavedKeys((data.integrations || []).map((i) => i.key));
            }
        };
        fetchKeys();
    }, []);

    const saveSecret = async (key) => {
        setLoading(true);
        try {
            const res = await apiFetch('/api/v1/integrations', {
                method: 'POST',
                body: JSON.stringify({ key, value })
            });
            const data = await res.json();
            if (res.ok) {
                setSavedKeys(prev => Array.from(new Set([...prev, key])));
                setValue('');
                setActiveKey(null);
            } else {
                alert(data.detail || 'Error guardando secreto');
            }
        } catch (err) {
            console.error(err);
            alert('Error guardando secreto');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="panel-frame">
            <div className="panel-header">
                <div className="panel-title">
                    <Key size={18} className="text-amber-400" />
                    <span>Integraciones</span>
                </div>
            </div>
            <div className="panel-body">
                <ul className="integration-list">
                    {secrets.map(s => (
                        <li key={s.key} className="integration-item glass-panel">
                            <div className="integration-head">
                                <div>
                                    <strong>{s.key}</strong>
                                    <small>{s.description}</small>
                                </div>
                                {savedKeys.includes(s.key) && (
                                    <span className="integration-saved">
                                        <Check size={14} /> Guardado
                                    </span>
                                )}
                            </div>
                            {activeKey === s.key ? (
                                <div className="integration-form">
                                    <input
                                        type="password"
                                        placeholder="Pega el secreto aquí"
                                        value={value}
                                        onChange={(e) => setValue(e.target.value)}
                                    />
                                    <button onClick={() => saveSecret(s.key)} disabled={loading || !value.trim()}>
                                        {loading ? <Loader size={16} className="spin" /> : <Save size={16} />}
                                    </button>
                                </div>
                            ) : (
                                <button
                                    onClick={() => setActiveKey(s.key)}
                                    className="integration-btn"
                                >
                                    Configurar
                                </button>
                            )}
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
