import React, { useState } from 'react';
import { api } from '../services/api';
import styles from './Login.module.css';

const Login = () => {
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        try {
            setLoading(true);
            const { auth_url } = await api.getLoginUrl();
            if (auth_url) {
                window.location.href = auth_url;
            }
        } catch (error) {
            console.error("Login failed", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>mAiL</h1>
                <p className={styles.tagline}>
                    AI-powered Gmail assistant that summarizes, prioritizes, and replies for you.
                </p>

                <button
                    onClick={handleLogin}
                    disabled={loading}
                    className={`${styles.googleBtn} ${loading ? styles.loading : ''}`}
                >
                    {loading ? 'Connecting...' : 'Login with Google'}
                </button>
            </div>
        </div>
    );
};

export default Login;
