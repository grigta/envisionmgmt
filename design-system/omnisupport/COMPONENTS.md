# OmniSupport Component Library

> Global reusable components for all pages. Import these alongside MASTER.md tokens.

---

## Buttons

### Primary Button
```html
<button class="btn btn-primary">
  <span>Начать бесплатно</span>
</button>
```

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
  border: none;
  text-decoration: none;
}

.btn-primary {
  background: var(--color-cta);
  color: white;
}

.btn-primary:hover {
  background: #0284C7;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(3, 105, 161, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  background: #94A3B8;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
```

### Secondary Button
```css
.btn-secondary {
  background: white;
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
}

.btn-secondary:hover {
  background: var(--color-primary);
  color: white;
}
```

### Ghost Button
```css
.btn-ghost {
  background: transparent;
  color: var(--color-secondary);
}

.btn-ghost:hover {
  background: #F1F5F9;
  color: var(--color-primary);
}
```

### Danger Button
```css
.btn-danger {
  background: #DC2626;
  color: white;
}

.btn-danger:hover {
  background: #B91C1C;
}
```

### Button Sizes
```css
.btn-sm {
  padding: 8px 16px;
  font-size: 13px;
}

.btn-lg {
  padding: 16px 32px;
  font-size: 16px;
}

.btn-icon {
  padding: 10px;
  min-width: 40px;
}
```

### Button with Icon
```html
<button class="btn btn-primary">
  <svg>...</svg>
  <span>Добавить</span>
</button>
```

---

## Form Inputs

### Text Input
```html
<div class="form-group">
  <label class="form-label">Email</label>
  <input type="email" class="form-input" placeholder="name@company.com" />
  <span class="form-hint">Мы никогда не передадим ваш email третьим лицам</span>
</div>
```

```css
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  margin-bottom: 6px;
}

.form-label-optional {
  font-weight: 400;
  color: #94A3B8;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F172A;
  background: white;
  transition: all 200ms ease;
}

.form-input::placeholder {
  color: #94A3B8;
}

.form-input:hover {
  border-color: #CBD5E1;
}

.form-input:focus {
  border-color: var(--color-cta);
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}

.form-input:disabled {
  background: #F8FAFC;
  color: #94A3B8;
  cursor: not-allowed;
}

.form-input.error {
  border-color: #DC2626;
}

.form-input.error:focus {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #64748B;
  margin-top: 4px;
}

.form-error {
  display: block;
  font-size: 12px;
  color: #DC2626;
  margin-top: 4px;
}
```

### Textarea
```css
.form-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F172A;
  resize: vertical;
  transition: all 200ms ease;
}

.form-textarea:focus {
  border-color: var(--color-cta);
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}
```

### Select
```css
.form-select {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 15px;
  color: #0F172A;
  background: white;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  appearance: none;
  cursor: pointer;
  transition: all 200ms ease;
}

.form-select:focus {
  border-color: var(--color-cta);
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}
```

### Checkbox
```html
<label class="form-checkbox">
  <input type="checkbox" />
  <span class="form-checkbox-box"></span>
  <span class="form-checkbox-label">Согласен с условиями использования</span>
</label>
```

```css
.form-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
}

.form-checkbox input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.form-checkbox-box {
  width: 20px;
  height: 20px;
  border: 2px solid #E2E8F0;
  border-radius: 4px;
  flex-shrink: 0;
  transition: all 200ms ease;
  position: relative;
}

.form-checkbox input:checked + .form-checkbox-box {
  background: var(--color-cta);
  border-color: var(--color-cta);
}

.form-checkbox input:checked + .form-checkbox-box::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 6px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.form-checkbox-label {
  font-size: 14px;
  color: #334155;
  line-height: 1.4;
}
```

### Radio
```css
.form-radio-box {
  width: 20px;
  height: 20px;
  border: 2px solid #E2E8F0;
  border-radius: 50%;
  flex-shrink: 0;
  transition: all 200ms ease;
  position: relative;
}

.form-radio input:checked + .form-radio-box {
  border-color: var(--color-cta);
}

