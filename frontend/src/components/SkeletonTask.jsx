import React from 'react';
import styles from '../pages/Tasks.module.css'; // Use the same new module

const SkeletonTask = () => (
    <div className={styles.taskItem} style={{ cursor: 'default' }}>
        <div className="skeleton" style={{ width: '20px', height: '20px', borderRadius: '6px' }}></div>
        <div className={styles.content}>
            <div className="skeleton" style={{ width: '70%', height: '1.2rem', marginBottom: '8px' }}></div>
            <div className={styles.metaRow}>
                <div className="skeleton" style={{ width: '80px', height: '0.9rem' }}></div>
                <div className="skeleton" style={{ width: '60px', height: '0.9rem' }}></div>
            </div>
        </div>
    </div>
);

export default SkeletonTask;
