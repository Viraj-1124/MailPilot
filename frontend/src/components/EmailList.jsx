// ... imports
import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../services/api'; // Ensure API is imported
import { useAuth } from '../auth/AuthContext';
import { Star, Clock, AlertCircle, Plus, RotateCw, Volume2, Square, ThumbsUp, ThumbsDown, Sparkles } from 'lucide-react'; // Added Plus, RotateCw, Feedback Icons
import styles from './EmailList.module.css';
import SkeletonEmail from './SkeletonEmail';
import { useToast } from './Toast';
import { useTextToSpeech } from '../hooks/useTextToSpeech';

const PriorityBadge = ({ priority }) => {
    const p = priority?.toLowerCase() || 'medium';
    return (
        <span className={`${styles.badge} ${styles[p]}`}>
            {priority}
        </span>
    );
};

// Helper to highlight text
const HighlightText = ({ text, highlight }) => {
    if (!highlight || !text) return <span>{text}</span>;

    const parts = text.split(new RegExp(`(${highlight})`, 'gi'));
    return (
        <span>
            {parts.map((part, i) =>
                part.toLowerCase() === highlight.toLowerCase() ? (
                    <span key={i} className={styles.highlight}>{part}</span>
                ) : (
                    part
                )
            )}
        </span>
    );
};

