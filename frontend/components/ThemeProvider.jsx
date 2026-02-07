import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

const THEMES = ['dark', 'light'];
const ACCENTS = ['cyan', 'blue', 'gray', 'green'];

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('aureon-theme') || 'dark';
        }
        return 'dark';
    });

    const [accent, setAccent] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('aureon-accent') || 'cyan';
        }
        return 'cyan';
    });

    // Apply theme to document
    useEffect(() => {
        const root = document.documentElement;
        root.setAttribute('data-theme', theme);
        localStorage.setItem('aureon-theme', theme);
    }, [theme]);

    // Apply accent to document
    useEffect(() => {
        const root = document.documentElement;
        root.setAttribute('data-accent', accent);
        localStorage.setItem('aureon-accent', accent);
    }, [accent]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    const cycleAccent = () => {
        setAccent(prev => {
            const currentIndex = ACCENTS.indexOf(prev);
            const nextIndex = (currentIndex + 1) % ACCENTS.length;
            return ACCENTS[nextIndex];
        });
    };

    const value = {
        theme,
        setTheme,
        toggleTheme,
        accent,
        setAccent,
        cycleAccent,
        themes: THEMES,
        accents: ACCENTS,
    };

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}

export default ThemeProvider;
