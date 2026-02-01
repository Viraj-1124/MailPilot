import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { X, ArrowLeft, CornerUpLeft, Send, Sparkles, Save, Clock, ClipboardList, Calendar, Bell, Archive, Inbox, Trash2, RotateCcw, Paperclip } from 'lucide-react';

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
    const [tasks, setTasks] = useState(null);
    const [extracting, setExtracting] = useState(false);
    const [taskMessage, setTaskMessage] = useState(null);

    useEffect(() => {
        if (emailId) {
            setReplyText(''); // Clear previous AI text or drafts
            setTasks(null);
            setTaskMessage(null);
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

    const handleExtractTasks = async () => {
        if (extracting || tasks) return;

        try {
            setExtracting(true);
            setTaskMessage(null);
            const res = await api.extractTasks(emailId);

            if (res.skipped) {
                setTaskMessage("No actionable tasks detected in this email.");
                setTasks([]);
            } else if (res.tasks && res.tasks.length === 0) {
                setTaskMessage("No tasks found.");
                setTasks([]);
            } else {
                setTasks(res.tasks);
            }
        } catch (e) {
            console.error(e);
            setTaskMessage("Task extraction failed. Try again.");
        } finally {
            setExtracting(false);
        }
    };

    const handleToggleTask = async (taskId) => {
        try {
            // Optimistic update
            setTasks(prev => prev.map(t =>
                t.id === taskId ? { ...t, completed: !t.completed } : t
            ));

            await api.toggleTaskCompletion(taskId);
        } catch (e) {
            console.error(e);
            // Revert on error
            setTasks(prev => prev.map(t =>
                t.id === taskId ? { ...t, completed: !t.completed } : t
            ));
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
        
    };

    if (!emailId) return null;

    return (
        <div className={styles.panel}>
            <header className={styles.header}>
                <div className={styles.headerControls}>
                    <button onClick={onClose} className={styles.closeBtn} title="Back to Inbox">
                        <ArrowLeft size={20} />
                    </button>
                    {email && (
                        <div className={styles.meta}>
                            {/* Archive / Unarchive */}
                            {email.is_archived ? (
                                <button title="Unarchive" onClick={async () => {
                                    await api.unarchiveEmail(emailId);
                                    if (onActionComplete) onActionComplete();
                                    else onClose();
                                }} className="icon-btn" style={{ marginRight: '8px' }}>
                                    <Inbox size={18} />
                                </button>
                            ) : (
                                <button title="Archive" onClick={async () => {
                                    await api.archiveEmail(emailId);
                                    if (onActionComplete) onActionComplete();
                                    else onClose();
                                }} className="icon-btn" style={{ marginRight: '8px' }}>
                                    <Archive size={18} />
                                </button>
                            )}

                            {/* Delete / Restore */}
                            {email.is_deleted ? (
                                <button title="Restore" onClick={async () => {
                                    await api.restoreEmail(emailId);
                                    if (onActionComplete) onActionComplete();
                                    else onClose();
                                }} className="icon-btn" style={{ marginRight: '16px', color: 'var(--success)' }}>
                                    <RotateCcw size={18} />
                                </button>
                            ) : (
                                <button title="Delete" onClick={async () => {
                                    if (confirm('Delete this email?')) {
                                        await api.deleteEmail(emailId);
                                        if (onActionComplete) onActionComplete();
                                        else onClose();
                                    }
                                }} className="icon-btn" style={{ marginRight: '16px', color: 'var(--danger)' }}>
                                    <Trash2 size={18} />
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

                        <div className={styles.body} dangerouslySetInnerHTML={(() => {
                            const body = email.body || '';
                            // Heuristic: If it contains HTML tags, treat as HTML
                            // (Checking for common tags generally sufficient for this context)
                            const isHtml = /<[a-z][\s\S]*>/i.test(body);

                            if (isHtml) {
                                // For HTML, we render as is. 
                                // Ideally, we would sanitize here if a library was available.
                                return { __html: body };
                            } else {
                                // For Plain Text:
                                // 1. Escape HTML (prevent XSS from text) - minimal manual handling
                                let text = body.replace(/&/g, "&amp;")
                                    .replace(/</g, "&lt;")
                                    .replace(/>/g, "&gt;")
                                    .replace(/"/g, "&quot;")
                                    .replace(/'/g, "&#039;");

                                // 2. Linkify URLs
                                text = text.replace(
                                    /(https?:\/\/[^\s]+)/g,
                                    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
                                );

                                // 3. Preserve line breaks (optional, as CSS pre-wrap handles it, but <br> is safer for innerHTML)
                                // Only doing this if pre-wrap isn't enough or for mixed content, 
                                // but with pure text + pre-wrap, newlines render fine. 
                                // However, keeping <br> ensures consistency if CSS fails or changes.
                                // For now, let's rely on CSS white-space: pre-wrap; 
                                // BUT since we are using dangerouslySetInnerHTML, we MUST wrap newlines in <br> 
                                // because innerHTML doesn't respect \n unless it's in a <pre> tag or style pre-wrap.
                                // Wait, style is pre-wrap. So \n should work!
                                // Let's try converting to <br> to be absolutely sure standard email spacing works.
                                // Gmail often converts plain text \n to <br>.
                                text = text.replace(/\n/g, '<br/>');

                                return { __html: text };
                            }
                        })()} />

                        {email.attachments && email.attachments.length > 0 && (
                            <div className={styles.attachments}>
                                {email.attachments.map((att, i) => (
                                    <div key={i} className={styles.attachment}>
                                        <span><Paperclip size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} /> {att.filename}</span>
                                        <span className={styles.size}>{Math.round(att.size / 1024)}KB</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>


                    {/* Tasks Extraction Section */}
                    <div className={styles.tasksSection}>
                        <div className={styles.tasksHeader}>
                            <div className={styles.tasksTitle}>Tasks & Action Items</div>
                            <button
                                className={styles.extractBtn}
                                onClick={handleExtractTasks}
                                disabled={extracting || (tasks && tasks.length > 0)}
                            >
                                <ClipboardList size={16} />
                                {extracting ? 'Extracting...' : tasks ? 'Tasks Extracted' : 'Extract Tasks'}
                            </button>
                        </div>

                        {taskMessage && <div className={styles.emptyTasks}>{taskMessage}</div>}

                        {tasks && tasks.length > 0 && (
                            <div className={styles.taskList}>
                                {tasks.map((task) => (
                                    <div key={task.id} className={`${styles.taskItem} ${task.completed ? styles.completed : ''}`}>
                                        <div
                                            className={styles.taskCheckbox}
                                            onClick={() => handleToggleTask(task.id)}
                                        >
                                            {task.completed && <div className={styles.checkedIndicator} />}
                                        </div>

                                        <div className={styles.taskContent}>
                                            <div className={styles.taskText}>{task.task_text}</div>
                                            {task.deadline && (
                                                <div className={styles.taskMeta}>
                                                    <Clock size={12} />
                                                    Due: {new Date(task.deadline).toLocaleString()}
                                                </div>
                                            )}
                                            <div style={{ display: 'flex', gap: '12px' }}>
                                                <AddToCalendarBtn taskId={task.id} calendarEventId={task.calendar_event_id} />
                                                <SetReminderBtn taskId={task.id} existingReminderTime={task.reminder_time} />
                                            </div>
                                        </div>
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

const AddToCalendarBtn = ({ taskId, calendarEventId }) => {
    const [status, setStatus] = React.useState(calendarEventId ? 'added' : 'idle');

    const handleAdd = async (e) => {
        e.stopPropagation();
        if (status === 'added') return;

        try {
            setStatus('loading');
            const res = await api.addToCalendar(taskId);
            if (res.success) {
                setStatus('added');
                if (res.calendar_event_link) {
                    window.open(res.calendar_event_link, '_blank');
                }
            } else {
                setStatus('error');
                console.warn(res.message);
            }
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    if (status === 'added') {
        return (
            <div className={styles.taskMeta} style={{ color: 'var(--success)', marginTop: '4px' }} title="Added to Google Calendar">
                <Calendar size={12} />
                <span>Added to Calendar</span>
            </div>
        );
    }

    return (
        <button
            className={styles.taskMeta}
            onClick={handleAdd}
            disabled={status === 'loading'}
            style={{
                background: 'none',
                border: 'none',
                padding: 0,
                color: status === 'error' ? 'var(--danger)' : 'var(--primary)',
                cursor: 'pointer',
                marginTop: '4px'
            }}
            title="Add to Google Calendar"
        >
            <Calendar size={12} />
            <span style={{ textDecoration: 'underline' }}>
                {status === 'loading' ? 'Adding...' : status === 'error' ? 'Retry' : 'Add to Calendar'}
            </span>
        </button>
    );
};

const SetReminderBtn = ({ taskId, existingReminderTime }) => {
    const [status, setStatus] = React.useState(existingReminderTime ? 'set' : 'idle');
    const [reminderTime, setReminderTime] = React.useState(existingReminderTime);
    const inputRef = React.useRef(null);

    const handleDateChange = async (e) => {
        const dateStr = e.target.value;
        if (!dateStr) return;

        try {
            setStatus('loading');
            const res = await api.setTaskReminder(taskId, new Date(dateStr).toISOString());
            if (res.success) {
                setStatus('set');
                setReminderTime(res.reminder_time);
            } else {
                setStatus('error');
            }
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    const handleClick = (e) => {
        e.stopPropagation();
        if (inputRef.current) {
            inputRef.current.showPicker();
        }
    };

    if (status === 'set') {
        return (
            <div className={styles.taskMeta} style={{ color: 'var(--text-secondary)', marginTop: '4px' }} title={`Reminder set for ${new Date(reminderTime).toLocaleString()}`}>
                <Bell size={12} fill="var(--warning)" color="var(--warning)" />
                <span>{new Date(reminderTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        );
    }

    return (
        <>
            <button
                className={styles.taskMeta}
                onClick={handleClick}
                disabled={status === 'loading'}
                style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    color: status === 'error' ? 'var(--danger)' : 'var(--text-tertiary)',
                    cursor: 'pointer',
                    marginTop: '4px'
                }}
                title="Set Reminder"
            >
                <Bell size={12} />
                <span style={{ textDecoration: 'underline' }}>
                    {status === 'loading' ? 'Setting...' : 'Set Reminder'}
                </span>
            </button>
            <input
                type="datetime-local"
                ref={inputRef}
                style={{ visibility: 'hidden', position: 'absolute', width: 0, height: 0 }}
                onChange={handleDateChange}
            />
        </>
    );
};

export default EmailDetail;
