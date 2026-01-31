import React, { useState } from 'react';
import { X, Send } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import styles from './EmailDetail.module.css'; // Reuse existing styles
import { useToast } from './Toast';

const ComposeModal = ({ onClose, initialData }) => {
    const { userEmail } = useAuth();
    const { addToast } = useToast();

    const [to, setTo] = useState(initialData?.to || '');
    const [subject, setSubject] = useState(initialData?.subject || '');
    const [body, setBody] = useState(initialData?.body || '');
    const [sending, setSending] = useState(false);

    const handleSend = async () => {
        if (!to || !subject || !body) {
            addToast("Please fill all fields", "error");
            return;
        }

        try {
            setSending(true);
            await api.sendNewEmail(to, subject, body);
            addToast("Email sent successfully", "success");
            onClose();
        } catch (error) {
            console.error(error);
            addToast("Failed to send email", "error");
        } finally {
            setSending(false);
        }
    };

    return (
        <div style={{
            position: 'fixed',
            bottom: 0,
            right: '80px',
            width: '500px',
            background: 'var(--bg-panel)',
            border: '1px solid var(--border)',
            borderTopLeftRadius: 'var(--radius-lg)',
            borderTopRightRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            maxHeight: '80vh'
        }}>
            <header className={styles.header} style={{ padding: '0.8rem 1rem', background: 'var(--bg-subtle)', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>New Message</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                        <X size={18} />
                    </button>
                </div>
            </header>

            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.8rem', flex: 1, overflowY: 'auto' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>From</label>
                    <input
                        type="text"
                        value={userEmail || ''}
                        readOnly
                        style={{
                            padding: '0.5rem',
                            borderRadius: '4px',
                            border: '1px solid var(--border)',
                            background: 'var(--bg-main)',
                            color: 'var(--text-secondary)'
                        }}
                    />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>To</label>
                    <input
                        type="email"
                        value={to}
                        onChange={(e) => setTo(e.target.value)}
                        placeholder="Recipient"
                        autoFocus
                        style={{
                            padding: '0.5rem',
                            borderRadius: '4px',
                            border: '1px solid var(--border)',
                            background: 'var(--bg-main)',
                            color: 'var(--text-main)'
                        }}
                    />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Subject</label>
                    <input
                        type="text"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        placeholder="Subject"
                        style={{
                            padding: '0.5rem',
                            borderRadius: '4px',
                            border: '1px solid var(--border)',
                            background: 'var(--bg-main)',
                            color: 'var(--text-main)'
                        }}
                    />
                </div>

                <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder="Type your message here..."
                    style={{
                        flex: 1,
                        minHeight: '200px',
                        padding: '0.8rem',
                        borderRadius: '4px',
                        border: '1px solid var(--border)',
                        background: 'var(--bg-main)',
                        color: 'var(--text-main)',
                        resize: 'none',
                        fontFamily: 'inherit'
                    }}
                />
            </div>

            <div style={{ padding: '1rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button
                    onClick={handleSend}
                    disabled={sending}
                    className={styles.sendBtn}
                    style={{ width: 'auto', padding: '0.5rem 1.5rem' }}
                >
                    <Send size={16} />
                    {sending ? 'Sending...' : 'Send'}
                </button>
            </div>
        </div>
    );
};

export default ComposeModal;
