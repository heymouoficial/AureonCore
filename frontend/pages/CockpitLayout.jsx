import React, { useState, useEffect } from 'react';
import { Activity, Brain, MessageCircle, Zap, Settings, Database, Users, Menu, X, FileText, Search, Link2, LogOut, PanelLeftClose, PanelLeft } from 'lucide-react';
import { ThemeProvider } from '../components/ThemeProvider';
import ThemeSwitcher from '../components/ThemeSwitcher';
import Chat from '../components/Chat';
import NanoAureons from '../components/NanoAureons';
import Integrations from '../components/Integrations';
import Profile from '../components/Profile';
import ResearchPanel from '../components/ResearchPanel';
import KnowledgePanel from '../components/KnowledgePanel';
import ChannelsPanel from '../components/ChannelsPanel';
import { apiFetch, API_URL } from '../lib/api';
import { useAuth } from '../context/AuthContext';

function CockpitLayout() {
    const { user, signOut } = useAuth();
    const [brainStatus, setBrainStatus] = useState(null);
    const [agents, setAgents] = useState([]);
    const [tenant, setTenant] = useState(null);
    const [view, setView] = useState('chat');
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    useEffect(() => {
        fetch(`${API_URL}/health`)
            .then(res => res.json())
            .then(data => setBrainStatus(data))
            .catch(() => setBrainStatus(null));

        async function fetchTenant() {
            try {
                const res = await apiFetch('/api/v1/tenants/me');
                const data = await res.json();
                if (data?.tenant) {
                    setTenant(data.tenant);
                }
            } catch (err) {
                console.error('Tenant fetch failed', err);
            }
        }

        async function fetchFleet() {
            try {
                const res = await apiFetch('/api/v1/nanoaureons');
                const data = await res.json();
                setAgents(data.fleet || []);
            } catch (err) {
                console.error('Fleet fetch failed', err);
            }
        }

        fetchTenant();
        fetchFleet();
    }, []);

    const NavButton = ({ icon: Icon, label, targetView }) => (
        <button
            onClick={() => { setView(targetView); setMobileMenuOpen(false); }}
            className={`nav-btn ${view === targetView ? 'active' : ''}`}
        >
            <Icon size={20} />
            <span>{label}</span>
        </button>
    );

    return (
        <ThemeProvider>
            {view === 'chat' && (
                <div className="fullscreen-chat">
                    <Chat onOpenMenu={() => setMobileMenuOpen(true)} onNavigate={setView} userId={user?.id} />
                </div>
            )}

            {view !== 'chat' && (
                <div className={`app-container ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
                    <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''} ${sidebarCollapsed ? 'collapsed' : ''}`}>
                        <div className="sidebar-header">
                            <Brain size={28} className="text-violet-400 flex-shrink-0" />
                            <div className="sidebar-title">CortexOS</div>
                            <button
                                className="sidebar-collapse-btn ml-auto"
                                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                                title={sidebarCollapsed ? 'Expandir' : 'Colapsar'}
                                aria-label={sidebarCollapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
                            >
                                {sidebarCollapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
                            </button>
                            <button className="mobile-close" onClick={() => setMobileMenuOpen(false)}>
                                <X size={24} />
                            </button>
                        </div>

                        <div className="tenant-chip">
                            <div className="tenant-label">Tenant</div>
                            <div className="tenant-name">{tenant?.name || 'Cargando...'}</div>
                        </div>

                        <nav className="sidebar-nav">
                            <NavButton icon={MessageCircle} label="Chat" targetView="chat" />
                            <NavButton icon={Search} label="Research" targetView="research" />
                            <NavButton icon={FileText} label="Knowledge" targetView="knowledge" />
                            <NavButton icon={Zap} label="NanoAureons" targetView="nanoaureons" />
                            <NavButton icon={Link2} label="Canales" targetView="channels" />
                            <NavButton icon={Database} label="Integraciones" targetView="integrations" />
                            <NavButton icon={Activity} label="Panel" targetView="dashboard" />
                            <NavButton icon={Settings} label="Perfil" targetView="settings" />
                        </nav>

                        <div className="sidebar-footer">
                            <ThemeSwitcher />
                            <button className="signout-btn" onClick={signOut}>
                                <LogOut size={16} />
                                Cerrar sesión
                            </button>
                            <div className="system-status">
                                <span className={`status-dot ${brainStatus ? 'online' : 'offline'}`}></span>
                                <span>{brainStatus?.status || 'Conectando...'}</span>
                            </div>
                        </div>
                    </aside>

                    <header className="mobile-header">
                        <button className="menu-toggle" onClick={() => setMobileMenuOpen(true)}>
                            <Menu size={24} />
                        </button>
                        <div className="mobile-title">
                            <Brain size={24} className="text-violet-400" />
                            <span>CortexOS</span>
                        </div>
                    </header>

                    <main className="main-content">
                        {view === 'nanoaureons' && <NanoAureons />}
                        {view === 'research' && <ResearchPanel />}
                        {view === 'knowledge' && <KnowledgePanel />}
                        {view === 'integrations' && <Integrations />}
                        {view === 'channels' && <ChannelsPanel />}

                        {view === 'dashboard' && (
                            <div className="dashboard-grid">
                                <div className="glass-panel">
                                    <h2 className="panel-title">
                                        <Activity size={20} className="text-emerald-400" />
                                        Estado del Sistema
                                    </h2>
                                    <div className="status-row">
                                        <span className={`status-dot ${brainStatus ? 'online' : 'offline'}`}></span>
                                        <span>Cortex: {brainStatus ? 'EN LÍNEA' : 'OFFLINE'}</span>
                                    </div>
                                    <p className="status-message">
                                        {brainStatus?.message || 'Núcleo neuronal activo'}
                                    </p>
                                </div>

                                <div className="glass-panel">
                                    <h2 className="panel-title">
                                        <Database size={20} className="text-blue-400" />
                                        Tenants
                                    </h2>
                                    <ul className="tenant-list">
                                        {tenant ? (
                                            <li className="tenant-item">
                                                <strong>{tenant.name}</strong>
                                                <span className="tier-badge">owner</span>
                                            </li>
                                        ) : (
                                            <p className="empty-state">No hay tenants cargados</p>
                                        )}
                                    </ul>
                                </div>

                                <div className="glass-panel">
                                    <h2 className="panel-title">
                                        <Users size={20} className="text-amber-400" />
                                        NanoAureons
                                    </h2>
                                    {agents.length > 0 ? (
                                        <ul className="agent-list">
                                            {agents.map(agent => (
                                                <li key={agent.id} className="agent-item">
                                                    <span>{agent.name}</span>
                                                    <span className="agent-status">{agent.status}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : <p className="empty-state">Flota lista para instrucciones</p>}
                                </div>
                            </div>
                        )}

                        {view === 'settings' && (
                            <div className="settings-grid">
                                <Profile />
                            </div>
                        )}
                    </main>

                    {mobileMenuOpen && <div className="sidebar-overlay" onClick={() => setMobileMenuOpen(false)} />}
                </div>
            )}
        </ThemeProvider>
    );
}

export default CockpitLayout;
