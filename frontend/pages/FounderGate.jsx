import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain } from 'lucide-react';
import { supabase } from '../lib/supabase';

/**
 * Founder Gate — Acceso único al Cockpit Aureon
 * Solo: hola@multiversa.group, moshequantum@gmail.com
 */
export default function FounderGate() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
            if (signInError) throw signInError;
            navigate('/app', { replace: true });
        } catch (err) {
            setError(err.message || 'Error de autenticación');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-shell">
            <div className="auth-glow" />
            <div className="auth-panel glass-panel">
                <div className="auth-header">
                    <div className="flex items-center justify-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-chartreuse/10 border border-chartreuse/20 flex items-center justify-center">
                            <Brain size={24} className="text-chartreuse" />
                        </div>
                    </div>
                    <h1 className="text-2xl font-bold text-ivory">Cockpit Aureon</h1>
                    <p className="text-chartreuse/90 text-sm mt-1">Bienvenido, Founder</p>
                    <p className="text-gray-500 text-xs mt-2">Acceso exclusivo</p>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    <label>
                        Email
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="hola@multiversa.group"
                            required
                        />
                    </label>
                    <label>
                        Contraseña
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />
                    </label>

                    {error && <div className="auth-error">{error}</div>}

                    <button className="auth-submit" type="submit" disabled={loading}>
                        {loading ? 'Conectando...' : 'Entrar al Cockpit'}
                    </button>
                </form>

                <p className="text-center text-gray-500 text-xs mt-6">
                    MultiversaGroup · AureonCore
                </p>
            </div>
        </div>
    );
}
