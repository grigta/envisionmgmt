# Analytics Pages Design Rules

> Applies to: `/analytics`, `/analytics/conversations`, `/analytics/operators`, `/analytics/channels`, `/analytics/csat`, `/analytics/ai`, `/analytics/tags`, `/reports/*`

---

## Layout Structure

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Page Header with Date Range Picker                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  KPI 1   │ │  KPI 2   │ │  KPI 3   │ │  KPI 4   │ │  KPI 5   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────┐ ┌───────────────────────────────┐  │
│  │                                     │ │                               │  │
│  │  Primary Chart (60%)                │ │  Secondary Chart (40%)        │  │
│  │                                     │ │                               │  │
│  └─────────────────────────────────────┘ └───────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────┐ ┌───────────────────────────────┐  │
│  │                                     │ │                               │  │
│  │  Data Table                         │ │  Leaderboard / Rankings       │  │
│  │                                     │ │                               │  │
│  └─────────────────────────────────────┘ └───────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Date Range Picker

```css
.analytics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.analytics-date-picker {
  display: flex;
  align-items: center;
  gap: 12px;
}

.analytics-preset-btns {
  display: flex;
  gap: 4px;
  background: #F1F5F9;
  padding: 4px;
  border-radius: 8px;
}

.analytics-preset-btn {
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
  transition: all 200ms ease;
}

.analytics-preset-btn:hover {
  color: #0F172A;
}

.analytics-preset-btn.active {
  background: white;
  color: #0F172A;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.analytics-custom-range {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
}

.analytics-custom-range:hover {
  border-color: #CBD5E1;
}

.analytics-custom-range svg {
  width: 16px;
  height: 16px;
  color: #64748B;
}

.analytics-custom-range span {
  font-size: 13px;
  color: #0F172A;
}
```

---

## KPI Cards

```css
.analytics-kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.analytics-kpi-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.analytics-kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.analytics-kpi-card.positive::before {
  background: #22C55E;
}

.analytics-kpi-card.negative::before {
  background: #EF4444;
}

.analytics-kpi-card.neutral::before {
  background: #0369A1;
}

.analytics-kpi-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.analytics-kpi-label svg {
  width: 14px;
  height: 14px;
}

.analytics-kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 8px;
  line-height: 1;
}

.analytics-kpi-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.analytics-kpi-change.positive {
  color: #22C55E;
}

.analytics-kpi-change.negative {
  color: #EF4444;
}

.analytics-kpi-change svg {
  width: 12px;
  height: 12px;
}

.analytics-kpi-sparkline {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  opacity: 0.1;
}

@media (max-width: 1280px) {
  .analytics-kpi-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .analytics-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

---

## Chart Cards

```css
.analytics-chart-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
  margin-bottom: 24px;
}

.analytics-chart-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  padding: 24px;
}

.analytics-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.analytics-chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.analytics-chart-actions {
  display: flex;
  gap: 8px;
}

.analytics-chart-toggle {
  display: flex;
  gap: 4px;
  background: #F1F5F9;
  padding: 2px;
  border-radius: 6px;
}

.analytics-chart-toggle-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
  transition: all 200ms ease;
}

.analytics-chart-toggle-btn.active {
  background: white;
  color: #0F172A;
}

.analytics-chart-container {
  height: 300px;
  position: relative;
}

/* Chart legend */
.analytics-chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #F1F5F9;
}

.analytics-legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748B;
}

.analytics-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
```

---

## Chart Color Palette

```css
:root {
  /* Primary series */
  --chart-1: #0369A1;
  --chart-2: #0891B2;
  --chart-3: #06B6D4;
  --chart-4: #22D3EE;

  /* Secondary series */
  --chart-5: #6366F1;
  --chart-6: #8B5CF6;
  --chart-7: #A855F7;

  /* Status colors */
  --chart-success: #22C55E;
  --chart-warning: #F59E0B;
  --chart-error: #EF4444;

  /* Neutral */
  --chart-gray: #94A3B8;
}
```

---

## Chart Types & Recommendations

| Page | Primary Chart | Secondary Chart |
|------|--------------|-----------------|
| `/analytics` | Area (Conversations over time) | Donut (By Channel) |
| `/analytics/conversations` | Stacked Bar (Volume by status) | Line (Response time trend) |
| `/analytics/operators` | Horizontal Bar (Leaderboard) | Radar (Skills comparison) |
| `/analytics/channels` | Multi-line (Channel comparison) | Pie (Distribution) |
| `/analytics/csat` | Line (CSAT trend) | Bar (By category) |
| `/analytics/ai` | Area (AI suggestions used) | Donut (Acceptance rate) |
| `/analytics/tags` | Treemap (Tag distribution) | Bar (Top 10 tags) |

---

## Data Tables

```css
.analytics-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  overflow: hidden;
}

