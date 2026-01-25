# Operator Panel Design Rules

> Applies to: `/inbox`, `/inbox/queue`, `/inbox/all`, `/inbox/archive`, `/inbox/:conversationId`, `/customers`, `/customers/:customerId`, `/search`, `/canned-responses`

---

## Layout Structure

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Top Bar (h: 56px)                                                           │
│  Logo | Search | Notifications | User                                         │
├────────────┬─────────────────────────────────────────────────────────────────┤
│            │                                                                  │
│  Sidebar   │  Main Content Area                                              │
│  (w: 64px) │                                                                  │
│            │  ┌─────────────────┬──────────────────────┬─────────────────┐   │
│  • Inbox   │  │ Conversations   │  Chat View           │  Customer Card  │   │
│  • Custom. │  │ List (280px)    │  (flex)              │  (320px)        │   │
│  • Search  │  │                 │                      │                 │   │
│  • Quick   │  │                 │                      │                 │   │
│            │  └─────────────────┴──────────────────────┴─────────────────┘   │
│            │                                                                  │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## Top Bar

```css
.operator-topbar {
  height: 56px;
  background: white;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  padding: 0 16px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.operator-logo {
  width: 32px;
  height: 32px;
  margin-right: 24px;
}

.operator-search {
  flex: 1;
  max-width: 400px;
  position: relative;
}

.operator-search-input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  background: #F1F5F9;
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  transition: all 200ms ease;
}

.operator-search-input:focus {
  background: white;
  border-color: #0369A1;
  outline: none;
}

.operator-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748B;
}

.operator-topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.operator-notification-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748B;
  transition: all 200ms ease;
}

.operator-notification-btn:hover {
  background: #F1F5F9;
  color: #0F172A;
}

.operator-notification-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: #DC2626;
  border-radius: 50%;
}

.operator-user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
}

.operator-user-menu:hover {
  background: #F1F5F9;
}

.operator-user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #0369A1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.operator-user-status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid white;
  position: absolute;
  bottom: -2px;
  right: -2px;
}

.operator-user-status.online {
  background: #22C55E;
}

.operator-user-status.away {
  background: #F59E0B;
}

.operator-user-status.offline {
  background: #94A3B8;
}
```

---

## Sidebar

```css
.operator-sidebar {
  width: 64px;
  background: #0F172A;
  position: fixed;
  top: 56px;
  left: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  z-index: 90;
}

.operator-sidebar-item {
  width: 48px;
  height: 48px;
  margin: 0 8px 8px;
  border-radius: 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  position: relative;
  transition: all 200ms ease;
}

.operator-sidebar-item:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.operator-sidebar-item.active {
  background: #0369A1;
  color: white;
}

.operator-sidebar-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  background: #DC2626;
  color: white;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.operator-sidebar-tooltip {
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 8px;
  padding: 6px 12px;
  background: #1E293B;
  color: white;
  font-size: 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease;
}

.operator-sidebar-item:hover .operator-sidebar-tooltip {
  opacity: 1;
}
```

---

## Conversations List

```css
.conversations-panel {
  width: 280px;
  background: white;
  border-right: 1px solid #E2E8F0;
  height: calc(100vh - 56px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.conversations-header {
  padding: 16px;
  border-bottom: 1px solid #E2E8F0;
}

.conversations-tabs {
  display: flex;
  gap: 4px;
  background: #F1F5F9;
  padding: 4px;
  border-radius: 8px;
}

.conversations-tab {
  flex: 1;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
  transition: all 200ms ease;
}

.conversations-tab.active {
  background: white;
  color: #0F172A;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  padding: 12px 16px;
  border-bottom: 1px solid #F1F5F9;
  cursor: pointer;
  transition: all 200ms ease;
  display: flex;
  gap: 12px;
}

.conversation-item:hover {
  background: #F8FAFC;
}

.conversation-item.active {
  background: #EFF6FF;
  border-left: 3px solid #0369A1;
}

.conversation-item.unread {
  background: #FEF9C3;
}

.conversation-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #E2E8F0;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #64748B;
}

.conversation-content {
  flex: 1;
  min-width: 0;
}

.conversation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.conversation-name {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: 11px;
  color: #94A3B8;
  flex-shrink: 0;
}

.conversation-preview {
  font-size: 13px;
  color: #64748B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-preview.unread {
  font-weight: 500;
  color: #0F172A;
}

.conversation-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.conversation-channel {
  width: 16px;
  height: 16px;
}

.conversation-tag {
  font-size: 10px;
  padding: 2px 6px;
  background: #E0F2FE;
  color: #0369A1;
  border-radius: 4px;
}
```

---

## Chat View

