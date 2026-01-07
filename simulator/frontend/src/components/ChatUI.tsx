import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './ChatUI.css'

interface Message {
  id: string
  sender: string // user id yoki "bot"
  text: string
  timestamp: string
  buttons?: {
    inline_keyboard?: Array<Array<{text: string; callback_data: string}>>
    reply_keyboard?: Array<Array<{text: string}>>
  }
}

interface Chat {
  id: string
  name: string
  type: 'bot' | 'user' // bot yoki user to user chat
  otherUserId?: number // user to user chatda qo'shni user id
  messages: Message[]
}

interface LocalUser {
  id: number
  name: string
  chats: Chat[]
}

const STORAGE_KEY = 'telegram_bot_simulator_chats'
const MODE_STORAGE_KEY = 'telegram_bot_simulator_mode'
const SIMULATOR_API = import.meta.env.VITE_SIMULATOR_URL || 'http://localhost:8000'

// Local storage helper
const getStorageData = (): LocalUser[] => {
  const data = localStorage.getItem(STORAGE_KEY)
  return data ? JSON.parse(data) : []
}

const saveStorageData = (data: LocalUser[]) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

const getMode = (): 'local' | 'aws' => {
  const mode = localStorage.getItem(MODE_STORAGE_KEY)
  return (mode as 'local' | 'aws') || 'local'
}

const saveMode = (mode: 'local' | 'aws') => {
  localStorage.setItem(MODE_STORAGE_KEY, mode)
}

// Linkification helper - yangi funksiyalar
const linkifyText = (text: string): (string | JSX.Element)[] => {
  const parts: (string | JSX.Element)[] = []
  let lastIndex = 0
  
  // URLs linkify
  const urlRegex = /(https?:\/\/[^\s]+)/g
  let match
  let keyCounter = 0
  
  while ((match = urlRegex.exec(text)) !== null) {
    // Add text before URL
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index))
    }
    
    // Add URL as link
    const url = match[0]
    parts.push(
      <a
        key={`url-${keyCounter++}`}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="message-link"
      >
        {url}
      </a>
    )
    
    lastIndex = match.index + match[0].length
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex))
  }
  
  // If no URLs found, return original text in array
  if (parts.length === 0) {
    return [text]
  }
  
  return parts
}

const renderMessageContent = (text: string): JSX.Element | JSX.Element[] => {
  const lines = text.split('\n')
  const elements = lines.map((line, idx) => (
    <div key={`line-${idx}`}>
      {linkifyText(line).map((part, partIdx) => (
        typeof part === 'string' ? (
          <span key={`part-${partIdx}`}>{part}</span>
        ) : (
          <React.Fragment key={`part-${partIdx}`}>{part}</React.Fragment>
        )
      ))}
    </div>
  ))
  
  return elements.length === 1 ? elements[0] : elements
}

