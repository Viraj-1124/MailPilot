import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import EmailDetail from './EmailDetail';
import ComposeModal from './ComposeModal';
import { useAuth } from '../auth/AuthContext';
import styles from './Layout.module.css';

const Layout = () => {
    const { userEmail, loading } = useAuth();
    const [selectedEmailId, setSelectedEmailId] = React.useState(null);
    const [isComposeOpen, setIsComposeOpen] = React.useState(false);
    const [composeData, setComposeData] = React.useState(null);
    const [refreshKey, setRefreshKey] = React.useState(0);

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
    }

    if (!userEmail) {
        return <Navigate to="/login" replace />;
    }

    const handleCompose = (data = null) => {
        setComposeData(data);
        setIsComposeOpen(true);
    };

    const triggerRefresh = () => {
        setRefreshKey(prev => prev + 1);
    };

    return (
        <div className={styles.layout}>
            <Sidebar />
            <main className={styles.main}>
                <Outlet context={{
                    onSelectEmail: setSelectedEmailId,
                    onCompose: handleCompose,
                    refreshKey: refreshKey,
                    triggerRefresh: triggerRefresh
                }} />
                {selectedEmailId && (
                    <EmailDetail
                        emailId={selectedEmailId}
                        onClose={() => setSelectedEmailId(null)}
                        onCompose={handleCompose}
                        onActionComplete={() => {
                            triggerRefresh();
                            setSelectedEmailId(null);
                        }}
                    />
                )}
            </main>

            {/* Compose Modal */}
            {isComposeOpen && (
                <div style={{ position: 'relative', zIndex: 1000 }}> {/* Ensure it stacks above everything */}
                    <ComposeModal
                        onClose={() => {
                            setIsComposeOpen(false);
                            setComposeData(null);
                        }}
                        initialData={composeData}
                    />
                </div>
            )}
        </div>
    );
};

export default Layout;
