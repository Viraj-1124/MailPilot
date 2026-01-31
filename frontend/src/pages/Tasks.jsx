import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { Check, Clock, Mail, Calendar, ClipboardList, CheckCircle2 } from 'lucide-react';
import styles from './Tasks.module.css';
import SkeletonTask from '../components/SkeletonTask';

const Tasks = () => {
    const { userEmail } = useAuth();
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadTasks = async () => {
        if (!userEmail) return;
        try {
            setLoading(true);
            const data = await api.getUserTasks(userEmail);
            setTasks(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadTasks();
    }, [userEmail]);

    const handleToggleTask = async (taskId) => {
        // Optimistic update
        setTasks(prev => prev.map(t =>
            t.id === taskId ? { ...t, completed: !t.completed } : t
        ));

        try {
            await api.toggleTaskCompletion(taskId);
        } catch (e) {
            console.error(e);
            // Revert
            setTasks(prev => prev.map(t =>
                t.id === taskId ? { ...t, completed: !t.completed } : t
            ));
        }
    };

    const activeTasks = tasks.filter(t => !t.completed);
    const completedTasks = tasks.filter(t => t.completed);

    return (
        <div className={styles.container}>
            <header className={styles.title}>
                <ClipboardList size={32} color="var(--primary)" />
                Tasks & Action Items
            </header>

            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <span>Active Tasks</span>
                    <span style={{ fontSize: '0.9rem', background: 'var(--bg-subtle)', padding: '2px 8px', borderRadius: '12px' }}>
                        {activeTasks.length}
                    </span>
                </div>

                {loading ? (
                    <div className={styles.taskList}>
                        {Array.from({ length: 3 }).map((_, i) => <SkeletonTask key={i} />)}
                    </div>
                ) : activeTasks.length === 0 ? (
                    <div className={styles.emptyState}>
                        <p>🎉 All caught up! No active tasks.</p>
                    </div>
                ) : (
                    <div className={styles.taskList}>
                        {activeTasks.map(task => (
                            <TaskItem key={task.id} task={task} onToggle={() => handleToggleTask(task.id)} />
                        ))}
                    </div>
                )}
            </section>

            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <span>Completed</span>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-tertiary)' }}>{completedTasks.length}</span>
                </div>

                {loading ? (
                    <div className={styles.taskList}>
                        {Array.from({ length: 1 }).map((_, i) => <SkeletonTask key={i} />)}
                    </div>
                ) : completedTasks.length === 0 ? (
                    <div className={styles.emptyState} style={{ background: 'transparent', border: 'none' }}>
                        <p>Completed tasks will appear here.</p>
                    </div>
                ) : (
                    <div className={styles.taskList}>
                        {completedTasks.map(task => (
                            <TaskItem key={task.id} task={task} onToggle={() => handleToggleTask(task.id)} />
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
};

const TaskItem = ({ task, onToggle }) => {
    // Basic heuristics for "due soon" - can be improved
    const isDueSoon = task.deadline && new Date(task.deadline) < new Date(Date.now() + 86400000 * 2);

    return (
        <div
            className={`${styles.taskItem} ${task.completed ? styles.completed : ''}`}
            onClick={onToggle}
        >
            <div className={`${styles.checkbox} ${task.completed ? styles.checked : ''}`}>
                {task.completed && <Check size={14} color="white" strokeWidth={3} />}
            </div>

            <div className={styles.content}>
                <div className={styles.taskText}>
                    {task.task_text}
                </div>

                <div className={styles.metaRow}>
                    {task.deadline && (
                        <div className={`${styles.metaItem} ${isDueSoon && !task.completed ? styles.dueSoon : ''}`}>
                            <Calendar size={12} />
                            {new Date(task.deadline).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </div>
                    )}
                    <div className={styles.metaItem}>
                        <Mail size={12} />
                        From Email
                    </div>
                    {!task.completed && task.source === 'ai' && (
                        <div className={styles.metaItem} style={{ color: 'var(--primary)', fontWeight: 500 }}>
                            AI Extracted
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Tasks;
