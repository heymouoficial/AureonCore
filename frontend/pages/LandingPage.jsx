import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Brain, Zap, Database, Users } from 'lucide-react';
import ShinyText from '../components/reactbits/ShinyText';
import StarBorder from '../components/reactbits/StarBorder';
import SpotlightCard from '../components/reactbits/SpotlightCard';

const LandingPage = () => {
    return (
        <div className="min-h-screen bg-[#050505] text-white overflow-hidden relative selection:bg-cyan-500/30 font-sans">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-cyan-900/10 rounded-full blur-[120px]" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-emerald-900/5 rounded-full blur-[150px]" />
            </div>

            {/* Nav */}
            <nav className="relative z-50 flex items-center justify-between px-6 py-6 max-w-7xl mx-auto backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#050505] to-[#12161f] border border-white/10 flex items-center justify-center shadow-lg shadow-cyan-900/20">
                        <Brain size={20} className="text-cyan-400" />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-white">Auréon<span className="text-cyan-400">OS</span></span>
                </div>
                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
                    <a href="#features" className="hover:text-white transition-colors duration-300">Capacidades</a>
                    <a href="#memory" className="hover:text-white transition-colors duration-300">Memoria Cortex</a>
                    <a href="#agents" className="hover:text-white transition-colors duration-300">NanoAureons</a>
                </div>
                <Link to="/login">
                    <StarBorder as="button" className="group" color="#00F2FF" speed="4s">
                        <span className="flex items-center gap-2 font-medium text-sm">
                            Iniciar Sistema
                            <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                        </span>
                    </StarBorder>
                </Link>
            </nav>

            {/* Hero */}
            <main className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-32 text-center flex flex-col items-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/5 mb-8 backdrop-blur-md shadow-inner shadow-white/5">
                    <Zap size={14} className="text-yellow-400" />
                    <span className="text-xs font-medium text-gray-300 tracking-wide uppercase">Sistema v2.0 En Línea</span>
                </div>

                <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-8 leading-[1.1]">
                    Gestiona tu Caos,<br />
                    <ShinyText text="Desbloquea tu Potencial" disabled={false} speed={3} className="text-cyan-400" />
                </h1>

                <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
                    El Sistema Operativo Inteligente para el Polímata Digital.
                    Orquesta agentes, centraliza memoria y ejecuta determinísticamente con <span className="text-emerald-400 font-mono text-sm">precisión</span>.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                    <Link to="/login">
                        <button className="px-8 py-4 bg-white text-black font-bold rounded-xl hover:scale-105 hover:shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)] transition-all duration-300 flex items-center justify-center gap-2">
                            Entrar al Nexus
                            <ArrowRight size={18} />
                        </button>
                    </Link>
                    <button className="px-8 py-4 bg-transparent border border-white/10 text-white font-medium rounded-xl hover:bg-white/5 transition-colors backdrop-blur-sm flex items-center gap-2">
                        Arquitectura del Sistema
                    </button>
                </div>

                {/* ReactBits Spotlight Grid */}
                <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl">
                    <SpotlightCard className="p-8 h-full flex flex-col items-start gap-4" spotlightColor="rgba(0, 242, 255, 0.15)">
                        <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center mb-2">
                            <Brain className="text-cyan-400" size={24} />
                        </div>
                        <h3 className="text-2xl font-bold text-white">Hybrid Cortex</h3>
                        <p className="text-gray-400 leading-relaxed">
                            Motor de procesamiento dual que combina privacidad local con escalabilidad en la nube. Pipelines de ejecución determinista para tareas complejas.
                        </p>
                    </SpotlightCard>

                    <SpotlightCard className="p-8 h-full flex flex-col items-start gap-4" spotlightColor="rgba(168, 85, 247, 0.15)">
                        <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center mb-2">
                            <Database className="text-purple-400" size={24} />
                        </div>
                        <h3 className="text-2xl font-bold text-white">Memoria RAG Infinita</h3>
                        <p className="text-gray-400 leading-relaxed">
                            Auréon lo recuerda todo. Recuperación de contexto profundo de tus documentos, código y conversaciones.
                        </p>
                    </SpotlightCard>

                    <SpotlightCard className="p-8 h-full flex flex-col items-start gap-4" spotlightColor="rgba(46, 204, 113, 0.15)">
                        <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-2">
                            <Users className="text-emerald-400" size={24} />
                        </div>
                        <h3 className="text-2xl font-bold text-white">Flota NanoAureons</h3>
                        <p className="text-gray-400 leading-relaxed">
                            Orquesta sub-agentes especializados (Arquitecto, Artista, Centinela) para ejecutar tareas de dominio específico en paralelo.
                        </p>
                    </SpotlightCard>
                </div>
            </main>

            <footer className="relative z-10 py-8 text-center text-gray-500 text-sm border-t border-white/5 mt-20">
                <p>&copy; 2026 Multiversa Lab. Impulsado por Aureon Cortex v2.0</p>
            </footer>
        </div>
    );
};

export default LandingPage;
