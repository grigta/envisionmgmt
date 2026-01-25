# Public/Marketing Pages Design Rules

> Applies to: `/`, `/features`, `/pricing`, `/cases`, `/about`, `/contact`, `/blog`, `/blog/:slug`, `/docs/*`, `/privacy`, `/terms`, `/sla`

---

## Common Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Navigation (sticky, transparent → white on scroll)                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Page Content (max-width: 1280px, centered)                                  │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  Footer                                                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Navigation

```css
.marketing-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 16px 40px;
  transition: all 300ms ease;
}

.marketing-nav.transparent {
  background: transparent;
}

.marketing-nav.solid {
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.marketing-nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.marketing-nav-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.marketing-nav-logo-icon {
  width: 36px;
  height: 36px;
}

.marketing-nav-logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
}

.marketing-nav-links {
  display: flex;
  align-items: center;
  gap: 32px;
}

.marketing-nav-link {
  font-size: 15px;
  font-weight: 500;
  color: #334155;
  text-decoration: none;
  transition: color 200ms ease;
  position: relative;
}

.marketing-nav-link:hover {
  color: #0369A1;
}

.marketing-nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: #0369A1;
  transition: width 200ms ease;
}

.marketing-nav-link:hover::after {
  width: 100%;
}

.marketing-nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Mobile menu */
.marketing-nav-mobile-toggle {
  display: none;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  cursor: pointer;
}

@media (max-width: 1024px) {
  .marketing-nav-links {
    display: none;
  }

  .marketing-nav-mobile-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
```

---

## Hero Section

```css
.marketing-hero {
  padding: 160px 40px 80px;
  background: linear-gradient(180deg, #F8FAFC 0%, white 100%);
}

.marketing-hero-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
}

.marketing-hero-content {
  max-width: 560px;
}

.marketing-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #EFF6FF;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #0369A1;
  margin-bottom: 24px;
}

.marketing-hero-title {
  font-size: 56px;
  font-weight: 800;
  color: #0F172A;
  line-height: 1.1;
  margin-bottom: 24px;
  letter-spacing: -0.02em;
}

.marketing-hero-title span {
  background: linear-gradient(135deg, #0369A1 0%, #0EA5E9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.marketing-hero-description {
  font-size: 18px;
  color: #64748B;
  line-height: 1.6;
  margin-bottom: 32px;
}

.marketing-hero-actions {
  display: flex;
  gap: 16px;
}

.marketing-hero-image {
  position: relative;
}

.marketing-hero-image img {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.15);
}

/* Trust indicators */
.marketing-hero-trust {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 48px;
  padding-top: 32px;
  border-top: 1px solid #E2E8F0;
}

.marketing-hero-trust-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748B;
}

.marketing-hero-trust-item svg {
  width: 20px;
  height: 20px;
  color: #22C55E;
}

@media (max-width: 1024px) {
  .marketing-hero-inner {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .marketing-hero-content {
    max-width: 100%;
  }

  .marketing-hero-title {
    font-size: 40px;
  }

  .marketing-hero-actions {
    justify-content: center;
  }

  .marketing-hero-trust {
    justify-content: center;
  }
}
```

---

## Section Spacing

```css
.marketing-section {
  padding: 96px 40px;
}

.marketing-section-inner {
  max-width: 1280px;
  margin: 0 auto;
}

.marketing-section.alt {
  background: #F8FAFC;
}

.marketing-section-header {
  text-align: center;
  max-width: 720px;
  margin: 0 auto 64px;
}

.marketing-section-label {
  font-size: 13px;
  font-weight: 600;
  color: #0369A1;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.marketing-section-title {
  font-size: 40px;
  font-weight: 700;
  color: #0F172A;
  line-height: 1.2;
  margin-bottom: 16px;
}

.marketing-section-description {
  font-size: 18px;
  color: #64748B;
  line-height: 1.6;
}
```

---

## Feature Cards

