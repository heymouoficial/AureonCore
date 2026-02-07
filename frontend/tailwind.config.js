/** @type {import('tailwindcss').Config} */
/** Multiversa Carbon/Chartreuse Design System */
export default {
    content: [
        "./index.html",
        "./*.{js,ts,jsx,tsx}",
        "./components/**/*.{js,ts,jsx,tsx}",
        "./pages/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                carbon: '#1b1b1b',
                graphite: '#2f2f2f',
                chartreuse: '#b7ff00',
                ivory: '#fafce8',
            },
            fontFamily: {
                heading: ['Plus Jakarta Sans', 'sans-serif'],
                body: ['Sora', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            borderRadius: {
                'sm': 'calc(0.5rem - 4px)',
                'md': 'calc(0.5rem - 2px)',
                'lg': '0.5rem',
                'xl': 'calc(0.5rem + 4px)',
            },
            animation: {
                'star-movement-bottom': 'star-movement-bottom linear infinite',
                'star-movement-top': 'star-movement-top linear infinite',
            },
            keyframes: {
                'star-movement-bottom': {
                    '0%': { transform: 'translate(0%, 0%)', opacity: '1' },
                    '100%': { transform: 'translate(-100%, 0%)', opacity: '0' },
                },
                'star-movement-top': {
                    '0%': { transform: 'translate(0%, 0%)', opacity: '1' },
                    '100%': { transform: 'translate(100%, 0%)', opacity: '0' },
                },
            },
        },
    },
    plugins: [],
}