.form-radio input:checked + .form-radio-box::after {
  content: '';
  position: absolute;
  top: 4px;
  left: 4px;
  width: 8px;
  height: 8px;
  background: var(--color-cta);
  border-radius: 50%;
}
```

### Toggle Switch
```html
<label class="form-toggle">
  <input type="checkbox" />
  <span class="form-toggle-track"></span>
  <span class="form-toggle-label">Включить уведомления</span>
</label>
```

```css
.form-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.form-toggle input {
  position: absolute;
  opacity: 0;
}

.form-toggle-track {
  width: 48px;
  height: 24px;
  background: #E2E8F0;
  border-radius: 12px;
  position: relative;
  transition: all 200ms ease;
  flex-shrink: 0;
}

.form-toggle-track::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: all 200ms ease;
}

.form-toggle input:checked + .form-toggle-track {
  background: var(--color-cta);
}

.form-toggle input:checked + .form-toggle-track::after {
  transform: translateX(24px);
}

.form-toggle-label {
  font-size: 14px;
  color: #334155;
}
```

---

## Cards

### Basic Card
```css
.card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #F1F5F9;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.card-description {
  font-size: 13px;
  color: #64748B;
  margin-top: 4px;
}

.card-body {
  padding: 24px;
}

.card-footer {
  padding: 16px 24px;
  background: #F8FAFC;
  border-top: 1px solid #F1F5F9;
}
```

### Interactive Card
```css
.card-interactive {
  cursor: pointer;
  transition: all 200ms ease;
}

.card-interactive:hover {
  border-color: #CBD5E1;
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

---

## Badges & Tags

### Badge
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge-primary {
  background: #EFF6FF;
  color: #0369A1;
}

.badge-success {
  background: #DCFCE7;
  color: #166534;
}

.badge-warning {
  background: #FEF3C7;
  color: #B45309;
}

.badge-danger {
  background: #FEE2E2;
  color: #DC2626;
}

.badge-neutral {
  background: #F1F5F9;
  color: #475569;
}
```

### Tag
```css
.tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #F1F5F9;
  border-radius: 4px;
  font-size: 12px;
  color: #475569;
}

.tag-removable {
  cursor: pointer;
}

.tag-remove {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 200ms ease;
}

.tag-remove:hover {
  background: rgba(0,0,0,0.1);
}
```

---

## Avatars

```css
.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #E2E8F0;
  color: #64748B;
  font-weight: 600;
  overflow: hidden;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-xs { width: 24px; height: 24px; font-size: 10px; }
.avatar-sm { width: 32px; height: 32px; font-size: 12px; }
.avatar-md { width: 40px; height: 40px; font-size: 14px; }
.avatar-lg { width: 56px; height: 56px; font-size: 18px; }
.avatar-xl { width: 80px; height: 80px; font-size: 24px; }

.avatar-group {
  display: flex;
}

.avatar-group .avatar {
  border: 2px solid white;
  margin-left: -8px;
}

.avatar-group .avatar:first-child {
  margin-left: 0;
}
```

---

## Dropdowns

```css
.dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  min-width: 200px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  border: 1px solid #E2E8F0;
  z-index: 50;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 200ms ease;
}

.dropdown.open .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  font-size: 14px;
  color: #334155;
  cursor: pointer;
  transition: background 200ms ease;
}

.dropdown-item:hover {
  background: #F8FAFC;
}

.dropdown-item svg {
  width: 18px;
  height: 18px;
  color: #64748B;
}

.dropdown-divider {
  height: 1px;
  background: #E2E8F0;
  margin: 8px 0;
}
```

---

## Modals

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  opacity: 0;
  visibility: hidden;
  transition: all 200ms ease;
}

.modal-overlay.open {
  opacity: 1;
  visibility: visible;
}

.modal {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  transform: scale(0.95);
  transition: transform 200ms ease;
}

.modal-overlay.open .modal {
  transform: scale(1);
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #64748B;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease;
}

.modal-close:hover {
  background: #F1F5F9;
  color: #0F172A;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  padding: 16px 24px;
  background: #F8FAFC;
  border-top: 1px solid #E2E8F0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
```

---

## Toasts / Notifications

