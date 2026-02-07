import React, { useState, useEffect } from 'react';
import { User, Settings } from 'lucide-react';
import { apiFetch } from '../lib/api';

export default function Profile() {
    const [profile, setProfile] = useState(null);

    useEffect(() => {
        apiFetch('/api/v1/auth/profile')
            .then(res => res.json())
            .then(data => setProfile(data))
            .catch(err => console.error(err));
    }, []);

    if (!profile) return <div className="panel-loading">Cargando perfil...</div>;

    return (
        <div className="glass-panel profile-card">
            <h2 className="panel-title">
                <User size={20} className="text-cyan-400" /> Cortex Profile
            </h2>
            <div className="profile-row">
                <div className="profile-avatar">
                    {profile.display_name?.slice(0, 2) || 'AU'}
                </div>
                <div>
                    <h3>{profile.display_name || profile.email}</h3>
                    <span className="tier-badge">{(profile.tier || 'trial').toUpperCase()}</span>
                </div>
            </div>
            <div className="profile-preferences">
                <p><Settings size={16} /> Preferencias</p>
                <div className="preferences-grid">
                    <div>Idioma: <strong>{profile.preferences?.language || 'es'}</strong></div>
                    <div>Zona: <strong>{profile.preferences?.timezone || 'America/Caracas'}</strong></div>
                </div>
            </div>
        </div>
    );
}
