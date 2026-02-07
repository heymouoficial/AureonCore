import React, { useState } from 'react';
import { Link2, CheckCircle } from 'lucide-react';
import { apiFetch } from '../lib/api';

export default function ChannelsPanel() {
    const [channel, setChannel] = useState('telegram');
    const [code, setCode] = useState('');
    const [identifier, setIdentifier] = useState('');
    const [linkInfo, setLinkInfo] = useState(null);
    const [status, setStatus] = useState(null);

    const requestCode = async () => {
        setStatus(null);
        const res = await apiFetch('/api/v1/channels/link', {
            method: 'POST',
            body: JSON.stringify({ channel }),
        });
        const data = await res.json();
        if (res.ok) {
            setLinkInfo(data);
            setCode(data.code || '');
        } else {
            setStatus(data?.detail || 'Error al generar código');
        }
    };

    const verify = async () => {
        setStatus(null);
        const res = await apiFetch('/api/v1/channels/verify', {
            method: 'POST',
            body: JSON.stringify({
                channel,
                code: code.trim(),
                channel_identifier: identifier.trim(),
            }),
        });
        const data = await res.json();
        if (res.ok) {
            setStatus(`Canal verificado: ${data.channel}`);
        } else {
            setStatus(data?.detail || 'Error al verificar');
        }
    };

    return (
        <div className="panel-frame">
            <div className="panel-header">
                <div className="panel-title">
                    <Link2 size={18} className="text-cyan-400" />
                    <span>Vincular Canales</span>
                </div>
            </div>

            <div className="panel-body">
                <div className="glass-panel channel-card">
                    <label>
                        Canal
                        <select value={channel} onChange={(e) => setChannel(e.target.value)}>
                            <option value="telegram">Telegram</option>
                            <option value="whatsapp">WhatsApp</option>
                        </select>
                    </label>

                    <button className="channel-btn" onClick={requestCode}>
                        Generar código
                    </button>

                    {linkInfo && (
                        <div className="channel-instructions">
                            Código: <strong>{linkInfo.code}</strong>
                            <p>{linkInfo.instructions}</p>
                        </div>
                    )}

                    <div className="channel-verify">
                        <input
                            type="text"
                            placeholder="Código"
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                        />
                        <input
                            type="text"
                            placeholder={channel === 'telegram' ? 'Telegram ID' : 'WhatsApp phone'}
                            value={identifier}
                            onChange={(e) => setIdentifier(e.target.value)}
                        />
                        <button onClick={verify}>
                            <CheckCircle size={16} /> Verificar
                        </button>
                    </div>

                    {status && <div className="channel-status">{status}</div>}
                </div>
            </div>
        </div>
    );
}
