import React from 'react';
import { NavLink } from 'react-router-dom';
import { Inbox, FileText, Send, PieChart, LogOut, Layers, Archive, Trash2, ClipboardList } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import styles from './Sidebar.module.css';

const Sidebar = () => {
    const { logout, userEmail } = useAuth();

    const navItems = [
        { to: '/', icon: Inbox, label: 'Inbox', end: true },
        { to: '/threads', icon: Layers, label: 'Threads' },
        { to: '/tasks', icon: ClipboardList, label: 'Tasks' }, // Reusing FileText (or different icon)
        { to: '/drafts', icon: FileText, label: 'Drafts' },
        { to: '/sent', icon: Send, label: 'Sent' },
        { to: '/archive', icon: Archive, label: 'Archive' },
        { to: '/trash', icon: Trash2, label: 'Trash' },
        { to: '/analytics', icon: PieChart, label: 'Analytics' },
    ];

    return (
        <aside className={styles.sidebar}>
            <div className={styles.header}>
                <div className={styles.logo}>mAiL</div>
            </div>

            <nav className={styles.nav}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        end={item.end}
                        className={({ isActive }) =>
                            `${styles.link} ${isActive ? styles.active : ''}`
                        }
                    >
                        <item.icon size={20} />
                        <span className={styles.label}>{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className={styles.footer}>
                <div className={styles.profile}>
                    <div className={styles.avatar}>
                        {(userEmail || 'U').charAt(0).toUpperCase()}
                    </div>
                    <div className={styles.userInfo}>
                        <span className={styles.userName}>Logged In</span>
                        <span className={styles.userEmail}>{userEmail || 'Guest'}</span>
                    </div>
                </div>
                <button onClick={logout} className={styles.logoutBtn} title="Logout">
                    <LogOut size={18} />
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