export default function ChatUI() {
  const [localUsers, setLocalUsers] = useState<LocalUser[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [showNewChatDialog, setShowNewChatDialog] = useState(false)
  const [newChatName, setNewChatName] = useState('')
  const [newChatType, setNewChatType] = useState<'bot' | 'user'>('user')
  const [newChatUserId, setNewChatUserId] = useState<number | null>(null)
  const [showNewUserDialog, setShowNewUserDialog] = useState(false)
  const [newUserName, setNewUserName] = useState('')
  const [lambdaMode, setLambdaMode] = useState<'local' | 'aws'>('local')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Init on mount
  useEffect(() => {
    initLocalUsers()
    const savedMode = getMode()
    setLambdaMode(savedMode)
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [selectedChatId])

  const initLocalUsers = () => {
    const stored = getStorageData()
    if (stored.length === 0) {
      // Default users bilan init
      const defaults: LocalUser[] = [
        {
          id: 999001,
          name: 'Ali',
          chats: [{ id: 'bot_1', name: '🤖 Bot', type: 'bot', messages: [] }]
        },
        {
          id: 999002,
          name: 'Fotima',
          chats: [{ id: 'bot_2', name: '🤖 Bot', type: 'bot', messages: [] }]
        }
      ]
      saveStorageData(defaults)
      setLocalUsers(defaults)
      setSelectedUserId(defaults[0].id)
      setSelectedChatId(defaults[0].chats[0].id)
    } else {
      setLocalUsers(stored)
      setSelectedUserId(stored[0].id)
      setSelectedChatId(stored[0].chats[0].id)
    }
  }

  const getCurrentUser = () => localUsers.find(u => u.id === selectedUserId)
  const getCurrentChat = () => getCurrentUser()?.chats.find(c => c.id === selectedChatId)

  const handleAddUser = () => {
    if (!newUserName.trim()) {
      alert('Foydalanuvchi nomini kiriting!')
      return
    }

    if (localUsers.some(u => u.name.toLowerCase() === newUserName.trim().toLowerCase())) {
      alert('Bu nom bilan foydalanuvchi allaqachon mavjud!')
      return
    }

    const newId = Math.max(0, ...localUsers.map(u => u.id)) + 1
    const newUser: LocalUser = {
      id: newId,
      name: newUserName.trim(),
      chats: [
        {
          id: `bot_${newId}`,
          name: '🤖 Bot',
          type: 'bot',
          messages: []
        }
      ]
    }

    const updated = [...localUsers, newUser]
    saveStorageData(updated)
    setLocalUsers(updated)
    setSelectedUserId(newId)
    setSelectedChatId(`bot_${newId}`)
    setShowNewUserDialog(false)
    setNewUserName('')
  }

  const handleDeleteUser = (userId: number) => {
    if (localUsers.length === 1) {
      alert('Kamida bitta foydalanuvchi qolishi kerak!')
      return
    }

    if (!confirm(`${localUsers.find(u => u.id === userId)?.name}ni o'chirishga ishonchisizmi?`)) {
      return
    }

    const updated = localUsers.filter(u => u.id !== userId)
    saveStorageData(updated)
    setLocalUsers(updated)

    if (selectedUserId === userId) {
      setSelectedUserId(updated[0]?.id ?? null)
      setSelectedChatId(updated[0]?.chats[0]?.id ?? null)
    }
  }

  const handleAddChat = () => {
    if (!selectedUserId || !newChatName.trim()) return
    
    const updatedUsers = localUsers.map(user => {
      if (user.id === selectedUserId) {
        const newChat: Chat = {
          id: `chat_${Date.now()}`,
          name: newChatName,
          type: newChatType,
          otherUserId: newChatUserId || undefined,
          messages: []
        }
        return { ...user, chats: [...user.chats, newChat] }
      }
      return user
    })
    
    setLocalUsers(updatedUsers)
    saveStorageData(updatedUsers)
    setShowNewChatDialog(false)
    setNewChatName('')
    setNewChatType('user')
    setNewChatUserId(null)
  }

  const handleDeleteChat = (chatId: string) => {
    const updatedUsers = localUsers.map(user => {
      if (user.id === selectedUserId) {
        const filtered = user.chats.filter(c => c.id !== chatId)
        return { ...user, chats: filtered }
      }
      return user
    })
    
    setLocalUsers(updatedUsers)
    saveStorageData(updatedUsers)
    
    if (selectedChatId === chatId) {
      const user = updatedUsers.find(u => u.id === selectedUserId)
      if (user && user.chats.length > 0) {
        setSelectedChatId(user.chats[0].id)
      }
    }
  }

  const handleClearChat = () => {
    if (!selectedUserId || !selectedChatId) return
    if (!confirm('Chatni tozalashga ishonchisizmi?')) return
    
    const updatedUsers = localUsers.map(user => {
      if (user.id === selectedUserId) {
        return {
          ...user,
          chats: user.chats.map(chat =>
            chat.id === selectedChatId ? { ...chat, messages: [] } : chat
          )
        }
      }
      return user
    })
    
    setLocalUsers(updatedUsers)
    saveStorageData(updatedUsers)
  }

  const handleCallbackButton = async (callbackData: string) => {
    if (!selectedUserId || !selectedChatId) return

    const currentChat = getCurrentChat()
    if (!currentChat || currentChat.type !== 'bot') return

    setLoading(true)
    try {
      const response = await axios.post(`${SIMULATOR_API}/send-callback`, {
        user_id: selectedUserId,
        callback_data: callbackData,
        mode: lambdaMode
      })

      const botText = response.data.response_text || 'Javob topilmadi'
      const botReplyId = `msg_${Date.now()}`

      const updatedUsers = localUsers.map(user => {
        if (user.id === selectedUserId) {
          return {
            ...user,
            chats: user.chats.map(chat => {
              if (chat.id === selectedChatId) {
                return {
                  ...chat,
                  messages: [...chat.messages, {
                    id: botReplyId,
                    sender: 'bot',
                    text: botText,
                    timestamp: new Date().toLocaleTimeString('uz-UZ')
                  }]
                }
              }
              return chat
            })
          }
        }
        return user
      })

      setLocalUsers(updatedUsers)
      saveStorageData(updatedUsers)
    } catch (error) {
      console.error('Failed to send callback:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || !selectedUserId || !selectedChatId) return

    const currentChat = getCurrentChat()
    if (!currentChat) return

    const userMessage = inputText
    setInputText('')
    const messageId = `msg_${Date.now()}`

    // Add user message immediately
    const updatedUsers = localUsers.map(user => {
      if (user.id === selectedUserId) {
        return {
          ...user,
          chats: user.chats.map(chat => {
            if (chat.id === selectedChatId) {
              return {
                ...chat,
                messages: [...chat.messages, {
                  id: messageId,
                  sender: String(selectedUserId),
                  text: userMessage,
                  timestamp: new Date().toLocaleTimeString('uz-UZ')
                }]
              }
            }
            return chat
          })
        }
      }
      return user
    })

    setLocalUsers(updatedUsers)
    saveStorageData(updatedUsers)

    // Handle bot chat separately
    if (currentChat.type === 'bot') {
      setLoading(true)
      try {
        const response = await axios.post(`${SIMULATOR_API}/send-message`, {
          user_id: selectedUserId,
          text: userMessage,
          mode: lambdaMode
        })

        const botText = response.data.response_text || 'Javob topilmadi'
        const botReplyId = `msg_${Date.now()}`
        const botButtons = response.data.buttons || undefined

        // Add bot response
        const finalUsers = updatedUsers.map(user => {
          if (user.id === selectedUserId) {
            return {
              ...user,
              chats: user.chats.map(chat => {
                if (chat.id === selectedChatId) {
                  return {
                    ...chat,
                    messages: [...chat.messages, {
                      id: botReplyId,
                      sender: 'bot',
                      text: botText,
                      timestamp: new Date().toLocaleTimeString('uz-UZ'),
                      buttons: botButtons
                    }]
                  }
                }
                return chat
              })
            }
          }
          return user
        })

        setLocalUsers(finalUsers)
        saveStorageData(finalUsers)
      } catch (error) {
        console.error('Failed to send to bot:', error)
        const errorMsg = (error as any).response?.data?.message || (error as any).message
        
        const errorUsers = updatedUsers.map(user => {
          if (user.id === selectedUserId) {
            return {
              ...user,
              chats: user.chats.map(chat => {
                if (chat.id === selectedChatId) {
                  return {
                    ...chat,
                    messages: [...chat.messages, {
                      id: `msg_${Date.now()}`,
                      sender: 'bot',
                      text: `❌ Xato: ${errorMsg}`,
                      timestamp: new Date().toLocaleTimeString('uz-UZ')
                    }]
                  }
                }
                return chat
              })
            }
          }
          return user
        })

        setLocalUsers(errorUsers)
        saveStorageData(errorUsers)
      } finally {
        setLoading(false)
      }
    } else if (currentChat.type === 'user' && currentChat.otherUserId) {
      // User to user chat - add message to other user's chat too
      const otherUserId = currentChat.otherUserId
      const finalUsers = updatedUsers.map(user => {
        if (user.id === otherUserId) {
          // Find or create corresponding chat
          const hasChat = user.chats.find(
            c => c.type === 'user' && c.otherUserId === selectedUserId
          )
          
          if (hasChat) {
            return {
              ...user,
              chats: user.chats.map(chat => {
                if (chat.id === hasChat.id) {
                  return {
                    ...chat,
                    messages: [...chat.messages, {
                      id: messageId,
                      sender: String(selectedUserId),
                      text: userMessage,
                      timestamp: new Date().toLocaleTimeString('uz-UZ')
                    }]
                  }
                }
                return chat
              })
            }
          } else {
            // Create chat for other user
            const currentUserName = getCurrentUser()?.name || 'Unknown'
            return {
              ...user,
              chats: [...user.chats, {
                id: `chat_${Date.now()}_${selectedUserId}`,
                name: currentUserName,
                type: 'user',
                otherUserId: selectedUserId,
                messages: [{
                  id: messageId,
                  sender: String(selectedUserId),
                  text: userMessage,
                  timestamp: new Date().toLocaleTimeString('uz-UZ')
                }]
              }]
            }
          }
        }
        return user
      })

      setLocalUsers(finalUsers)
      saveStorageData(finalUsers)
    }
  }

  return (
    <div className="chat-container">
      {/* Users Sidebar */}
      <div className="users-sidebar">
        <div className="sidebar-header">
          <h3>👥 Foydalanuvchilar</h3>
          <button
            className="add-user-btn"
            onClick={() => setShowNewUserDialog(true)}
            title="Yangi foydalanuvchi qo'shish"
          >
            ➕
          </button>
        </div>
        <div className="users-list">
          {localUsers.map(user => (
            <div
              key={user.id}
              className={`user-item ${selectedUserId === user.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedUserId(user.id)
                if (user.chats.length > 0) {
                  setSelectedChatId(user.chats[0].id)
                }
              }}
            >
              <div className="user-avatar">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="user-info">
                <div className="user-name">{user.name}</div>
                <div className="user-status">{user.chats.length} chat</div>
              </div>
              {localUsers.length > 1 && (
                <button
                  className="delete-user-btn"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteUser(user.id)
                  }}
                  title="Foydalanuvchini o'chirish"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        {/* New User Dialog */}
        {showNewUserDialog && (
          <div className="user-dialog">
            <div className="dialog-header">
              <h4>Yangi Foydalanuvchi</h4>
              <button
                onClick={() => setShowNewUserDialog(false)}
                className="close-btn"
              >
                ✕
              </button>
            </div>
            <div className="dialog-body">
              <input
                type="text"
                placeholder="Foydalanuvchi nomi..."
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddUser()}
                autoFocus
              />
            </div>
            <div className="dialog-footer">
              <button
                onClick={() => setShowNewUserDialog(false)}
                className="btn-cancel"
              >
                Bekor
              </button>
              <button
                onClick={handleAddUser}
                className="btn-create"
                disabled={!newUserName.trim()}
              >
                Yaratish
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Chats Sidebar */}
      <div className="chats-sidebar">
        {selectedUserId && (
          <>
            <div className="chats-header">
              <h4>💬 Chatlar</h4>
              <div className="header-buttons">
                <select
                  value={lambdaMode}
                  onChange={(e) => {
                    const newMode = e.target.value as 'local' | 'aws'
                    setLambdaMode(newMode)
                    saveMode(newMode)
                  }}
                  className="mode-select"
                  title="Lambda mode: local (testing) yoki aws (production)"
                >
                  <option value="local">🖥️ Local</option>
                  <option value="aws">☁️ AWS</option>
                </select>
                <button
                  className="add-chat-btn"
                  onClick={() => setShowNewChatDialog(true)}
                  title="Yangi chat qo'shish"
                >
                  ➕
                </button>
              </div>
            </div>

            <div className="chats-list">
              {getCurrentUser()?.chats.map(chat => (
                <div
                  key={chat.id}
                  className={`chat-item ${selectedChatId === chat.id ? 'active' : ''}`}
                  onClick={() => setSelectedChatId(chat.id)}
                >
                  <div className="chat-name">{chat.name}</div>
                  <div className="chat-badge">{chat.messages.length}</div>
                  {chat.type === 'user' && (
                    <button
                      className="delete-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteChat(chat.id)
                      }}
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* New Chat Dialog */}
            {showNewChatDialog && (
              <div className="chat-dialog">
                <div className="dialog-header">
                  <h4>Yangi Chat</h4>
                  <button
                    onClick={() => setShowNewChatDialog(false)}
                    className="close-btn"
                  >
                    ✕
                  </button>
                </div>
                <div className="dialog-body">
                  <input
                    type="text"
                    placeholder="Chat nomi..."
                    value={newChatName}
                    onChange={(e) => setNewChatName(e.target.value)}
                    autoFocus
                  />
                  <select
                    value={newChatType}
                    onChange={(e) => setNewChatType(e.target.value as 'bot' | 'user')}
                  >
                    <option value="user">Foydalanuvchi chatsi</option>
                    <option value="bot">Bot chatsi</option>
                  </select>
                  {newChatType === 'user' && (
                    <select
                      value={newChatUserId || ''}
                      onChange={(e) => setNewChatUserId(Number(e.target.value))}
                    >
                      <option value="">Foydalanuvchi tanlang</option>
                      {localUsers
                        .filter(u => u.id !== selectedUserId)
                        .map(u => (
                          <option key={u.id} value={u.id}>
                            {u.name}
                          </option>
                        ))}
                    </select>
                  )}
                </div>
                <div className="dialog-footer">
                  <button
                    onClick={() => setShowNewChatDialog(false)}
                    className="btn-cancel"
                  >
                    Bekor
                  </button>
                  <button
                    onClick={handleAddChat}
                    className="btn-create"
                    disabled={!newChatName.trim() || (newChatType === 'user' && !newChatUserId)}
                  >
                    Yaratish
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Chat Area */}
      <div className="chat-main">
        {selectedChatId && getCurrentChat() ? (
          <>
            {/* Header */}
            <div className="chat-header">
              <div className="header-content">
                <h2>{getCurrentChat()?.name}</h2>
                <p className="chat-info">
                  {getCurrentChat()?.type === 'bot' ? '🤖 Bot' : `👤 ${getCurrentUser()?.name}`}
                </p>
              </div>
              <div className="header-actions">
                <button
                  className="clear-btn"
                  onClick={handleClearChat}
                  title="Chatni tozalash"
                >
                  🗑️
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="messages-area">
              {getCurrentChat()?.messages.length === 0 ? (
                <div className="empty-state">
                  <p className="empty-emoji">💬</p>
                  <p className="empty-title">Hech qanday xabar yo'q</p>
                  <p className="empty-hint">Xabarni yuboring boshlang</p>
                </div>
              ) : (
                getCurrentChat()?.messages.map((msg) => {
                  const isBotMessage = msg.sender === 'bot'
                  const isOwnMessage = msg.sender === String(selectedUserId)

                  return (
                    <div key={msg.id} className={`message ${isBotMessage ? 'bot' : isOwnMessage ? 'user' : 'other'}`}>
                      {!isOwnMessage && !isBotMessage && (
                        <div className="message-sender">
                          {localUsers.find(u => u.id === Number(msg.sender))?.name}
                        </div>
                      )}
                      <div className="message-content">
                        <div className="message-text">
                          {renderMessageContent(msg.text)}
                        </div>
                        {msg.buttons && msg.buttons.inline_keyboard && (
                          <div className="inline-buttons">
                            {msg.buttons.inline_keyboard.map((row, rowIdx) => (
                              <div key={rowIdx} className="button-row">
                                {row.map((btn, btnIdx) => (
                                  <button
                                    key={btnIdx}
                                    className="inline-button"
                                    onClick={() => handleCallbackButton(btn.callback_data)}
                                    disabled={loading}
                                  >
                                    {btn.text}
                                  </button>
                                ))}
                              </div>
                            ))}
                          </div>
                        )}
                        <span className="message-time">{msg.timestamp}</span>
                      </div>
                    </div>
                  )
                })
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
            <p>📱 Chat tanlang</p>
          </div>
        )}
      </div>
    </div>
  )
}