```css
.marketing-features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
}

.marketing-feature-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  border: 1px solid #E2E8F0;
  transition: all 300ms ease;
  cursor: default;
}

.marketing-feature-card:hover {
  border-color: #CBD5E1;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
  transform: translateY(-4px);
}

.marketing-feature-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.marketing-feature-icon svg {
  width: 28px;
  height: 28px;
  color: #0369A1;
}

.marketing-feature-title {
  font-size: 20px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 12px;
}

.marketing-feature-description {
  font-size: 15px;
  color: #64748B;
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .marketing-features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .marketing-features-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## Pricing Cards

```css
.marketing-pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  align-items: start;
}

.marketing-pricing-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  border: 2px solid #E2E8F0;
  position: relative;
  transition: all 300ms ease;
}

.marketing-pricing-card:hover {
  border-color: #CBD5E1;
}

.marketing-pricing-card.popular {
  border-color: #0369A1;
  transform: scale(1.05);
  box-shadow: 0 25px 50px -12px rgba(3, 105, 161, 0.2);
}

.marketing-pricing-badge {
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 16px;
  background: #0369A1;
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.marketing-pricing-name {
  font-size: 20px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 8px;
}

.marketing-pricing-description {
  font-size: 14px;
  color: #64748B;
  margin-bottom: 24px;
}

.marketing-pricing-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 24px;
}

.marketing-pricing-currency {
  font-size: 24px;
  font-weight: 600;
  color: #0F172A;
}

.marketing-pricing-amount {
  font-size: 56px;
  font-weight: 800;
  color: #0F172A;
  line-height: 1;
}

.marketing-pricing-period {
  font-size: 16px;
  color: #64748B;
}

.marketing-pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 32px;
}

.marketing-pricing-feature {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  font-size: 14px;
  color: #334155;
}

.marketing-pricing-feature svg {
  width: 20px;
  height: 20px;
  color: #22C55E;
  flex-shrink: 0;
  margin-top: 1px;
}

.marketing-pricing-feature.disabled {
  color: #94A3B8;
}

.marketing-pricing-feature.disabled svg {
  color: #CBD5E1;
}

@media (max-width: 1024px) {
  .marketing-pricing-grid {
    grid-template-columns: 1fr;
    max-width: 400px;
    margin: 0 auto;
  }

  .marketing-pricing-card.popular {
    transform: none;
    order: -1;
  }
}
```

---

## Testimonials / Case Studies

```css
.marketing-testimonials-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
}

.marketing-testimonial-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  border: 1px solid #E2E8F0;
  transition: all 300ms ease;
}

.marketing-testimonial-card:hover {
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
}

.marketing-testimonial-quote {
  font-size: 18px;
  color: #334155;
  line-height: 1.6;
  margin-bottom: 24px;
  font-style: italic;
}

.marketing-testimonial-metrics {
  display: flex;
  gap: 32px;
  padding: 20px 0;
  border-top: 1px solid #F1F5F9;
  border-bottom: 1px solid #F1F5F9;
  margin-bottom: 24px;
}

.marketing-testimonial-metric {
  text-align: center;
}

.marketing-testimonial-metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #0369A1;
}

.marketing-testimonial-metric-label {
  font-size: 12px;
  color: #64748B;
  text-transform: uppercase;
}

.marketing-testimonial-author {
  display: flex;
  align-items: center;
  gap: 16px;
}

.marketing-testimonial-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
}

.marketing-testimonial-name {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.marketing-testimonial-role {
  font-size: 14px;
  color: #64748B;
}

.marketing-testimonial-company {
  height: 24px;
  margin-left: auto;
  opacity: 0.5;
}
```

---

## FAQ Section

```css
.marketing-faq-list {
  max-width: 800px;
  margin: 0 auto;
}

.marketing-faq-item {
  border-bottom: 1px solid #E2E8F0;
}

.marketing-faq-question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 0;
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
  cursor: pointer;
  transition: color 200ms ease;
}

