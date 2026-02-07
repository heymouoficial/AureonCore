import React, { useState, useRef, useEffect } from 'react';
import { Bot, Menu, Sparkles } from 'lucide-react';
import ReasoningSteps from './ReasoningSteps';
import ResponseCard from './ResponseCard';
import { apiFetch } from '../lib/api';

export default function Chat({ onOpenMenu, onNavigate, userId = 'default' }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentSteps, setCurrentSteps] = useState([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [conversationId, setConversationId] = useState(null);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, currentSteps]);

    const sendMessageWithStreaming = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = {
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setIsStreaming(true);
        setCurrentSteps([
            { number: 1, description: 'Analizando mensaje', status: 'pending' },
            { number: 2, description: 'Procesando contexto', status: 'pending' },
            { number: 3, description: 'Generando respuesta', status: 'pending' },
        ]);

        try {
            const response = await apiFetch('/api/v1/chat/stream', {
                method: 'POST',
                body: JSON.stringify({
                    message: input,
                    channel: 'pwa',
                    sender_id: userId,
                    conversation_id: conversationId
                })
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(errText || 'Error de autenticación');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value);
                const lines = text.split('\n').filter(line => line.startsWith('data: '));

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'step') {
                            setCurrentSteps(prev => prev.map(step =>
                                step.number === data.step
                                    ? { ...step, status: data.status, result: data.result }
                                    : step
                            ));
                        } else if (data.type === 'complete') {
                            setIsStreaming(false);
                            setCurrentSteps([]);
                            if (data.conversation_id) {
                                setConversationId(data.conversation_id);
                            }

                            // Create response message with card support
                            const assistantMessage = {
                                role: 'assistant',
                                content: data.response,
                                timestamp: new Date(),
                                card: data.card,
                                processingTime: data.processing_time_ms,
                                citations: data.citations || []
                            };

                            setMessages(prev => [...prev, assistantMessage]);
                        } else if (data.type === 'error') {
                            setIsStreaming(false);
                            setCurrentSteps([]);
                            setMessages(prev => [...prev, {
                                role: 'assistant',
                                content: `⚠️ Error: ${data.message}`,
                                timestamp: new Date(),
                                error: true,
                            }]);
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        } catch (error) {
            setIsStreaming(false);
            setCurrentSteps([]);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '⚠️ Error de conexión con Aureon Cortex',
                timestamp: new Date(),
                error: true,
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessageWithStreaming();
        }
    };

    const hasMessages = messages.length > 0 || isStreaming;
    const hasInput = input.trim().length > 0;

    return (
        <div className="zap-container">
            {/* Top bar with menu */}
            <div className="zap-topbar">
                <button className="zap-menu-btn" onClick={onOpenMenu}>
                    <Menu size={20} />
                </button>
                <div className="zap-topbar-title">
                    <Sparkles size={16} className="topbar-icon" />
                    Auréon
                </div>
                {isStreaming && (
                    <div className="topbar-status">
                        <span className="status-dot"></span>
                        Procesando...
                    </div>
                )}
            </div>

            {/* Content area */}
            <div className={`zap-content ${hasMessages ? 'has-messages' : ''}`}>
                {/* Welcome screen */}
                {!hasMessages && !isStreaming && (
                    <div className="zap-welcome">
                        <div className="zap-logo">
                            <Bot size={40} />
                        </div>
                        <h1 className="zap-title">Hola, soy Auréon</h1>
                        <p className="zap-subtitle">¿En qué puedo ayudarte hoy?</p>
                    </div>
                )}

                {/* Messages */}
                <div className="zap-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`zap-message ${msg.role}`}>
                            {msg.role === 'assistant' && msg.card ? (
                                <ResponseCard card={{
                                    ...msg.card,
                                    content: msg.content,
                                    status: 'complete'
                                }} />
                            ) : (
                                <div className={`zap-message-content ${msg.error ? 'error' : ''}`}>
                                    {msg.content}
                                </div>
                            )}
                            {msg.processingTime && (
                                <div className="message-meta">
                                    ⚡ {msg.processingTime}ms
                                </div>
                            )}
                            {msg.citations && msg.citations.length > 0 && (
                                <div className="citation-inline">
                                    {msg.citations.map((c, cidx) => (
                                        c.url ? (
                                            <a key={cidx} href={c.url} target="_blank" rel="noreferrer">
                                                {c.title || c.url}
                                            </a>
                                        ) : (
                                            <span key={cidx}>{c.title || 'Fuente'}</span>
                                        )
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}

                    {/* Live reasoning steps */}
                    {isStreaming && currentSteps.length > 0 && (
                        <div className="zap-message assistant">
                            <ReasoningSteps
                                steps={currentSteps}
                                title="Procesando tu consulta"
                                compact={false}
                            />
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Floating input - Capsule Style */}
            <div className="zap-input-wrapper">
                <div className="zap-input-container">
                    <input
                        ref={inputRef}
                        type="text"
                        className="zap-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask me anything..."
                        disabled={isLoading}
                    />
                    <button
                        className={`zap-send-btn ${hasInput ? 'active' : ''}`}
                        onClick={sendMessageWithStreaming}
                        disabled={!hasInput || isLoading}
                        title="Send"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 2L11 13" />
                            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                        </svg>
                        <span className="sparkle">✦</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
