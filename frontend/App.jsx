import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import FounderGate from './pages/FounderGate';
import CockpitLayout from './pages/CockpitLayout';

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    {/* Founder Gate: bienvenida + login (único acceso) */}
                    <Route path="/" element={<FounderGate />} />
                    <Route path="/login" element={<Navigate to="/" replace />} />

                    {/* App Route: The OS Cockpit */}
                    <Route
                        path="/app/*"
                        element={(
                            <ProtectedRoute>
                                <CockpitLayout />
                            </ProtectedRoute>
                        )}
                    />

                    {/* Catch all */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;
