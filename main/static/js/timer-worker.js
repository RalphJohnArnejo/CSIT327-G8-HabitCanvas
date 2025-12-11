/**
 * Timer Web Worker
 * Runs timer logic in background thread so it continues even when tab is minimized
 */

let timerInterval = null;
let endTime = null;
let isRunning = false;

// Handle messages from main thread
self.onmessage = function(e) {
    const { action, data } = e.data;
    
    switch(action) {
        case 'start':
            startTimer(data.endTime);
            break;
        case 'pause':
            pauseTimer();
            break;
        case 'stop':
            stopTimer();
            break;
        case 'sync':
            // Sync state from main thread (e.g., on page load)
            if(data.isRunning && data.endTime) {
                startTimer(data.endTime);
            }
            break;
        case 'getState':
            sendState();
            break;
    }
};

function startTimer(targetEndTime) {
    if(timerInterval) {
        clearInterval(timerInterval);
    }
    
    endTime = targetEndTime;
    isRunning = true;
    
    // Tick every 100ms for accuracy
    timerInterval = setInterval(() => {
        const now = Date.now();
        const remaining = Math.ceil((endTime - now) / 1000);
        
        if(remaining <= 0) {
            // Timer finished
            clearInterval(timerInterval);
            timerInterval = null;
            isRunning = false;
            endTime = null;
            
            self.postMessage({
                type: 'finished',
                timeLeft: 0
            });
        } else {
            // Send tick update
            self.postMessage({
                type: 'tick',
                timeLeft: remaining,
                isRunning: true
            });
        }
    }, 100);
    
    // Send immediate state
    sendState();
}

function pauseTimer() {
    if(timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    const remaining = endTime ? Math.max(0, Math.ceil((endTime - Date.now()) / 1000)) : 0;
    isRunning = false;
    endTime = null;
    
    self.postMessage({
        type: 'paused',
        timeLeft: remaining
    });
}

function stopTimer() {
    if(timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    isRunning = false;
    endTime = null;
    
    self.postMessage({
        type: 'stopped'
    });
}

function sendState() {
    const remaining = endTime ? Math.max(0, Math.ceil((endTime - Date.now()) / 1000)) : 0;
    
    self.postMessage({
        type: 'state',
        isRunning: isRunning,
        timeLeft: remaining,
        endTime: endTime
    });
}
