import React from 'react';
import { BrowserRouter as Router, Routes, Route, useOutletContext } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import EmailList from './components/EmailList';
import Threads from './components/Threads';
import Search from './components/Search';
import Analytics from './components/Analytics';
import Drafts from './components/Drafts';

// Placeholder components
const Inbox = () => {
    const { onSelectEmail, onCompose } = useOutletContext() || {};
    return <EmailList type="inbox" onSelectEmail={(id) => onSelectEmail && onSelectEmail(id)} onCompose={onCompose} />;
};

const Sent = () => {
    const { onSelectEmail, onCompose } = useOutletContext() || {};
    return <EmailList type="sent" onSelectEmail={(id) => onSelectEmail && onSelectEmail(id)} onCompose={onCompose} />;
};

const Archive = () => {
    const { onSelectEmail, onCompose } = useOutletContext() || {};
    return <EmailList type="archive" onSelectEmail={(id) => onSelectEmail && onSelectEmail(id)} onCompose={onCompose} />;
};

const Trash = () => {
    const { onSelectEmail, onCompose } = useOutletContext() || {};
    return <EmailList type="trash" onSelectEmail={(id) => onSelectEmail && onSelectEmail(id)} onCompose={onCompose} />;
};

import { ToastProvider } from './components/Toast';

function App() {
    // ...

    return (
        <AuthProvider>
            <ToastProvider>
                <Router>
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/" element={<Layout />}>
                            <Route index element={<Inbox />} />
                            <Route path="threads" element={<Threads />} />

                            <Route path="search" element={<Search />} />
                            <Route path="analytics" element={<Analytics />} />
                            <Route path="dashboard" element={<Analytics />} />
                            <Route path="drafts" element={<Drafts />} />
                            <Route path="sent" element={<Sent />} />
                            <Route path="archive" element={<Archive />} />
                            <Route path="trash" element={<Trash />} />
                            <Route path="*" element={<div style={{ padding: '2rem' }}>Page not found</div>} />
                        </Route>
                    </Routes>
                </Router>
            </ToastProvider>
        </AuthProvider>
    );
}

export default App;