.marketing-faq-question:hover {
  color: #0369A1;
}

.marketing-faq-icon {
  width: 24px;
  height: 24px;
  color: #64748B;
  transition: transform 200ms ease;
}

.marketing-faq-item.open .marketing-faq-icon {
  transform: rotate(180deg);
}

.marketing-faq-answer {
  padding-bottom: 24px;
  font-size: 16px;
  color: #64748B;
  line-height: 1.6;
  display: none;
}

.marketing-faq-item.open .marketing-faq-answer {
  display: block;
}
```

---

## CTA Section

```css
.marketing-cta {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  padding: 96px 40px;
  text-align: center;
}

.marketing-cta-inner {
  max-width: 720px;
  margin: 0 auto;
}

.marketing-cta-title {
  font-size: 40px;
  font-weight: 700;
  color: white;
  margin-bottom: 16px;
}

.marketing-cta-description {
  font-size: 18px;
  color: #94A3B8;
  margin-bottom: 32px;
}

.marketing-cta-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
```

---

## Footer

```css
.marketing-footer {
  background: #0F172A;
  padding: 80px 40px 32px;
}

.marketing-footer-inner {
  max-width: 1280px;
  margin: 0 auto;
}

.marketing-footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 64px;
  margin-bottom: 64px;
}

.marketing-footer-brand {
  max-width: 280px;
}

