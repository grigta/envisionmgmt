# Auth Pages Design Rules

> Applies to: `/login`, `/signup`, `/forgot-password`, `/reset-password/:token`, `/verify-email/:token`, `/invite/:token`, `/two-factor`

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌─────────────────────┐  ┌─────────────────────────────┐  │
│   │                     │  │                             │  │
│   │   Brand Panel       │  │      Form Panel             │  │
│   │   (Left 40%)        │  │      (Right 60%)            │  │
│   │                     │  │                             │  │
│   │   • Logo            │  │   • Page Title              │  │
│   │   • Tagline         │  │   • Form Fields             │  │
│   │   • Trust badges    │  │   • Primary CTA             │  │
│   │   • Testimonial     │  │   • Secondary links         │  │
│   │                     │  │                             │  │
│   └─────────────────────┘  └─────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Mobile:** Stack vertically, Brand Panel becomes compact header.

---

## Brand Panel

```css
.auth-brand-panel {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  min-height: 100vh;
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.auth-logo {
  width: 48px;
  height: 48px;
  margin-bottom: 32px;
}

.auth-tagline {
  font-size: 32px;
  font-weight: 700;
  color: white;
  line-height: 1.2;
  margin-bottom: 16px;
}

.auth-subtitle {
  font-size: 16px;
  color: #94A3B8;
  margin-bottom: 48px;
}

.auth-testimonial {
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 24px;
  margin-top: auto;
}

.auth-testimonial-text {
  font-size: 14px;
  color: #E2E8F0;
  font-style: italic;
  margin-bottom: 16px;
}

.auth-testimonial-author {
  display: flex;
  align-items: center;
  gap: 12px;
}

.auth-testimonial-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.auth-testimonial-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.auth-testimonial-role {
  font-size: 12px;
  color: #94A3B8;
}
```

---

## Form Panel

```css
.auth-form-panel {
  background: #F8FAFC;
  min-height: 100vh;
  padding: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-form-container {
  width: 100%;
  max-width: 400px;
}

.auth-form-title {
  font-size: 24px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 8px;
}

.auth-form-subtitle {
  font-size: 14px;
  color: #64748B;
  margin-bottom: 32px;
}
```

---

## Form Fields

```css
.auth-field {
  margin-bottom: 20px;
}

.auth-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  margin-bottom: 6px;
}

.auth-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: all 200ms ease;
  background: white;
}

.auth-input:focus {
  border-color: #0369A1;
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}

.auth-input-error {
  border-color: #DC2626;
}

.auth-error-message {
  font-size: 12px;
  color: #DC2626;
  margin-top: 4px;
}

/* Password field with toggle */
.auth-password-wrapper {
  position: relative;
}

.auth-password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748B;
  cursor: pointer;
}
```

---

## Buttons

```css
.auth-btn-primary {
  width: 100%;
  padding: 14px 24px;
  background: #0369A1;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
}

.auth-btn-primary:hover {
  background: #0284C7;
  transform: translateY(-1px);
}

.auth-btn-primary:disabled {
  background: #94A3B8;
  cursor: not-allowed;
  transform: none;
}

.auth-btn-secondary {
  width: 100%;
  padding: 14px 24px;
  background: white;
  color: #0F172A;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.auth-btn-secondary:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}
```

---

## Social Login

```css
.auth-divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
}

.auth-divider-line {
  flex: 1;
  height: 1px;
  background: #E2E8F0;
}

.auth-divider-text {
  padding: 0 16px;
  font-size: 12px;
  color: #94A3B8;
  text-transform: uppercase;
}

.auth-social-buttons {
  display: flex;
  gap: 12px;
}

.auth-social-btn {
  flex: 1;
  padding: 12px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-social-btn:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}
```

---

## Links

```css
.auth-link {
  color: #0369A1;
  text-decoration: none;
  font-size: 14px;
  transition: color 200ms ease;
}

.auth-link:hover {
  color: #0284C7;
  text-decoration: underline;
}

.auth-footer-text {
  text-align: center;
  font-size: 14px;
  color: #64748B;
  margin-top: 24px;
}
```

---

## 2FA Page Specific

```css
.auth-2fa-inputs {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 24px;
}

.auth-2fa-input {
  width: 48px;
  height: 56px;
  text-align: center;
  font-size: 24px;
  font-weight: 600;
  border: 2px solid #E2E8F0;
  border-radius: 8px;
  transition: all 200ms ease;
}

.auth-2fa-input:focus {
  border-color: #0369A1;
  outline: none;
}

.auth-resend-code {
  text-align: center;
  font-size: 14px;
  color: #64748B;
}

.auth-resend-timer {
  color: #0369A1;
  font-weight: 500;
}
```

---

## Trust Badges (Brand Panel)

```css
.auth-trust-badges {
  display: flex;
  gap: 24px;
  margin-top: 32px;
}

.auth-trust-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94A3B8;
  font-size: 12px;
}

.auth-trust-badge svg {
  width: 16px;
  height: 16px;
  color: #22C55E;
}
```

---

## Page-Specific Content

| Page | Title | Subtitle |
|------|-------|----------|
| `/login` | Войдите в аккаунт | Рады видеть вас снова |
| `/signup` | Создайте аккаунт | Начните бесплатный 14-дневный пробный период |
| `/forgot-password` | Забыли пароль? | Введите email для восстановления |
| `/reset-password` | Новый пароль | Создайте надёжный пароль |
| `/verify-email` | Подтвердите email | Проверьте почту для завершения регистрации |
| `/invite/:token` | Присоединяйтесь к команде | Вас пригласили в [Company Name] |
| `/two-factor` | Двухфакторная аутентификация | Введите код из приложения |

---

## Responsive

```css
@media (max-width: 1024px) {
  .auth-layout {
    flex-direction: column;
  }

  .auth-brand-panel {
    min-height: auto;
    padding: 32px;
  }

  .auth-testimonial {
    display: none;
  }

  .auth-form-panel {
    min-height: auto;
    padding: 32px;
  }
}

@media (max-width: 640px) {
  .auth-brand-panel {
    padding: 24px;
  }

  .auth-tagline {
    font-size: 24px;
  }

  .auth-form-panel {
    padding: 24px;
  }
}
```
