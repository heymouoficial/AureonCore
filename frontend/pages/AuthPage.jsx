import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function AuthPage() {
    const [mode, setMode] = useState('login');
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
            if (mode === 'login') {
                const { error: signInError } = await supabase.auth.signInWithPassword({
                    email,
                    password,
                });
                if (signInError) throw signInError;
                navigate('/app');
            } else {
                const { error: signUpError } = await supabase.auth.signUp({
                    email,
                    password,
                });
                if (signUpError) throw signUpError;
                navigate('/app');
            }
        } catch (err) {
            setError(err.message || 'Error de autenticación');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-shell">
            <div className="auth-glow"></div>
            <div className="auth-panel glass-panel">
                <div className="auth-header">
                    <div className="auth-brand">Auréon OS</div>
                    <p>Accede al Cockpit Cortex</p>
                </div>

                <div className="auth-tabs">
                    <button
                        className={mode === 'login' ? 'active' : ''}
                        onClick={() => setMode('login')}
                        type="button"
                    >
                        Ingresar
                    </button>
                    <button
                        className={mode === 'signup' ? 'active' : ''}
                        onClick={() => setMode('signup')}
                        type="button"
                    >
                        Crear cuenta
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    <label>
                        Email
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="tu@email.com"
                            required
                        />
                    </label>
                    <label>
                        Password
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
                        {loading ? 'Conectando...' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
                    </button>
                </form>

                <div className="auth-footer">
                    <Link to="/">Volver al portal</Link>
                </div>
            </div>
        </div>
    );
}
