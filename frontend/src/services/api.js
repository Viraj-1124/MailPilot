const API_BASE_URL = 'http://localhost:8000';

class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    // Ensure credentials are sent with requests (for cookies)
    const fetchOptions = {
        ...options,
        headers,
        credentials: 'include',
    };

    try {
        const response = await fetch(url, fetchOptions);

        if (!response.ok) {
            throw new ApiError(`Request failed with status ${response.status}`, response.status);
        }

        // Some endpoints might return empty body or redirect
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return await response.json();
        }
        return response.text();

    } catch (error) {
        console.error(`API Error at ${endpoint}:`, error);
        throw error;
    }
}

export const api = {
    getLoginUrl: () => request('/login-url'),

    // Auth
    getMe: () => request('/me'),
    logout: () => request('/logout', { method: 'POST' }),

    fetchEmails: (userEmail) => request(`/fetch-emails?user_email=${userEmail}`),

    getEmailsFromDB: (userEmail, priority = 'All', folder = 'inbox') => request(`/emails?user_email=${userEmail}&priority=${priority}&folder=${folder}`),

    getThreads: (userEmail, mode = 'subject') => request(`/threads?user_email=${userEmail}&mode=${mode}`),

    getSmartThreads: (userEmail) => request(`/smart-threads?user_email=${userEmail}`),

    getSearch: (userEmail, query) => request(`/search?user_email=${userEmail}&q=${encodeURIComponent(query)}`),

    getEmail: (emailId) => request(`/email/${emailId}`),

    generateReply: (emailId, tone) => request(`/generate-reply?email_id=${emailId}&tone=${tone}`, {
        method: 'POST'
    }),

    // Actually, let's fix the POST requests to use query params if that's what backend expects
    // or I might need to adjust based on error.
    // For generate_reply(email_id: str, tone: str) -> POST /generate-reply?email_id=...&tone=...

    generateReplyQuery: (emailId, tone) => request(`/generate-reply?email_id=${emailId}&tone=${tone}`, { method: 'POST' }),

    saveDraft: (emailId, userEmail, draftText, tone) => request('/draft', {
        method: 'POST',
        body: JSON.stringify({
            email_id: emailId,
            user_email: userEmail,
            draft_text: draftText,
            tone: tone
        })
    }),

    getAllDrafts: (userEmail) => request(`/all-drafts?user_email=${userEmail}`),

    getDraft: (emailId, userEmail) => request(`/drafts?email_id=${emailId}&user_email=${userEmail}`),

    // Let's try sending as Query Params for all POSTs as per likely FastAPI default behavior for scalar args
    sendReply: (emailId, replyText) => request(`/send-reply?email_id=${emailId}&reply_text=${encodeURIComponent(replyText)}`, { method: 'POST' }),

    sendNewEmail: (to, subject, body) => request('/send-email', {
        method: 'POST',
        body: JSON.stringify({
            to_email: to,
            subject: subject,
            body: body
        })
    }),

    autoReply: (emailId, tone) => request(`/auto-reply?email_id=${emailId}&tone=${tone}`, { method: 'POST' }),

    getUserAnalytics: (userEmail) => request(`/analytics/user?user_email=${userEmail}`),

    archiveEmail: (emailId) => request(`/email/${emailId}/archive`, { method: 'POST' }),
    unarchiveEmail: (emailId) => request(`/email/${emailId}/unarchive`, { method: 'POST' }),
    deleteEmail: (emailId) => request(`/email/${emailId}/delete`, { method: 'POST' }),
    restoreEmail: (emailId) => request(`/email/${emailId}/restore`, { method: 'POST' }),
    markRead: (emailId) => request(`/email/${emailId}/read`, { method: 'POST' }),

    submitFeedback: (emailId, priority, isCorrect) => request('/feedback', {
        method: 'POST',
        body: JSON.stringify({
            email_id: emailId,
            priority: priority,
            is_correct: isCorrect
        })
    }),

    getQuickSummary: (emailId) => request(`/email/${emailId}/quick-summary`, { method: 'POST' }),

    extractTasks: (emailId) => request(`/emails/${emailId}/extract-tasks`, { method: 'POST' }),

    toggleTaskCompletion: (taskId) => request(`/tasks/${taskId}/complete`, { method: 'PATCH' }),

    getUserTasks: (userEmail) => request(`/tasks?user_email=${userEmail}`),

    addToCalendar: (taskId) => request(`/tasks/${taskId}/add-to-calendar`, { method: 'POST' }),
};
