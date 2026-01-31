import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from './AuthContext';

const Callback = () => {
    const [searchParams] = useSearchParams();
    const { login } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        // In a real flow, the backend redirects to localhost:5173/dashboard?email=...
        // But if our backend redirects to /auth/callback on frontend, we handle it here.
        // Looking at backend server.py:
        // return RedirectResponse(url=f"http://localhost:5173/dashboard?email={user_email}")
        // So actually the backend redirects DIRECTLY to a route we need to handle.
        // We don't need a specific /auth/callback route on frontend unless we change backend.

        // However, the backend /login-url redirect_uri is 'http://localhost:8000/auth/callback'
        // This is the BACKEND callback.
        // Then backend redirects to http://localhost:5173/dashboard?email=...

        // So on frontend we just need to ensure the router handles /dashboard?email=...
        // Or just / (root) with email param since I set home as /.

        // Let's rely on AuthContext reading the URL param on mount.
        // So this component might not be needed if backend redirects to / directly.
        // But let's keep it safe.
    }, []);

    return <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px' }}>Authenticating...</div>;
};

export default Callback;
