import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { BarChart, TrendingUp, Mail, Paperclip, MessageSquare } from 'lucide-react';
import styles from './Analytics.module.css';

const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className={styles.card}>
        <div className={styles.cardHeader}>
            <span className={styles.cardTitle}>{title}</span>
            <Icon size={20} color={color} />
        </div>
        <div className={styles.cardValue}>{value}</div>
    </div>
);

const Analytics = () => {
    const { userEmail } = useAuth();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (userEmail) loadStats();
    }, [userEmail]);

    const loadStats = async () => {
        try {
            const stats = await api.getUserAnalytics(userEmail);
            setData(stats);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className={styles.loading}>Loading analytics...</div>;
    if (!data) return <div className={styles.error}>No data available</div>;

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>Analytics Dashboard</h1>
            </header>

            <div className={styles.grid}>
                <StatCard title="Total Emails" value={data.total_emails} icon={Mail} color="var(--primary)" />
                <StatCard title="Attachments" value={data.total_attachments} icon={Paperclip} color="var(--warning)" />
                <StatCard title="Threads" value={data.thread_count} icon={MessageSquare} color="var(--info)" />
                <StatCard title="Avg Summary" value={`${data.average_summary_length} chars`} icon={TrendingUp} color="var(--success)" />
            </div>

            <div className={styles.chartsRow}>
                <div className={styles.chartCard}>
                    <h3>Priority Distribution</h3>
                    <div className={styles.barChart}>
                        {Object.entries(data.priority_distribution || {}).map(([key, val]) => (
                            <div key={key} className={styles.barRow}>
                                <span className={styles.barLabel}>{key}</span>
                                <div className={styles.barTrack}>
                                    <div
                                        className={styles.barFill}
                                        style={{
                                            width: `${(val / data.total_emails) * 100}%`,
                                            background: key === 'High' ? 'var(--danger)' : key === 'Medium' ? 'var(--warning)' : 'var(--success)'
                                        }}
                                    />
                                </div>
                                <span className={styles.barValue}>{val}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className={styles.chartCard}>
                    <h3>Category Distribution</h3>
                    <div className={styles.barChart}>
                        {Object.entries(data.category_distribution || {}).map(([key, val]) => (
                            <div key={key} className={styles.barRow}>
                                <span className={styles.barLabel}>{key}</span>
                                <div className={styles.barTrack}>
                                    <div
                                        className={styles.barFill}
                                        style={{
                                            width: `${(val / data.total_emails) * 100}%`,
                                            background: 'var(--primary)'
                                        }}
                                    />
                                </div>
                                <span className={styles.barValue}>{val}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
