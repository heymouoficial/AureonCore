import React from 'react';
import { Sun, Moon, Palette } from 'lucide-react';
import { useTheme } from './ThemeProvider';

const ACCENT_COLORS = {
    cyan: { color: '#06b6d4', label: 'Cyan' },
    blue: { color: '#3b82f6', label: 'Blue' },
    gray: { color: '#64748b', label: 'Gray' },
    green: { color: '#10b981', label: 'Green' },
};

export function ThemeSwitcher({ variant = 'full' }) {
    const { theme, toggleTheme, accent, setAccent, accents } = useTheme();

    if (variant === 'minimal') {
        return (
            <div className="theme-switcher-minimal">
                <button
                    className="theme-toggle-btn"
                    onClick={toggleTheme}
                    title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
                >
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>
            </div>
        );
    }

    return (
        <div className="theme-switcher">
            <div className="theme-switcher-section">
                <button
                    className="theme-toggle-btn"
                    onClick={toggleTheme}
                    title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
                >
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
                </button>
            </div>

            <div className="theme-switcher-divider" />

            <div className="accent-selector">
                {accents.map((acc) => (
                    <button
                        key={acc}
                        className={`accent-btn ${accent === acc ? 'active' : ''}`}
                        onClick={() => setAccent(acc)}
                        title={ACCENT_COLORS[acc].label}
                        style={{ '--btn-accent': ACCENT_COLORS[acc].color }}
                    >
                        <span
                            className="accent-dot"
                            style={{ background: ACCENT_COLORS[acc].color }}
                        />
                    </button>
                ))}
            </div>
        </div>
    );
}

export default ThemeSwitcher;
