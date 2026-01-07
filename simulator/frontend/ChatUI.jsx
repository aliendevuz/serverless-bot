import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatUI.css';

function ChatUI() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const SIMULATOR_API = process.env.REACT_APP_SIMULATOR_URL || 'http://localhost:8000';

  // Load users on mount
  useEffect(() => {
    loadUsers();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${SIMULATOR_API}/users`);
      setUsers(response.data.users);
      if (response.data.users.length > 0) {
        setSelectedUser(response.data.users[0]);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleSelectUser = (user) => {
    setSelectedUser(user);
    setMessages([]);
    setInputText('');
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || !selectedUser) return;

    const userMessage = inputText;
    setInputText('');
    setLoading(true);

    // Add user message to chat
    setMessages(prev => [...prev, {
      sender: 'user',
      text: userMessage,
      timestamp: new Date().toLocaleTimeString()
    }]);

    try {
      // Send to simulator
      const response = await axios.post(`${SIMULATOR_API}/send-message`, {
        user_id: selectedUser.id,
        chat_id: selectedUser.id,
        text: userMessage
      });

      // Add bot response
      const botText = response.data.bot_response?.text || 'Xato yuz berdi';
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: botText,
        timestamp: new Date().toLocaleTimeString()
      }]);

    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: `❌ Xato: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Users Sidebar */}
      <div className="users-sidebar">
        <h3>Foydalanuvchilar</h3>
        <div className="users-list">
          {users.map(user => (
            <div
              key={user.id}
              className={`user-item ${selectedUser?.id === user.id ? 'active' : ''}`}
              onClick={() => handleSelectUser(user)}
            >
              <div className="user-avatar">
                {user.first_name.charAt(0).toUpperCase()}
              </div>
              <div className="user-info">
                <div className="user-name">{user.first_name}</div>
                <div className="user-username">@{user.username}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="chat-main">
        {selectedUser ? (
          <>
            {/* Header */}
            <div className="chat-header">
              <h2>{selectedUser.first_name} {selectedUser.last_name}</h2>
              <p className="user-status">@{selectedUser.username}</p>
            </div>

            {/* Messages */}
            <div className="messages-area">
              {messages.length === 0 ? (
                <div className="empty-state">
                  <p>Hozir hech qanday xabar yo'q</p>
                  <p className="hint">Xabarni yuboring boshlang</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} className={`message ${msg.sender}`}>
                    <div className="message-content">
                      <p>{msg.text}</p>
                      <span className="message-time">{msg.timestamp}</span>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form className="message-input" onSubmit={handleSendMessage}>
              <input
                type="text"
                placeholder="Xabar yuboring..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading}
              />
              <button type="submit" disabled={loading || !inputText.trim()}>
                {loading ? '⏳' : '📤'}
              </button>
            </form>
          </>
        ) : (
          <div className="no-chat">
            <p>Foydalanuvchini tanlang</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatUI;