.marketing-footer-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.marketing-footer-logo-text {
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.marketing-footer-description {
  font-size: 14px;
  color: #94A3B8;
  line-height: 1.6;
  margin-bottom: 24px;
}

.marketing-footer-social {
  display: flex;
  gap: 12px;
}

.marketing-footer-social-link {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  transition: all 200ms ease;
}

.marketing-footer-social-link:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.marketing-footer-column-title {
  font-size: 14px;
  font-weight: 600;
  color: white;
  margin-bottom: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.marketing-footer-links {
  list-style: none;
  padding: 0;
  margin: 0;
}

.marketing-footer-link {
  margin-bottom: 12px;
}

.marketing-footer-link a {
  font-size: 14px;
  color: #94A3B8;
  text-decoration: none;
  transition: color 200ms ease;
}

.marketing-footer-link a:hover {
  color: white;
}

.marketing-footer-bottom {
  padding-top: 32px;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.marketing-footer-copyright {
  font-size: 14px;
  color: #64748B;
}

.marketing-footer-legal {
  display: flex;
  gap: 24px;
}

.marketing-footer-legal a {
  font-size: 14px;
  color: #64748B;
  text-decoration: none;
  transition: color 200ms ease;
}

.marketing-footer-legal a:hover {
  color: white;
}

@media (max-width: 1024px) {
  .marketing-footer-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .marketing-footer-brand {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .marketing-footer-grid {
    grid-template-columns: 1fr;
  }

  .marketing-footer-brand {
    grid-column: span 1;
  }

  .marketing-footer-bottom {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
}
```

---

## Blog Layout

```css
.marketing-blog-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
}

.marketing-blog-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #E2E8F0;
  transition: all 300ms ease;
}

.marketing-blog-card:hover {
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
  transform: translateY(-4px);
}

.marketing-blog-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.marketing-blog-content {
  padding: 24px;
}

.marketing-blog-category {
  font-size: 12px;
  font-weight: 600;
  color: #0369A1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.marketing-blog-title {
  font-size: 20px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 12px;
  line-height: 1.3;
}

.marketing-blog-excerpt {
  font-size: 14px;
  color: #64748B;
  line-height: 1.6;
  margin-bottom: 16px;
}

.marketing-blog-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #94A3B8;
}

/* Blog article page */
.marketing-article {
  max-width: 720px;
  margin: 0 auto;
  padding: 120px 40px 80px;
}

.marketing-article-header {
  text-align: center;
  margin-bottom: 48px;
}

.marketing-article-title {
  font-size: 40px;
  font-weight: 700;
  color: #0F172A;
  line-height: 1.2;
  margin-bottom: 24px;
}

.marketing-article-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  font-size: 14px;
  color: #64748B;
}

.marketing-article-content {
  font-size: 18px;
  color: #334155;
  line-height: 1.8;
}

.marketing-article-content h2 {
  font-size: 28px;
  font-weight: 700;
  color: #0F172A;
  margin-top: 48px;
  margin-bottom: 24px;
}

.marketing-article-content h3 {
  font-size: 22px;
  font-weight: 600;
  color: #0F172A;
  margin-top: 32px;
  margin-bottom: 16px;
}

.marketing-article-content p {
  margin-bottom: 24px;
}

.marketing-article-content img {
  width: 100%;
  border-radius: 12px;
  margin: 32px 0;
}

.marketing-article-content blockquote {
  border-left: 4px solid #0369A1;
  padding-left: 24px;
  margin: 32px 0;
  font-style: italic;
  color: #64748B;
}
```

---

## Documentation Layout

```css
.marketing-docs {
  display: grid;
  grid-template-columns: 280px 1fr 200px;
  gap: 40px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 96px 40px;
}

.marketing-docs-sidebar {
  position: sticky;
  top: 96px;
  height: fit-content;
}

.marketing-docs-nav-section {
  margin-bottom: 24px;
}

.marketing-docs-nav-title {
  font-size: 12px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.marketing-docs-nav-link {
  display: block;
  padding: 8px 12px;
  font-size: 14px;
  color: #64748B;
  text-decoration: none;
  border-radius: 6px;
  transition: all 200ms ease;
}

.marketing-docs-nav-link:hover {
  color: #0F172A;
  background: #F8FAFC;
}

.marketing-docs-nav-link.active {
  color: #0369A1;
  background: #EFF6FF;
  font-weight: 500;
}

.marketing-docs-content {
  min-width: 0;
}

.marketing-docs-toc {
  position: sticky;
  top: 96px;
  height: fit-content;
}

.marketing-docs-toc-title {
  font-size: 12px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.marketing-docs-toc-link {
  display: block;
  padding: 6px 0;
  font-size: 13px;
  color: #64748B;
  text-decoration: none;
  transition: color 200ms ease;
  border-left: 2px solid transparent;
  padding-left: 12px;
  margin-left: -2px;
}

.marketing-docs-toc-link:hover {
  color: #0F172A;
}

.marketing-docs-toc-link.active {
  color: #0369A1;
  border-left-color: #0369A1;
}

@media (max-width: 1200px) {
  .marketing-docs {
    grid-template-columns: 240px 1fr;
  }

  .marketing-docs-toc {
    display: none;
  }
}

@media (max-width: 768px) {
  .marketing-docs {
    grid-template-columns: 1fr;
  }

  .marketing-docs-sidebar {
    position: static;
  }
}
```

---

## Trust & Authority Elements

```css
/* Security badges */
.marketing-trust-badges {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 32px 0;
}

.marketing-trust-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.marketing-trust-badge-icon {
  width: 32px;
  height: 32px;
}

.marketing-trust-badge-text {
  font-size: 13px;
  font-weight: 500;
  color: #334155;
}

/* Stat counters */
.marketing-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  text-align: center;
}

.marketing-stat {
  padding: 32px;
}

.marketing-stat-value {
  font-size: 48px;
  font-weight: 800;
  color: #0F172A;
  margin-bottom: 8px;
}

.marketing-stat-label {
  font-size: 14px;
  color: #64748B;
}

/* Logo cloud */
.marketing-logos {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
  padding: 48px 0;
}

.marketing-logo {
  height: 32px;
  opacity: 0.4;
  transition: opacity 200ms ease;
}

.marketing-logo:hover {
  opacity: 1;
}
```
