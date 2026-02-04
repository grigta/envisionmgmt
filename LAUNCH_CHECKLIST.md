# 🚀 LAUNCH CHECKLIST — OmniSupport

*Критерии готовности к запуску MVP*
*Обновлено: 2026-02-03 by Clawd*

---

## 📦 Product

- [x] Core Features
  - [x] Chat widget встраивается одной строкой
  - [x] AI отвечает на вопросы (Claude, OpenAI, YandexGPT, GigaChat)
  - [x] История чатов сохраняется
  - [x] Работает на mobile

- [ ] Quality
  - [ ] Нет critical багов
  - [ ] Время ответа < 3 сек
  - [ ] Uptime > 99%

- [x] UX
  - [x] Widget не мешает сайту
  - [x] Понятно как закрыть чат
  - [x] Есть индикатор "печатает..."

---

## 📚 Documentation

- [x] README понятен новому пользователю
- [x] Quick Start Guide (5 минут до первого чата)
- [x] API документация (16 разделов, примеры)
- [x] Примеры интеграции (HTML, React, Vue, Next.js)
- [ ] FAQ

---

## 💼 Business

- [x] Landing Page
  - [x] Понятный value proposition
  - [x] Pricing таблица
  - [x] CTA "Попробовать бесплатно"
  
- [x] Pricing определён
  - [x] Free tier (100 сообщений/мес)
  - [x] Pro tier ($29/мес)
  - [x] Enterprise (custom)

- [x] Legal
  - [x] Terms of Service
  - [x] Privacy Policy
  - [x] GDPR compliance

---

## 🔧 Technical

- [ ] Infrastructure
  - [ ] Production сервер
  - [ ] SSL сертификат
  - [ ] CDN для widget.js

- [ ] DevOps
  - [ ] CI/CD настроен
  - [ ] Мониторинг (uptime, errors)
  - [ ] Алерты в Telegram

- [x] Security
  - [x] API keys не в коде (.env)
  - [x] Rate limiting
  - [x] Input validation

- [ ] Backup
  - [ ] DB backup автоматический
  - [ ] Recovery протестирован

---

## 📊 Launch Readiness Score

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Product | 40% | 75% | 30% |
| Docs | 15% | 90% | 13.5% |
| Business | 25% | 100% | 25% |
| Technical | 20% | 35% | 7% |
| **TOTAL** | 100% | — | **75.5%** |

**Status**: 🟡 Almost ready — need infrastructure

**Blockers for launch**:
1. 🔴 Production сервер (deploy backend + widget)
2. 🔴 SSL + домен
3. 🟡 Quality testing
4. 🟡 Backup setup

**Estimated time to launch**: 1 week (with infra)

---

## 🎯 Next Steps

1. **Deploy backend** to VPS/Cloud (Yandex Cloud, DigitalOcean)
2. **Setup domain** omnisupport.attention.dev
3. **Configure SSL** (Let's Encrypt)
4. **CDN for widget.js** (Cloudflare)
5. **Smoke test** all flows
6. **Soft launch** to 3-5 beta users

---

*Last updated: 2026-02-03 by Clawd*
