// WebSocket connection
const notificationSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/notifications/'
);

// Notification counter element
const notificationCounter = document.getElementById('notification-counter');
let unreadCount = 0;

// Handle WebSocket connection
notificationSocket.onopen = function(e) {
    console.log('WebSocket connection established');
};

// Handle incoming messages
notificationSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('Received notification:', data);
    
    // Update notification counter
    unreadCount++;
    updateNotificationCounter();
    
    // Show notification toast
    showNotificationToast(data);
};

// Handle WebSocket errors
notificationSocket.onclose = function(e) {
    console.error('WebSocket connection closed unexpectedly');
};

// Update notification counter
function updateNotificationCounter() {
    if (notificationCounter) {
        notificationCounter.textContent = unreadCount;
        notificationCounter.classList.remove('hidden');
    }
}

// Show notification toast
function showNotificationToast(data) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-sm transform transition-transform duration-300 translate-y-0';
    toast.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div class="ml-3 w-0 flex-1">
                <p class="text-sm font-medium text-gray-900">${data.title}</p>
                <p class="mt-1 text-sm text-gray-500">${data.message}</p>
            </div>
            <div class="ml-4 flex-shrink-0 flex">
                <button class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    <span class="sr-only">Close</span>
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    // Add click handler to close button
    const closeButton = toast.querySelector('button');
    closeButton.addEventListener('click', () => {
        toast.remove();
    });
    
    // Add to document
    document.body.appendChild(toast);
    
    // Remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Mark messages as read
function markMessagesAsRead() {
    if (notificationSocket.readyState === WebSocket.OPEN) {
        notificationSocket.send(JSON.stringify({
            'type': 'mark_read'
        }));
        unreadCount = 0;
        updateNotificationCounter();
    }
}

// Add event listener to mark messages as read when viewing messages
document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
        markMessagesAsRead();
    }
}); 