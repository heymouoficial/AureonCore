import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import CockpitLayout from './pages/CockpitLayout';
import AuthPage from './pages/AuthPage';

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    {/* Public Route: Landing Page */}
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/login" element={<AuthPage />} />

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