.analytics-table-header {
  padding: 16px 20px;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.analytics-table-title {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.analytics-table-search {
  width: 240px;
  padding: 8px 12px 8px 36px;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 13px;
}

.analytics-table {
  width: 100%;
  border-collapse: collapse;
}

.analytics-table th {
  text-align: left;
  padding: 12px 20px;
  background: #F8FAFC;
  font-size: 11px;
  font-weight: 600;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #E2E8F0;
  position: sticky;
  top: 0;
}

.analytics-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.analytics-table th.sortable:hover {
  color: #0F172A;
}

.analytics-table th .sort-icon {
  margin-left: 4px;
  opacity: 0.3;
}

.analytics-table th.sorted .sort-icon {
  opacity: 1;
  color: #0369A1;
}

.analytics-table td {
  padding: 16px 20px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 14px;
  color: #0F172A;
}

.analytics-table tr:hover td {
  background: #F8FAFC;
}

/* Inline sparkline in table */
.analytics-table-sparkline {
  width: 80px;
  height: 24px;
}

/* Mini bar in table */
.analytics-table-bar {
  width: 100px;
  height: 6px;
  background: #E2E8F0;
  border-radius: 3px;
  overflow: hidden;
}

.analytics-table-bar-fill {
  height: 100%;
  background: #0369A1;
  border-radius: 3px;
}

/* Pagination */
.analytics-table-pagination {
  padding: 12px 20px;
  border-top: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.analytics-pagination-info {
  font-size: 13px;
  color: #64748B;
}

.analytics-pagination-controls {
  display: flex;
  gap: 4px;
}

.analytics-pagination-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid #E2E8F0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #64748B;
  transition: all 200ms ease;
}

.analytics-pagination-btn:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}

.analytics-pagination-btn.active {
  background: #0369A1;
  border-color: #0369A1;
  color: white;
}
```

---

## Leaderboard

```css
.analytics-leaderboard {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
}

.analytics-leaderboard-header {
  padding: 20px;
  border-bottom: 1px solid #E2E8F0;
}

.analytics-leaderboard-title {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.analytics-leaderboard-list {
  padding: 12px 0;
}

.analytics-leaderboard-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  gap: 16px;
  transition: background 200ms ease;
}

.analytics-leaderboard-item:hover {
  background: #F8FAFC;
}

.analytics-leaderboard-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.analytics-leaderboard-rank.gold {
  background: #FEF3C7;
  color: #B45309;
}

.analytics-leaderboard-rank.silver {
  background: #F1F5F9;
  color: #475569;
}

.analytics-leaderboard-rank.bronze {
  background: #FED7AA;
  color: #C2410C;
}

.analytics-leaderboard-rank.default {
  background: #F1F5F9;
  color: #94A3B8;
}

.analytics-leaderboard-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #E2E8F0;
  flex-shrink: 0;
}

.analytics-leaderboard-info {
  flex: 1;
  min-width: 0;
}

.analytics-leaderboard-name {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.analytics-leaderboard-meta {
  font-size: 12px;
  color: #64748B;
}

.analytics-leaderboard-score {
  font-size: 18px;
  font-weight: 700;
  color: #0F172A;
  flex-shrink: 0;
}

.analytics-leaderboard-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  flex-shrink: 0;
}

.analytics-leaderboard-trend.up {
  color: #22C55E;
}

.analytics-leaderboard-trend.down {
  color: #EF4444;
}
```

---

## Export Options

```css
.analytics-export-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
  border: 1px solid #E2E8F0;
  min-width: 180px;
  z-index: 50;
}

.analytics-export-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  font-size: 14px;
  color: #0F172A;
  cursor: pointer;
  transition: all 200ms ease;
}

.analytics-export-item:hover {
  background: #F8FAFC;
}

.analytics-export-item svg {
  width: 18px;
  height: 18px;
  color: #64748B;
}
```

---

## Loading States

```css
.analytics-skeleton {
  background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.analytics-skeleton-kpi {
  height: 120px;
}

.analytics-skeleton-chart {
  height: 300px;
}

.analytics-skeleton-row {
  height: 48px;
  margin-bottom: 8px;
}
```

---

## Metric Pulse Animation

```css
.analytics-kpi-value.pulse {
  animation: metric-pulse 2s ease-in-out;
}

@keyframes metric-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* Counter animation */
.analytics-kpi-value[data-animate] {
  transition: all 0.5s ease-out;
}
```

---

## Responsive

```css
@media (max-width: 1280px) {
  .analytics-chart-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analytics-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .analytics-date-picker {
    flex-direction: column;
    gap: 8px;
  }

  .analytics-preset-btns {
    overflow-x: auto;
  }

  .analytics-kpi-grid {
    grid-template-columns: 1fr;
  }

  .analytics-table {
    display: block;
    overflow-x: auto;
  }
}
```
