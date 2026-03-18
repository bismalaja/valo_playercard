// Notification System
// Handles floating toast notifications for Django messages and client-side events

(function() {
    // Preserve any toasts queued before this script finished loading.
    window.__toastQueue = window.__toastQueue || [];
    let container = null;

    // 1. Inject CSS Styles
    const style = document.createElement('style');
    style.textContent = `
        #toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        }

        .toast-notification {
            pointer-events: auto;
            background: rgba(15, 25, 35, 0.95);
            border: 1px solid rgba(0, 245, 255, 0.3);
            color: #f5f9ff;
            padding: 15px 25px;
            border-radius: 4px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: space-between;
            animation: slideIn 0.3s ease-out forwards;
            min-width: 300px;
            backdrop-filter: blur(5px);
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        
        .toast-notification.success { border-color: #00f555; border-left: 4px solid #00f555; }
        .toast-notification.error { border-color: #ff4655; border-left: 4px solid #ff4655; }
        .toast-notification.warning { border-color: #ffaa00; border-left: 4px solid #ffaa00; }
        .toast-notification.info { border-color: #00f5ff; border-left: 4px solid #00f5ff; }

        .toast-close {
            background: none;
            border: none;
            color: inherit;
            margin-left: 15px;
            cursor: pointer;
            opacity: 0.7;
            font-size: 18px;
            line-height: 1;
        }
        
        .toast-close:hover { opacity: 1; }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes fadeOut {
            to { opacity: 0; transform: translateY(-20px); }
        }
    `;
    document.head.appendChild(style);

    // 2. Create Container lazily (script can load before <body> exists)
    function ensureContainer() {
        if (container && container.parentNode) return container;

        container = document.getElementById('toast-container');
        if (container) return container;

        if (!document.body) return null;

        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
        return container;
    }

    // 3. Define Global Function
    window.showToast = function(message, type = 'info') {
        const target = ensureContainer();
        if (!target) {
            window.__toastQueue.push({ message, type });
            return;
        }

        // Map Django types to our CSS classes
        const typeMap = {
            'success': 'success',
            'error': 'error',
            'warning': 'warning',
            'info': 'info',
            'debug': 'info'
        };
        const className = typeMap[type] || type;

        const toast = document.createElement('div');
        toast.className = `toast-notification ${className}`;
        
        const textSpan = document.createElement('span');
        textSpan.textContent = message;
        toast.appendChild(textSpan);

        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => removeToast(toast);
        toast.appendChild(closeBtn);

        target.appendChild(toast);

        // Auto remove
        setTimeout(() => removeToast(toast), 5000);
    };

    // Allow pages to dispatch global toast events.
    window.addEventListener('app:toast', (event) => {
        const detail = event.detail || {};
        window.showToast(detail.message || '', detail.type || 'info');
    });

    // Flush any queued toasts captured before showToast was defined.
    if (window.__toastQueue.length) {
        window.__toastQueue.forEach((entry) => {
            window.showToast(entry.message, entry.type || 'info');
        });
        window.__toastQueue = [];
    }

    function removeToast(toast) {
        toast.style.animation = 'fadeOut 0.5s ease-out forwards';
        toast.addEventListener('animationend', () => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        });
    }

    // 4. Initialize from existing HTML messages (Django integration)
    document.addEventListener('DOMContentLoaded', () => {
        ensureContainer();

        const messageContainer = document.querySelector('.messages-data');
        if (messageContainer) {
            const messages = messageContainer.querySelectorAll('.message-item');
            messages.forEach(item => {
                const text = item.getAttribute('data-message');
                const tag = item.getAttribute('data-tag');
                showToast(text, tag);
            });
        }

        if (window.__toastQueue.length) {
            const pending = [...window.__toastQueue];
            window.__toastQueue = [];
            pending.forEach((entry) => {
                window.showToast(entry.message, entry.type || 'info');
            });
        }
    });

})();