```css
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #F8FAFC;
  height: calc(100vh - 56px);
}

.chat-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-customer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-customer-name {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.chat-customer-status {
  font-size: 12px;
  color: #64748B;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.chat-action-btn {
  padding: 8px 12px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 13px;
  color: #64748B;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 200ms ease;
}

.chat-action-btn:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
  color: #0F172A;
}

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message.customer {
  align-self: flex-start;
}

.message.operator {
  align-self: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.message.customer .message-bubble {
  background: white;
  color: #0F172A;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.message.operator .message-bubble {
  background: #0369A1;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #94A3B8;
  margin-top: 4px;
  padding: 0 4px;
}

.message.operator .message-time {
  text-align: right;
}

/* AI Suggestion */
.ai-suggestion {
  background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
  border: 1px solid #C7D2FE;
  border-radius: 12px;
  padding: 16px;
  margin: 8px 24px;
}

.ai-suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-suggestion-icon {
  width: 20px;
  height: 20px;
  color: #6366F1;
}

.ai-suggestion-label {
  font-size: 12px;
  font-weight: 600;
  color: #4F46E5;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ai-suggestion-text {
  font-size: 14px;
  color: #1E1B4B;
  line-height: 1.5;
  margin-bottom: 12px;
}

.ai-suggestion-actions {
  display: flex;
  gap: 8px;
}

.ai-suggestion-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
}

.ai-suggestion-btn.accept {
  background: #4F46E5;
  color: white;
  border: none;
}

.ai-suggestion-btn.accept:hover {
  background: #4338CA;
}

.ai-suggestion-btn.edit {
  background: white;
  color: #4F46E5;
  border: 1px solid #C7D2FE;
}

.ai-suggestion-btn.dismiss {
  background: transparent;
  color: #64748B;
  border: none;
}

/* Input Area */
.chat-input-area {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #E2E8F0;
}

.chat-input-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.chat-toolbar-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #64748B;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease;
}

.chat-toolbar-btn:hover {
  background: #F1F5F9;
  color: #0F172A;
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-textarea {
  flex: 1;
  min-height: 44px;
  max-height: 120px;
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  font-size: 14px;
  resize: none;
  transition: all 200ms ease;
}

.chat-textarea:focus {
  border-color: #0369A1;
  outline: none;
}

.chat-send-btn {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #0369A1;
  border: none;
  cursor: pointer;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease;
}

.chat-send-btn:hover {
  background: #0284C7;
  transform: scale(1.05);
}

.chat-send-btn:disabled {
  background: #94A3B8;
  cursor: not-allowed;
  transform: none;
}
```

---

## Customer Card (Right Panel)

```css
.customer-card-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #E2E8F0;
  height: calc(100vh - 56px);
  overflow-y: auto;
}

.customer-card-header {
  padding: 24px;
  text-align: center;
  border-bottom: 1px solid #E2E8F0;
}

.customer-card-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #E2E8F0;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 600;
  color: #64748B;
}

.customer-card-name {
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 4px;
}

.customer-card-email {
  font-size: 14px;
  color: #64748B;
}

.customer-card-section {
  padding: 16px 24px;
  border-bottom: 1px solid #F1F5F9;
}

.customer-card-section-title {
  font-size: 11px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.customer-card-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.customer-card-label {
  font-size: 13px;
  color: #64748B;
}

.customer-card-value {
  font-size: 13px;
  font-weight: 500;
  color: #0F172A;
}

.customer-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.customer-card-tag {
  font-size: 12px;
  padding: 4px 8px;
  background: #F1F5F9;
  color: #475569;
  border-radius: 4px;
}

.customer-card-history {
  padding: 16px 24px;
}

.customer-card-history-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #F1F5F9;
}

.customer-card-history-item:last-child {
  border-bottom: none;
}

.customer-card-history-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #F1F5F9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.customer-card-history-content {
  flex: 1;
}

.customer-card-history-title {
  font-size: 13px;
  font-weight: 500;
  color: #0F172A;
  margin-bottom: 2px;
}

.customer-card-history-meta {
  font-size: 12px;
  color: #94A3B8;
}
```

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New message | `Ctrl/Cmd + N` |
| Search | `Ctrl/Cmd + K` |
| Send message | `Ctrl/Cmd + Enter` |
| Accept AI suggestion | `Tab` |
| Close conversation | `Ctrl/Cmd + W` |
| Next conversation | `Alt + ↓` |
| Previous conversation | `Alt + ↑` |

---

## Status Colors

| Status | Background | Text |
|--------|------------|------|
| Open | `#DCFCE7` | `#166534` |
| Pending | `#FEF9C3` | `#854D0E` |
| Resolved | `#E0E7FF` | `#3730A3` |
| Closed | `#F1F5F9` | `#475569` |
