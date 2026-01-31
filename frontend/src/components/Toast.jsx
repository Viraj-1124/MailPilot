import React, { createContext, useContext, useState, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

const ToastContext = createContext(null);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
};

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((message, type = 'info', duration = 3000) => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);

        if (duration) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ addToast }}>
            {children}
            <div style={{
                position: 'fixed',
                bottom: '24px',
                right: '24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                zIndex: 9999
            }}>
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        style={{
                            background: 'var(--bg-panel)',
                            color: 'var(--text-main)',
                            padding: '12px 16px',
                            borderRadius: 'var(--radius-md)',
                            boxShadow: 'var(--shadow-lg)',
                            border: '1px solid var(--border)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            minWidth: '300px',
                            animation: 'slideIn 0.2s ease-out'
                        }}
                    >
                        {toast.type === 'success' && <CheckCircle size={20} color="var(--success)" />}
                        {toast.type === 'error' && <AlertCircle size={20} color="var(--danger)" />}
                        {toast.type === 'info' && <Info size={20} color="var(--info)" />}

                        <span style={{ flex: 1, fontSize: '0.875rem' }}>{toast.message}</span>

                        <button onClick={() => removeToast(toast.id)} style={{ color: 'var(--text-tertiary)' }}>
                            <X size={16} />
                        </button>
                    </div>
                ))}
            </div>
            <style>{`
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `}</style>
        </ToastContext.Provider>
    );
};