const EmailList = ({ type = 'inbox', onSelectEmail, onCompose }) => {
    const { userEmail } = useAuth();
    const [emails, setEmails] = useState([]);
    const [isError, setIsError] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [summary, setSummary] = useState('');
    const [priorityFilter, setPriorityFilter] = useState('All');
    const [searchQuery, setSearchQuery] = useState(''); // State for local highlighting if needed, or pass from prop

    // Refreshing state
    const [refreshing, setRefreshing] = useState(false);

    const { addToast } = useToast();
    const { isSpeaking, speak, stop, isSupported } = useTextToSpeech();

    // Logic to load emails from DB
    const loadEmailsFromDB = async () => {
        try {
            setIsLoading(true);
            const data = await api.getEmailsFromDB(userEmail, priorityFilter, type);
            if (data && data.emails) {
                setEmails(data.emails);
                setSummary(data.overall_summary);
            }
        } catch (err) {
            console.error("DB Load Error:", err);
            setIsError(true);
        } finally {
            setIsLoading(false);
        }
    };

    // Better Sync/Refresh Handler
    const handleRefresh = async () => {
        try {
            setRefreshing(true);
            // addToast("Syncing...", "info"); // Optional, but rotation is enough visual feedback
            const data = await api.fetchEmails(userEmail);
            if (data && data.emails) {
                await loadEmailsFromDB();
                addToast("Inbox updated", "success");
            }
        } catch (err) {
            console.error("Refresh Error:", err);
            addToast("Sync failed", "error");
        } finally {
            setRefreshing(false);
        }
    };

    const { refreshKey } = useOutletContext() || {};

    useEffect(() => {
        if (!userEmail) return;
        if (['inbox', 'sent', 'archive', 'trash'].includes(type)) {
            loadEmailsFromDB();
        } else {
            // For threads/drafts/etc, logic would be here (if independent of this component)
        }
    }, [userEmail, type, priorityFilter, refreshKey]);

    if (isError) return <div className={styles.error}>Connection error. Please retry.</div>;

    const priorities = ['All', 'High', 'Medium', 'Low'];

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className={styles.title}>
                            {type === 'inbox' ? 'Inbox' :
                                type === 'sent' ? 'Sent' :
                                    type === 'archive' ? 'Archive' :
                                        type === 'trash' ? 'Trash' : 'Emails'}
                        </h1>
                        <div className={styles.subtitle}>
                            {summary && (
                                <div className={styles.aiSummary} style={{ display: 'flex', alignItems: 'start', gap: '8px' }}>
                                    <span style={{ flex: 1 }}>✨ AI Summary: {summary}</span>
                                    {/* Text-to-Speech Control: Plays AI summary using browser native API */}
                                    {isSupported && (
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                isSpeaking ? stop() : speak(summary);
                                            }}
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                color: 'var(--text-secondary)',
                                                cursor: 'pointer',
                                                padding: '2px',
                                                marginTop: '2px'
                                            }}
                                            title={isSpeaking ? "Stop" : "Read aloud"}
                                        >
                                            {isSpeaking ? <Square size={16} fill="currentColor" /> : <Volume2 size={18} />}
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Modern Refresh Button (Icon Only) */}
                    {type === 'inbox' && (
                        <button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className={styles.iconBtn}
                            title="Sync Emails"
                            style={{
                                padding: '0.5rem',
                                borderRadius: '50%',
                                backgroundColor: 'var(--bg-subtle)',
                                color: 'var(--text-secondary)',
                                transition: 'all 0.3s ease'
                            }}
                        >
                            <RotateCw size={20} className={refreshing ? 'animate-spin' : ''} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
                            <style>{`
                                @keyframes spin { 100% { transform: rotate(360deg); } }
                            `}</style>
                        </button>
                    )}
                </div>

                {/* Filter Chips & Search Row */}
                <div className="flex flex-col gap-md" style={{ marginTop: '1rem' }}>

                    {/* Search Bar */}
                    <div style={{ position: 'relative', width: '100%' }}>
                        {/* Using a standard text input for local search filtering/highlighting */}
                        <input
                            type="text"
                            placeholder="Search emails..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '0.6rem 1rem 0.6rem 2.5rem', // Left padding for icon
                                borderRadius: 'var(--radius-md)',
                                border: '1px solid var(--border)',
                                backgroundColor: 'var(--bg-panel)',
                                fontSize: '0.9rem',
                                color: 'var(--text-main)',
                                outline: 'none'
                            }}
                        />
                        {/* Search Icon */}
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="18" height="18" viewBox="0 0 24 24"
                            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                            style={{ position: 'absolute', left: '0.8rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }}
                        >
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </div>

                    {type === 'inbox' && (
                        <div className={styles.filterRow}>
                            {priorities.map((p) => (
                                <button
                                    key={p}
                                    className={`${styles.filterChip} ${priorityFilter === p ? styles.active : ''}`}
                                    onClick={() => setPriorityFilter(p)}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </header>

            <div className={styles.list}>
                {isLoading ? (
                    Array.from({ length: 5 }).map((_, i) => <SkeletonEmail key={i} />)
                ) : emails.length === 0 ? (
                    <div className={styles.empty}>
                        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                            <p style={{ marginBottom: '0.5rem', fontSize: '1.2rem' }}>📭</p>
                            <p>No {priorityFilter !== 'All' ? `${priorityFilter} priority` : ''} emails found.</p>
                        </div>
                    </div>
                ) : (
                    emails
                        .filter(email => {
                            if (!searchQuery) return true;
                            const q = searchQuery.toLowerCase();
                            return (
                                (email.subject && email.subject.toLowerCase().includes(q)) ||
                                (email.from && email.from.toLowerCase().includes(q)) ||
                                (email.summary && email.summary.toLowerCase().includes(q))
                            );
                        })
                        .map((email) => {
                            // Helper to extract clean name
                            const getSenderName = (from) => {
                                // Maps from either 'from' or 'from_' or 'sender' based on api response
                                const raw = from || email.from_ || email.sender;
                                if (!raw) return 'Unknown';
                                const match = raw.match(/^([^<]+)/);
                                return match ? match[1].trim() : raw;
                            };

                            const handleEmailClick = async (eId) => {
                                // Optimistic update
                                setEmails(prev => prev.map(em => em.email_id === eId ? { ...em, is_read: true } : em));
                                onSelectEmail(eId);
                                try {
                                    await api.markRead(eId);
                                } catch (err) {
                                    console.error("Failed to mark read", err);
                                }
                            };

                            const isUnread = !email.is_read;

                            return (
                                <div
                                    key={email.email_id}
                                    className={styles.emailItem}
                                    onClick={() => handleEmailClick(email.email_id)}
                                    style={{
                                        backgroundColor: isUnread ? 'var(--bg-panel)' : 'var(--bg-subtle)', // Slight contrast for read
                                        borderLeftColor: isUnread ? 'var(--primary)' : 'transparent'
                                    }}
                                >
                                    <div className={styles.emailHeader}>
                                        <span className={styles.sender} style={{ fontWeight: isUnread ? 700 : 500, fontSize: '1rem' }}>
                                            <HighlightText text={getSenderName(email.from)} highlight={searchQuery} />
                                        </span>
                                        <span className={styles.time} style={{ fontWeight: isUnread ? 700 : 400 }}>
                                            {new Date(email.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                    <div className={styles.subjectRow}>
                                        <span className={styles.subject} style={{ fontWeight: isUnread ? 700 : 400 }}>
                                            <HighlightText text={email.subject} highlight={searchQuery} />
                                        </span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <PriorityBadge priority={email.priority} />

                                            {/* AI Feedback Controls */}
                                            {email.priority && (
                                                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                                                    {!email.feedbackSubmitted ? (
                                                        <>
                                                            <button
                                                                className={styles.feedbackBtn}
                                                                title="Correct classification"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setEmails(prev => prev.map(em => em.email_id === email.email_id ? { ...em, feedbackSubmitted: 'correct' } : em));
                                                                    api.submitFeedback(email.email_id, email.priority, true);
                                                                    addToast("Feedback saved!", "success");
                                                                }}
                                                            >
                                                                <ThumbsUp size={14} />
                                                            </button>
                                                            <button
                                                                className={styles.feedbackBtn}
                                                                title="Incorrect classification"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setEmails(prev => prev.map(em => em.email_id === email.email_id ? { ...em, feedbackSubmitted: 'incorrect' } : em));
                                                                    api.submitFeedback(email.email_id, email.priority, false);
                                                                    addToast("Thanks for feedback", "info");
                                                                }}
                                                            >
                                                                <ThumbsDown size={14} />
                                                            </button>
                                                        </>
                                                    ) : (
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginLeft: '4px' }}>
                                                            {email.feedbackSubmitted === 'correct' ? <ThumbsUp size={14} color="var(--success)" /> : <ThumbsDown size={14} color="var(--danger)" />}
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <p className={styles.summary} style={{ flex: 1, marginRight: '8px' }}>
                                                <HighlightText text={email.summary} highlight={searchQuery} />
                                            </p>

                                            {/* Quick Summarize Button */}
                                            <button
                                                className={styles.feedbackBtn}
                                                title="Quick Summarize"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    if (email.quickSummary || email.isSummarizing) return;

                                                    // Set loading state
                                                    setEmails(prev => prev.map(em => em.email_id === email.email_id ? { ...em, isSummarizing: true } : em));

                                                    api.getQuickSummary(email.email_id)
                                                        .then(data => {
                                                            setEmails(prev => prev.map(em =>
                                                                em.email_id === email.email_id
                                                                    ? { ...em, quickSummary: data.summary, isSummarizing: false }
                                                                    : em
                                                            ));
                                                        })
                                                        .catch(err => {
                                                            addToast("Failed to summarize", "error");
                                                            setEmails(prev => prev.map(em => em.email_id === email.email_id ? { ...em, isSummarizing: false } : em));
                                                        });
                                                }}
                                                style={{ color: email.quickSummary ? 'var(--primary)' : 'var(--text-tertiary)' }}
                                            >
                                                <Sparkles size={16} className={email.isSummarizing ? 'animate-pulse' : ''} />
                                            </button>
                                        </div>

                                        {/* Display Quick Summary if available */}
                                        {email.quickSummary && (
                                            <div style={{
                                                marginTop: '8px',
                                                padding: '8px',
                                                backgroundColor: 'var(--bg-subtle)',
                                                borderRadius: 'var(--radius-md)',
                                                borderLeft: '2px solid var(--primary)',
                                                fontSize: '0.85rem',
                                                color: 'var(--text-main)',
                                                animation: 'fadeIn 0.3s ease'
                                            }}>
                                                <strong>AI:</strong> {email.quickSummary}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                )}
            </div>

            {/* Minimal FAB for Compose */}
            <button className={styles.composeBtn} title="Compose" onClick={() => onCompose && onCompose()}>
                <Plus size={24} />
            </button>
        </div >
    );
};

export default EmailList;
