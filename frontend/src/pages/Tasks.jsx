import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../auth/AuthContext';
import { Check, Clock, Mail } from 'lucide-react';
import styles from '../components/EmailDetail.module.css'; // Reusing mostly compatible styles

const Tasks = () => {
    const { userEmail } = useAuth();
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadTasks = async () => {
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
        if (userEmail) loadTasks();
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

    if (loading) return <div style={{ padding: '2rem' }}>Loading tasks...</div>;

    const activeTasks = tasks.filter(t => !t.completed);
    const completedTasks = tasks.filter(t => t.completed);

    return (
        <div style={{ padding: '2rem', height: '100%', overflowY: 'auto' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.5rem' }}>Tasks</h1>

            <section style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>Active ({activeTasks.length})</h2>
                {activeTasks.length === 0 && <div style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>No active tasks.</div>}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {activeTasks.map(task => (
                        <TaskItem key={task.id} task={task} onToggle={() => handleToggleTask(task.id)} />
                    ))}
                </div>
            </section>

            <section>
                <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>Completed ({completedTasks.length})</h2>
                {completedTasks.length === 0 && <div style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>No completed tasks.</div>}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {completedTasks.map(task => (
                        <TaskItem key={task.id} task={task} onToggle={() => handleToggleTask(task.id)} />
                    ))}
                </div>
            </section>
        </div>
    );
};

const TaskItem = ({ task, onToggle }) => (
    <div style={{
        display: 'flex',
        gap: '12px',
        padding: '12px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        opacity: task.completed ? 0.6 : 1,
        alignItems: 'flex-start'
    }}>
        <div
            onClick={onToggle}
            style={{
                width: '20px',
                height: '20px',
                borderRadius: '4px',
                border: '2px solid var(--text-tertiary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: '1px',
                borderColor: task.completed ? 'var(--primary)' : 'var(--text-tertiary)',
                background: task.completed ? 'var(--primary)' : 'transparent'
            }}
        >
            {task.completed && <Check size={14} color="white" />}
        </div>

        <div style={{ flex: 1 }}>
            <div style={{
                fontSize: '1rem',
                marginBottom: '4px',
                textDecoration: task.completed ? 'line-through' : 'none',
                color: task.completed ? 'var(--text-tertiary)' : 'var(--text-main)'
            }}>
                {task.task_text}
            </div>

            <div style={{ display: 'flex', gap: '12px', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
                {task.deadline && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} />
                        {new Date(task.deadline).toLocaleDateString()}
                    </div>
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Mail size={12} />
                    From email
                </div>
            </div>
        </div>
    </div>
);

export default Tasks;
