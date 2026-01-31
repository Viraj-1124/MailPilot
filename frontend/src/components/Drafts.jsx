import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { FileText, Edit3 } from 'lucide-react';
import styles from './EmailList.module.css'; // Reuse styles for consistency

const Drafts = () => {
    const { userEmail } = useAuth();
    const [drafts, setDrafts] = useState([]);
    const [loading, setLoading] = useState(true);

    const { onSelectEmail } = useOutletContext() || {};

    useEffect(() => {
        if (userEmail) loadDrafts();
    }, [userEmail]);

    const loadDrafts = async () => {
        try {
            setLoading(true);
            const data = await api.getAllDrafts(userEmail);
            setDrafts(data || []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>Drafts</h1>
                <p className={styles.subtitle} style={{ marginTop: '0.5rem' }}>
                    Manage your saved drafts
                </p>
            </header>

            <div className={styles.list}>
                {loading && <div className={styles.loading}>Loading drafts...</div>}

                {!loading && drafts.length === 0 && (
                    <div className={styles.empty}>No drafts found.</div>
                )}

                {!loading && drafts.map((draft) => (
                    <div
                        key={draft.email_id}
                        className={styles.emailItem}
                        onClick={() => onSelectEmail && onSelectEmail(draft.email_id)}
                    >
                        <div className={styles.emailHeader}>
                            <span className={styles.sender}>Draft</span>
                            <span className={styles.time}>{new Date(draft.updated_at).toLocaleDateString()}</span>
                        </div>
                        <div className={styles.subjectRow}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Edit3 size={16} color="var(--primary)" />
                                <span className={styles.subject}>{draft.subject}</span>
                            </div>
                        </div>
                        <p className={styles.summary}>{draft.draft_text}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Drafts;
