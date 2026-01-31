import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { Search as SearchIcon } from 'lucide-react';
import styles from './EmailList.module.css'; // Reuse

// Helper to highlight text (duplicate or move to separate util in production)
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

const Search = () => {
    const { userEmail } = useAuth();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    const { onSelectEmail } = useOutletContext() || {};

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        try {
            setLoading(true);
            const data = await api.getSearch(userEmail, query);
            setResults(data);
            setHasSearched(true);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>Search</h1>
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px', marginTop: '1rem' }}>
                    <div style={{ position: 'relative', flex: 1 }}>
                        <SearchIcon size={18} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-tertiary)' }} />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search visible emails..."
                            style={{
                                width: '100%',
                                padding: '10px 10px 10px 40px',
                                borderRadius: 'var(--radius-md)',
                                border: '1px solid var(--border)',
                                background: 'var(--bg-panel)',
                                color: 'var(--text-main)'
                            }}
                        />
                    </div>
                    <button type="submit" className="btn-primary">Search</button>
                </form>
            </header>

            <div className={styles.list}>
                {loading && <div className={styles.loading}>Searching...</div>}

                {!loading && hasSearched && results.length === 0 && (
                    <div className={styles.empty}>No matching emails found.</div>
                )}

                {!loading && results.map((email) => (
                    <div
                        key={email.email_id}
                        className={styles.emailItem}
                        onClick={() => onSelectEmail && onSelectEmail(email.email_id)}
                    >
                        <div className={styles.emailHeader}>
                            <span className={styles.sender}>
                                <HighlightText text={email.sender} highlight={query} />
                            </span>
                            <span className={styles.time}>{new Date(email.timestamp).toLocaleDateString()}</span>
                        </div>
                        <div className={styles.subjectRow}>
                            <span className={styles.subject}>
                                <HighlightText text={email.subject} highlight={query} />
                            </span>
                        </div>
                        <p className={styles.summary}>
                            <HighlightText text={email.summary} highlight={query} />
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Search;
