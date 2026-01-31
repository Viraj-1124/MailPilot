import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import styles from './EmailList.module.css'; // Reuse EmailList styles for consistency
import { ChevronDown, ChevronRight, MessageSquare } from 'lucide-react';

const Threads = () => {
    const { userEmail } = useAuth();
    const [threads, setThreads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [mode, setMode] = useState('category'); // subject, smart, sender, category, priority
    const [expanded, setExpanded] = useState({});

    useEffect(() => {
        console.log(`Threads component mounted.User: ${userEmail}, Mode: ${mode} `);
        if (userEmail) loadThreads();
    }, [userEmail, mode]);

    const loadThreads = async () => {
        try {
            setLoading(true);
            console.log(`Loading threads for ${userEmail} in mode ${mode} `);

            let data;
            if (mode === 'smart') {
                data = await api.getSmartThreads(userEmail);
                // Backend returns { smart_threads: [...] }
                setThreads(data.smart_threads || []);
            } else {
                data = await api.getThreads(userEmail, mode);
                // Backend returns { threads: [...] }
                setThreads(data.threads || []);
            }
            console.log("Threads loaded:", data);
        } catch (error) {
            console.error("Failed to load threads:", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleExpand = (key) => {
        setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const { onSelectEmail } = useOutletContext() || {};

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className="flex justify-between items-center">
                    <h1 className={styles.title}>Threads</h1>
                    <div className="flex gap-sm">
                        <select
                            value={mode}
                            onChange={(e) => setMode(e.target.value)}
                            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)' }}
                        >
                            <option value="subject">By Subject</option>
                            <option value="smart">✨ Smart Threads</option>
                            <option value="sender">By Sender</option>
                            <option value="category">By Category</option>
                            <option value="priority">By Priority</option>
                        </select>
                    </div>
                </div>
            </header>

            {loading ? <div className={styles.loading}>Loading threads...</div> : (
                <div className={styles.list}>
                    {(!threads || threads.length === 0) ? <div className={styles.empty}>No threads found.</div> : (
                        threads.map((thread) => {
                            if (!thread) return null;
                            const key = thread.group_key || thread.smart_thread_id || Math.random().toString();
                            // Determine a human-readable title
                            let label = thread.group_key;
                            if (!label || label.startsWith('smart-') || label.startsWith('thread-')) {
                                // If it's a technical ID, use the subject of the newest email as the thread title
                                const newestEmail = thread.emails?.[0]; // Assuming sorted by newest first
                                label = newestEmail?.subject || 'No Subject';
                            }
                            // Fallback
                            if (!label) label = 'Unnamed Thread';

                            return (
                                <div key={key} className={styles.threadGroup}>
                                    <div
                                        className={styles.groupHeader}
                                        onClick={() => toggleExpand(key)}
                                        style={{
                                            padding: '1rem',
                                            background: 'var(--bg-subtle)',
                                            borderRadius: 'var(--radius-md)',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            fontWeight: '600'
                                        }}
                                    >
                                        {expanded[key] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                                        <span>{label}</span>
                                        <span style={{
                                            background: mode === 'priority'
                                                ? (label === 'High' ? 'var(--error)' : label === 'Medium' ? 'var(--warning)' : 'var(--success)')
                                                : 'var(--primary)',
                                            color: 'white',
                                            padding: '2px 8px',
                                            borderRadius: '12px',
                                            fontSize: '0.75rem'
                                        }}>
                                            {thread.emails?.length || 0}
                                        </span>
                                    </div>
                                    {/* Preview of latest email if not expanded */}
                                    {!expanded[key] && thread.emails?.length > 0 && (
                                        <div style={{ marginLeft: '2.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingBottom: '0.5rem' }}>
                                            {thread.emails[0].summary || thread.emails[0].subject}
                                        </div>
                                    )}

                                    {expanded[key] && (
                                        <div style={{ marginLeft: '1.5rem', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                            {thread.emails?.map(email => (
                                                <div
                                                    key={email.email_id || Math.random()}
                                                    className={styles.emailItem}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onSelectEmail && onSelectEmail(email.email_id);
                                                    }}
                                                >
                                                    <div className={styles.emailHeader}>
                                                        <span className={styles.sender}>{email.sender || email.from || 'Unknown'}</span>
                                                        <span className={styles.time}>{email.timestamp ? new Date(email.timestamp).toLocaleDateString() : ''}</span>
                                                    </div>
                                                    <div className={styles.subjectRow}>
                                                        <span className={styles.subject}>{email.subject || '(No Subject)'}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    )}
                </div>
            )}
        </div>
    );
};

export default Threads;