```css
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  border: 1px solid #E2E8F0;
  min-width: 320px;
  max-width: 400px;
  animation: toast-slide-in 300ms ease;
}

@keyframes toast-slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.toast-success .toast-icon { color: #22C55E; }
.toast-error .toast-icon { color: #DC2626; }
.toast-warning .toast-icon { color: #F59E0B; }
.toast-info .toast-icon { color: #0369A1; }

.toast-content {
  flex: 1;
}

.toast-title {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 2px;
}

.toast-message {
  font-size: 13px;
  color: #64748B;
}

.toast-close {
  width: 20px;
  height: 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #94A3B8;
  flex-shrink: 0;
}
```

---

## Loading States

### Spinner
```css
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #E2E8F0;
  border-top-color: var(--color-cta);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner-sm { width: 16px; height: 16px; border-width: 2px; }
.spinner-lg { width: 40px; height: 40px; border-width: 4px; }
```

### Skeleton
```css
.skeleton {
  background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-text {
  height: 16px;
  margin-bottom: 8px;
}

.skeleton-text:last-child {
  width: 70%;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.skeleton-button {
  height: 44px;
  width: 120px;
}
```

---

## Empty States

```css
.empty-state {
  text-align: center;
  padding: 64px 24px;
}

.empty-state-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: #CBD5E1;
}

.empty-state-title {
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 8px;
}

.empty-state-description {
  font-size: 14px;
  color: #64748B;
  max-width: 360px;
  margin: 0 auto 24px;
}
```

---

## Tooltips

```css
.tooltip {
  position: relative;
}

.tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #1E293B;
  color: white;
  font-size: 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 200ms ease;
  z-index: 50;
}

.tooltip-content::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #1E293B;
}

.tooltip:hover .tooltip-content {
  opacity: 1;
  visibility: visible;
}
```

---

## Progress Indicators

### Progress Bar
```css
.progress {
  height: 8px;
  background: #E2E8F0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--color-cta);
  border-radius: 4px;
  transition: width 300ms ease;
}

.progress-bar.success { background: #22C55E; }
.progress-bar.warning { background: #F59E0B; }
.progress-bar.danger { background: #DC2626; }
```

### Steps
```css
.steps {
  display: flex;
  align-items: center;
}

.step {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #E2E8F0;
  color: #64748B;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step.active .step-number {
  background: var(--color-cta);
  color: white;
}

.step.completed .step-number {
  background: #22C55E;
  color: white;
}

.step-label {
  font-size: 14px;
  color: #64748B;
}

.step.active .step-label {
  color: #0F172A;
  font-weight: 500;
}

.step-connector {
  flex: 1;
  height: 2px;
  background: #E2E8F0;
  margin: 0 16px;
}

.step.completed + .step-connector {
  background: #22C55E;
}
```

---

## Tables

```css
.table-wrapper {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  text-align: left;
  padding: 12px 16px;
  background: #F8FAFC;
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #E2E8F0;
}

.table td {
  padding: 16px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 14px;
  color: #0F172A;
}

.table tr:hover td {
  background: #F8FAFC;
}
```

---

## Icons (Lucide Recommended)

```html
<!-- Install: npm install lucide -->
<script src="https://unpkg.com/lucide@latest"></script>
<script>lucide.createIcons();</script>

<!-- Usage -->
<i data-lucide="message-circle"></i>
<i data-lucide="users"></i>
<i data-lucide="settings"></i>
<i data-lucide="bar-chart-2"></i>
```

**Recommended Icons:**
- Navigation: `menu`, `x`, `chevron-down`, `chevron-right`, `arrow-left`
- Actions: `plus`, `edit-2`, `trash-2`, `download`, `upload`, `search`
- Status: `check-circle`, `alert-circle`, `info`, `x-circle`
- Communication: `message-circle`, `send`, `mail`, `phone`
- Users: `user`, `users`, `user-plus`
- Settings: `settings`, `sliders`, `toggle-left`
- Charts: `bar-chart-2`, `trending-up`, `trending-down`, `pie-chart`
- Files: `file`, `folder`, `paperclip`, `image`
- AI: `sparkles`, `wand-2`, `brain`
