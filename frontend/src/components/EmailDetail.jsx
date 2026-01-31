import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { X, CornerUpLeft, Send, Sparkles, Save, Clock } from 'lucide-react';
import styles from './EmailDetail.module.css';

const EmailDetail = ({ emailId, onClose, onCompose, onActionComplete }) => {
    const { userEmail } = useAuth();
    const [email, setEmail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [replyText, setReplyText] = useState('');
    const [tone, setTone] = useState('formal');
    const [generating, setGenerating] = useState(false);
    const [sending, setSending] = useState(false);
    const [toast, setToast] = useState(null);

    useEffect(() => {
        if (emailId) {
            setReplyText(''); // Clear previous AI text or drafts
            loadEmail();
        }
    }, [emailId]);

    const loadEmail = async () => {
        try {
            setLoading(true);
            const data = await api.getEmail(emailId);
            setEmail(data);

            if (userEmail) {
                try {
                    const draftRes = await api.getDraft(emailId, userEmail);
                    if (draftRes && draftRes.draft_text) {
                        setReplyText(draftRes.draft_text);
                        if (draftRes.tone) setTone(draftRes.tone);
                    }
                } catch (err) {
                    // Start fresh if no draft
                }
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateReply = async () => {
        try {
            setGenerating(true);
            const res = await api.generateReply(emailId, tone);

            // Check if structured reply exists (using new backend logic)
            if (res.reply_subject && res.reply_body) {
                // Open global compose modal with pre-filled data
                if (onCompose) {
                    onCompose({
                        to: email.from_ || email.from, // Ensure we get the sender email
                        subject: res.reply_subject,
                        body: res.reply_body
                    });
                    // Optional: Close this detail view if desired, or keep open
                    // onClose(); 
                } else {
                    // Fallback to inline if onCompose not available (shouldn't happen with updated Layout)
                    setReplyText(res.reply_body);
                }
            } else {
                // Fallback for legacy or error string
                setReplyText(res.generated_reply || res.reply || '');
            }
        } catch (e) {
            console.error(e);
        } finally {
            setGenerating(false);
        }
    };

    const handleSend = async () => {
        setSending(true);
        // Simulate "Undo" capability by showing toast first? 
        // Requirement: "Show toast: 'Email will be sent in 10 seconds – Undo?'"

        setToast({ state: 'counting', seconds: 10 });
        // We will handle the timer logic in a useEffect or simple interval here
    };

    // Timer logic for undo
    useEffect(() => {
        let timer;
        if (toast?.state === 'counting') {
            if (toast.seconds === 0) {
                // Send now
                actuallySend();
            } else {
                timer = setTimeout(() => {
                    setToast(prev => ({ ...prev, seconds: prev.seconds - 1 }));
                }, 1000);
            }
        }
        return () => clearTimeout(timer);
    }, [toast]);

    const actuallySend = async () => {
        try {
            setToast({ state: 'sending' });
            await api.sendReply(emailId, replyText);
            setToast({ state: 'sent' });
            setTimeout(() => {
                onClose();
                setToast(null);
                setReplyText(''); // Ensure text is cleared on close
            }, 1500);
        } catch (e) {
            console.error(e);
            setToast({ state: 'error' });
        }
    };

    const handleUndo = () => {
        setToast(null);
        setSending(false);
        // Call backend undo-send if specified? 
        // Requirement says: "If user clicks Undo: Call POST /undo-send" - implies backend buffers it?
        // But usually frontend buffers. "Email will be sent in 10s".
        // If backend endpoint exists for undo, it means we MIGHT send it immediately but with a delay flag?
        // Checking req: "If not undone: Email is sent via backend".
        // "If user clicks Undo: Call POST /undo-send".
        // This implies we send a request FIRST, then undo?
        // OR we wait. "Email will be sent in 10 seconds". Usually means FE wait.
        // But if there is a specific /undo-send endpoint, maybe backend holds it?
        // Let's assume simpler FE wait for now unless I see /undo-send in backend.
        // Checked server.py -> I do NOT see /undo-send endpoint.
        // So I will implement purely on frontend.
    };

    if (!emailId) return null;

    return (
        <div className={styles.panel}>
            <header className={styles.header}>
                <div className={styles.headerControls}>
                    <button onClick={onClose} className={styles.closeBtn}><X size={20} /></button>
                    {email && (
                        <div className={styles.meta}>
                            {/* Archive / Unarchive */}
                            {email.is_archived ? (
                                <button title="Unarchive" onClick={async () => {
                                    await api.unarchiveEmail(emailId);
                                    if (onActionComplete) onActionComplete();
                                    else onClose();
                                }} style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '8px' }}>
                                    📤
                                </button>
                            ) : (
                                <button title="Archive" onClick={async () => {
                                    await api.archiveEmail(emailId);
                                    if (onActionComplete) onActionComplete();
                                    else onClose();
                                }} style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '8px' }}>
                                    📥
                                </button>
                            )}

                            {/* Delete / Restore */}
                            {email.is_deleted ? (
                                <button title="Restore" onClick={async () => {
                                    await api.restoreEmail(emailId);
                                    if (onActionComplete) onActionComplete();
                                    else onClose();
                                }} style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '16px', color: 'green' }}>
                                    ♻️
                                </button>
                            ) : (
                                <button title="Delete" onClick={async () => {
                                    if (confirm('Delete this email?')) {
                                        await api.deleteEmail(emailId);
                                        if (onActionComplete) onActionComplete();
                                        else onClose();
                                    }
                                }} style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '16px', color: 'red' }}>
                                    🗑️
                                </button>
                            )}

                            <span className={styles.date}>{new Date(email.timestamp || Date.now()).toLocaleDateString()}</span>
                        </div>
                    )}
                </div>
            </header>

            {loading ? (
                <div className={styles.loading}>Loading email...</div>
            ) : !email ? (
                <div className={styles.loading} style={{ color: 'var(--text-secondary)' }}>Email not found or deleted</div>
            ) : (
                <>
                    <div className={styles.content}>
                        <h2 className={styles.subject}>{email.subject || '(No Subject)'}</h2>
                        <div className={styles.sender}>
                            <div className={styles.avatar}>{(email.from_ || email.from || '?').charAt(0)}</div>
                            <div className={styles.senderInfo}>
                                <span className={styles.name}>{email.from_ || email.from || 'Unknown Sender'}</span>
                                <span className={styles.to}>to me</span>
                            </div>
                        </div>

                        <div className={styles.body} dangerouslySetInnerHTML={{ __html: email.body.replace(/\n/g, '<br/>') }} />

                        {email.attachments && email.attachments.length > 0 && (
                            <div className={styles.attachments}>
                                {email.attachments.map((att, i) => (
                                    <div key={i} className={styles.attachment}>
                                        <span>📎 {att.filename}</span>
                                        <span className={styles.size}>{Math.round(att.size / 1024)}KB</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className={styles.replySection}>
                        <div className={styles.aiControls}>
                            <select
                                value={tone}
                                onChange={(e) => setTone(e.target.value)}
                                className={styles.toneSelect}
                            >
                                <option value="formal">Formal</option>
                                <option value="casual">Casual</option>
                                <option value="concise">Concise</option>
                            </select>
                            <button
                                onClick={handleGenerateReply}
                                className={styles.aiBtn}
                                disabled={generating}
                            >
                                <Sparkles size={16} />
                                {generating ? 'Generating...' : 'AI Reply'}
                            </button>
                        </div>

                        <textarea
                            className={styles.replyInput}
                            value={replyText}
                            onChange={(e) => setReplyText(e.target.value)}
                            placeholder="Write a reply..."
                        />

                        <div className={styles.actions}>
                            <button
                                className={styles.draftBtn}
                                onClick={async () => {
                                    if (!userEmail) return;
                                    try {
                                        await api.saveDraft(emailId, userEmail, replyText, tone);
                                        setToast({ state: 'saved', seconds: 0 }); // Reuse toast for "Saved"
                                        setTimeout(() => setToast(null), 2000);
                                    } catch (e) { console.error(e); }
                                }}
                            >
                                <Save size={18} />
                                Save Draft
                            </button>
                            <button
                                className={styles.sendBtn}
                                onClick={handleSend}
                                disabled={!replyText || sending}
                            >
                                <Send size={18} />
                                {toast?.state === 'counting' ? `Sending in ${toast.seconds}s...` : 'Send'}
                            </button>
                        </div>
                    </div>

                    {toast?.state === 'counting' && (
                        <div className={styles.toast}>
                            <span>Sending in {toast.seconds}s...</span>
                            <button onClick={handleUndo} className={styles.undoLink}>Undo</button>
                        </div>
                    )}
                    {toast?.state === 'saved' && (
                        <div className={styles.toast} style={{ background: 'var(--success)' }}>
                            <span>Draft Saved!</span>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default EmailDetail;
