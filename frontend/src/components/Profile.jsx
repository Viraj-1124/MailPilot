import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import styles from './Profile.module.css';
import { Save, Plus, Trash2, CheckCircle, BarChart, Settings, Sliders } from 'lucide-react';
import Analytics from './Analytics'; // Reuse existing Analytics
import { useToast } from './Toast';

const ROLES = [
    "Student", "Job Seeker", "Professional", "Influencer", "Founder", "Recruiter", "Freelancer"
];

const INTERESTS = [
    "Jobs", "Internships", "Collaborations", "Research", "Freelance", "Finance",
    "College", "Startups", "Technology", "Design", "Marketing"
];

const Profile = () => {
    const { userEmail } = useAuth();
    const { addToast } = useToast();
    const [activeTab, setActiveTab] = useState('settings');

    // Preferences State
    const [role, setRole] = useState('');
    const [myInterests, setMyInterests] = useState([]);
    const [about, setAbout] = useState('');
    const [saving, setSaving] = useState(false);

    // Rules State
    const [rules, setRules] = useState([]);
    const [newSender, setNewSender] = useState('');
    const [newPriority, setNewPriority] = useState('High');
    const [newAutoReply, setNewAutoReply] = useState(false);

    useEffect(() => {
        if (userEmail) {
            loadPreferences();
            loadRules();
        }
    }, [userEmail]);

    const loadPreferences = async () => {
        try {
            const data = await api.getPreferences();
            if (data) {
                setRole(data.primary_role || '');
                setMyInterests(data.interests || []);
                setAbout(data.about_user || '');
            }
        } catch (e) {
            console.error("Failed to load preferences", e);
        }
    };

    const loadRules = async () => {
        try {
            const data = await api.getSenderRules();
            setRules(data || []);
        } catch (e) {
            console.error("Failed to load rules", e);
        }
    };

    const toggleInterest = (interest) => {
        if (myInterests.includes(interest)) {
            setMyInterests(myInterests.filter(i => i !== interest));
        } else {
            setMyInterests([...myInterests, interest]);
        }
    };

    const handleSavePreferences = async () => {
        setSaving(true);
        try {
            await api.savePreferences({
                primary_role: role,
                interests: myInterests,
                about_user: about
            });
            addToast('Preferences saved successfully', 'success');
        } catch (e) {
            addToast('Failed to save preferences', 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleAddRule = async (e) => {
        e.preventDefault();
        if (!newSender) return;

        try {
            const rule = await api.saveSenderRule({
                sender_email: newSender,
                force_priority: newPriority,
                auto_reply: newAutoReply
            });
            setRules(prev => {
                // Remove if exists then add new
                const filtered = prev.filter(r => r.sender_email !== newSender);
                return [...filtered, rule];
            });
            setNewSender('');
            addToast('Rule added', 'success');
        } catch (e) {
            addToast('Failed to add rule', 'error');
        }
    };

    const handleDeleteRule = async (ruleId) => {
        try {
            await api.deleteSenderRule(ruleId);
            setRules(prev => prev.filter(r => r.id !== ruleId));
            addToast('Rule deleted', 'success');
        } catch (e) {
            addToast('Failed to delete rule', 'error');
        }
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>Your Profile</h1>
                <p className={styles.subtitle}>Manage your personal AI assistant settings</p>
            </header>

            <div className={styles.tabs}>
                <button
                    className={`${styles.tab} ${activeTab === 'settings' ? styles.active : ''}`}
                    onClick={() => setActiveTab('settings')}
                >
                    <Settings size={18} style={{ display: 'inline', marginRight: 8 }} />
                    Settings
                </button>
                <button
                    className={`${styles.tab} ${activeTab === 'analytics' ? styles.active : ''}`}
                    onClick={() => setActiveTab('analytics')}
                >
                    <BarChart size={18} style={{ display: 'inline', marginRight: 8 }} />
                    Analytics
                </button>
            </div>

            {activeTab === 'analytics' ? (
                <Analytics />
            ) : (
                <>
                    {/* PERSONALIZATION SECTION */}
                    <div className={styles.section}>
                        <div className={styles.sectionTitle}>
                            <Sliders size={20} color="var(--primary)" />
                            Personalization Profile
                        </div>
                        <p className={styles.label} style={{ marginBottom: '1.5rem', fontWeight: 400 }}>
                            Tell us about yourself so we can prioritize emails that matter to you.
                        </p>

                        <div className={styles.gridRow}>
                            {/* Styling improvement: Use grid for layout if needed, or keep stacked */}
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>Primary Role</label>
                            <select
                                className={styles.select}
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                            >
                                <option value="">Select a role...</option>
                                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>Interests (Select all that apply)</label>
                            <div className={styles.pillContainer}>
                                {INTERESTS.map(interest => (
                                    <div
                                        key={interest}
                                        className={`${styles.pill} ${myInterests.includes(interest) ? styles.selected : ''}`}
                                        onClick={() => toggleInterest(interest)}
                                    >
                                        {interest}
                                        {myInterests.includes(interest) && <CheckCircle size={14} style={{ marginLeft: 6 }} />}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>About You</label>
                            <textarea
                                className={styles.textarea}
                                placeholder="I am looking for software engineering internships and hackathons..."
                                value={about}
                                onChange={(e) => setAbout(e.target.value)}
                            />
                        </div>

                        <button
                            className={styles.saveBtn}
                            onClick={handleSavePreferences}
                            disabled={saving}
                        >
                            {saving ? 'Saving...' : <><Save size={18} /> Save Preferences</>}
                        </button>
                    </div>

                    {/* SENDER RULES SECTION */}
                    <div className={styles.section}>
                        <div className={styles.sectionTitle}>
                            <Settings size={20} color="var(--warning)" />
                            Important Senders & Rules
                        </div>
                        <p className={styles.label} style={{ marginBottom: '1.5rem', fontWeight: 400 }}>
                            Force priority or automate replies for specific senders.
                        </p>

                        <div className={styles.addRuleCard}>
                            <h4 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Add New Rule</h4>
                            <form className={styles.addRuleForm} onSubmit={handleAddRule}>
                                <div style={{ flex: 2 }}>
                                    <input
                                        type="email"
                                        className={styles.input}
                                        placeholder="Sender Email (e.g., boss@company.com)"
                                        value={newSender}
                                        required
                                        onChange={(e) => setNewSender(e.target.value)}
                                    />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <select
                                        className={styles.select}
                                        value={newPriority}
                                        onChange={(e) => setNewPriority(e.target.value)}
                                    >
                                        <option value="High">High</option>
                                        <option value="Medium">Medium</option>
                                        <option value="Low">Low</option>
                                    </select>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <label className={styles.checkboxLabel}>
                                        <input
                                            type="checkbox"
                                            checked={newAutoReply}
                                            onChange={(e) => setNewAutoReply(e.target.checked)}
                                        />
                                        <span>Auto-Reply</span>
                                    </label>
                                </div>
                                <button type="submit" className={styles.addBtn}>
                                    <Plus size={18} /> Add
                                </button>
                            </form>
                        </div>

                        <div className={styles.rulesList}>
                            {rules.length === 0 && (
                                <div className={styles.emptyState}>
                                    No rules set. Add one above!
                                </div>
                            )}
                            {rules.map(rule => (
                                <div key={rule.id} className={styles.ruleItem}>
                                    <div className={styles.ruleInfo}>
                                        <span className={styles.ruleEmail}>{rule.sender_email}</span>
                                        <div className={styles.ruleMeta}>
                                            {rule.force_priority && (
                                                <span className={`${styles.badge} ${styles[rule.force_priority.toLowerCase()]}`}>
                                                    Priority: {rule.force_priority}
                                                </span>
                                            )}
                                            {rule.auto_reply && (
                                                <span className={`${styles.badge} ${styles.auto}`}>
                                                    Auto-Reply: ON
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <button
                                        className={styles.deleteBtn}
                                        onClick={() => handleDeleteRule(rule.id)}
                                        title="Delete Rule"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default Profile;
