import React from 'react';
import styles from './EmailList.module.css'; // Reuse basic list styles for spacing

const SkeletonEmail = () => {
    return (
        <div className={styles.emailItem} style={{ cursor: 'default' }}>
            <div className={styles.emailHeader}>
                <div className="skeleton" style={{ width: '30%', height: '1.2rem' }}></div>
                <div className="skeleton" style={{ width: '15%', height: '1rem' }}></div>
            </div>
            <div className={styles.subjectRow} style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>
                <div className="skeleton" style={{ width: '60%', height: '1.2rem' }}></div>
                <div className="skeleton" style={{ width: '60px', height: '20px', borderRadius: '99px' }}></div>
            </div>
            <div className="skeleton" style={{ width: '90%', height: '1rem', marginTop: '0.5rem' }}></div>
            <div className="skeleton" style={{ width: '80%', height: '1rem', marginTop: '0.25rem' }}></div>
        </div>
    );
};

export default SkeletonEmail;
