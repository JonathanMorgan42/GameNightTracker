/**
 * WebSocket service for real-time communication using Socket.IO.
 * Handles connection management, reconnection, and event handling.
 */

export class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.eventHandlers = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  /**
   * Connect to Socket.IO server
   */
  connect() {
    if (this.socket) {
      return this.socket;
    }

    // Socket.IO is loaded from CDN
    if (typeof io === 'undefined') {
      console.error('Socket.IO not loaded');
      return null;
    }

    this.socket = io({
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
    });

    this.setupEventHandlers();
    return this.socket;
  }

  /**
   * Set up default event handlers
   */
  setupEventHandlers() {
    this.socket.on('connect', () => {
      this.connected = true;
      this.reconnectAttempts = 0;
      console.log('WebSocket connected');
      this.emit('ws:connected');
    });

    this.socket.on('disconnect', (reason) => {
      this.connected = false;
      console.log('WebSocket disconnected:', reason);
      this.emit('ws:disconnected', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      this.emit('ws:error', error);
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`WebSocket reconnection attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
      this.emit('ws:reconnect_failed');
    });
  }

  /**
   * Disconnect from server
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Join a room
   */
  joinRoom(roomId, data = {}) {
    if (!this.connected) {
      console.warn('Cannot join room: not connected');
      return;
    }

    this.socket.emit('join_game', {
      game_id: roomId,
      ...data,
    });
  }

  /**
   * Leave a room
   */
  leaveRoom(roomId) {
    if (!this.connected) {
      return;
    }

    this.socket.emit('leave_game', {
      game_id: roomId,
    });
  }

  /**
   * Send event to server
   */
  send(event, data) {
    if (!this.connected) {
      console.warn(`Cannot send event ${event}: not connected`);
      return;
    }

    this.socket.emit(event, data);
  }

  /**
   * Listen for event from server
   */
  on(event, callback) {
    if (!this.socket) {
      this.connect();
    }

    // Store handler for removal later
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event).push(callback);

    this.socket.on(event, callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (!this.socket) {
      return;
    }

    this.socket.off(event, callback);

    // Remove from stored handlers
    if (this.eventHandlers.has(event)) {
      const handlers = this.eventHandlers.get(event);
      const index = handlers.indexOf(callback);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Emit custom event (internal event bus)
   */
  emit(event, data) {
    const customEvent = new CustomEvent(event, { detail: data });
    window.dispatchEvent(customEvent);
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected;
  }
}

// Export singleton instance
export const wsService = new WebSocketService();
