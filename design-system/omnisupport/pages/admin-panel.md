# Admin Panel Design Rules

> Applies to: `/settings/*`, `/team/*`, `/channels/*`, `/scenarios/*`, `/knowledge/*`, `/integrations/*`, `/branding/*`, `/billing/*`

---

## Layout Structure

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Top Bar (shared with Operator Panel)                                        │
├────────────┬─────────────────────────────────────────────────────────────────┤
│            │                                                                  │
│  Sidebar   │  ┌───────────────────────────────────────────────────────────┐  │
│  (w: 240px)│  │  Page Header                                              │  │
│            │  │  Title + Description + Actions                            │  │
│  Sections: │  ├───────────────────────────────────────────────────────────┤  │
│  • Settings│  │                                                           │  │
│  • Team    │  │  Content Area                                             │  │
│  • Channels│  │  (max-width: 1200px, centered)                           │  │
│  • Scenar. │  │                                                           │  │
│  • Knowled.│  │                                                           │  │
│  • Integr. │  │                                                           │  │
│  • Brand.  │  │                                                           │  │
│  • Billing │  │                                                           │  │
│            │  └───────────────────────────────────────────────────────────┘  │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## Admin Sidebar

```css
.admin-sidebar {
  width: 240px;
  background: white;
  border-right: 1px solid #E2E8F0;
  position: fixed;
  top: 56px;
  left: 0;
  bottom: 0;
  overflow-y: auto;
  z-index: 90;
}

.admin-sidebar-section {
  padding: 16px 0;
  border-bottom: 1px solid #F1F5F9;
}

.admin-sidebar-section:last-child {
  border-bottom: none;
}

.admin-sidebar-title {
  font-size: 11px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 16px;
  margin-bottom: 8px;
}

.admin-sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: #64748B;
  text-decoration: none;
  font-size: 14px;
  transition: all 200ms ease;
  cursor: pointer;
}

.admin-sidebar-item:hover {
  background: #F8FAFC;
  color: #0F172A;
}

.admin-sidebar-item.active {
  background: #EFF6FF;
  color: #0369A1;
  font-weight: 500;
}

.admin-sidebar-item svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.admin-sidebar-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: #FEE2E2;
  color: #DC2626;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

---

## Page Header

```css
.admin-page-header {
  padding: 32px 40px;
  background: white;
  border-bottom: 1px solid #E2E8F0;
}

.admin-page-header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.admin-page-title {
  font-size: 24px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 4px;
}

.admin-page-description {
  font-size: 14px;
  color: #64748B;
}

.admin-page-actions {
  display: flex;
  gap: 12px;
}
```

---

## Content Area

```css
.admin-content {
  margin-left: 240px;
  padding-top: 56px;
  min-height: 100vh;
  background: #F8FAFC;
}

.admin-content-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 40px;
}
```

---

## Settings Cards

```css
.settings-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  margin-bottom: 24px;
  overflow: hidden;
}

.settings-card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #F1F5F9;
}

.settings-card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 4px;
}

.settings-card-description {
  font-size: 13px;
  color: #64748B;
}

.settings-card-body {
  padding: 24px;
}

.settings-card-footer {
  padding: 16px 24px;
  background: #F8FAFC;
  border-top: 1px solid #F1F5F9;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Settings Row */
.settings-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid #F1F5F9;
}

.settings-row:last-child {
  border-bottom: none;
}

.settings-row-label {
  flex: 1;
}

.settings-row-title {
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
  margin-bottom: 2px;
}

.settings-row-description {
  font-size: 13px;
  color: #64748B;
}

.settings-row-control {
  flex-shrink: 0;
  margin-left: 24px;
}
```

---

## Form Elements

```css
/* Input Group */
.admin-input-group {
  margin-bottom: 20px;
}

.admin-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  margin-bottom: 6px;
}

.admin-label-optional {
  font-weight: 400;
  color: #94A3B8;
  margin-left: 4px;
}

.admin-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 200ms ease;
}

.admin-input:focus {
  border-color: #0369A1;
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}

.admin-input-hint {
  font-size: 12px;
  color: #64748B;
  margin-top: 4px;
}

/* Select */
.admin-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,...");
  background-repeat: no-repeat;
  background-position: right 12px center;
}

/* Toggle Switch */
.admin-toggle {
  position: relative;
  width: 48px;
  height: 24px;
  background: #E2E8F0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 200ms ease;
}

.admin-toggle.active {
  background: #0369A1;
}

.admin-toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: all 200ms ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.admin-toggle.active .admin-toggle-knob {
  transform: translateX(24px);
}

/* Textarea */
.admin-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px 14px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  transition: all 200ms ease;
}

.admin-textarea:focus {
  border-color: #0369A1;
  outline: none;
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}
```

---

## Data Tables

```css
.admin-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  overflow: hidden;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
}

.admin-table th {
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

.admin-table td {
  padding: 16px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 14px;
  color: #0F172A;
}

.admin-table tr:last-child td {
  border-bottom: none;
}

.admin-table tr:hover td {
  background: #F8FAFC;
}

.admin-table-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.admin-table-action {
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

.admin-table-action:hover {
  background: #F1F5F9;
  color: #0F172A;
}

.admin-table-action.danger:hover {
  background: #FEE2E2;
  color: #DC2626;
}
```

---

## Scenario Builder (No-Code Constructor)

```css
.scenario-canvas {
  background: #F1F5F9;
  background-image:
    radial-gradient(circle, #CBD5E1 1px, transparent 1px);
  background-size: 20px 20px;
  min-height: calc(100vh - 200px);
  position: relative;
  overflow: auto;
}

.scenario-toolbar {
  position: absolute;
  left: 16px;
  top: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 10;
}

.scenario-tool {
  width: 40px;
  height: 40px;
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

.scenario-tool:hover {
  background: #F1F5F9;
  color: #0F172A;
}

.scenario-tool.active {
  background: #EFF6FF;
  color: #0369A1;
}

/* Nodes */
.scenario-node {
  position: absolute;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  min-width: 200px;
  cursor: move;
}

.scenario-node-header {
  padding: 12px 16px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  align-items: center;
  gap: 8px;
}

.scenario-node-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scenario-node-icon.trigger {
  background: #DCFCE7;
  color: #166534;
}

.scenario-node-icon.message {
  background: #E0F2FE;
  color: #0369A1;
}

.scenario-node-icon.condition {
  background: #FEF3C7;
  color: #B45309;
}

.scenario-node-icon.action {
  background: #EDE9FE;
  color: #6D28D9;
}

.scenario-node-icon.ai {
  background: #FCE7F3;
  color: #BE185D;
}

.scenario-node-title {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
}

.scenario-node-body {
  padding: 12px 16px;
}

.scenario-node-preview {
  font-size: 13px;
  color: #64748B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Connection ports */
.scenario-port {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  border: 2px solid #0369A1;
  cursor: crosshair;
}

.scenario-port.input {
  top: 50%;
  left: -6px;
  transform: translateY(-50%);
}

.scenario-port.output {
  top: 50%;
  right: -6px;
  transform: translateY(-50%);
}

/* Connections */
.scenario-connection {
  stroke: #0369A1;
  stroke-width: 2;
  fill: none;
}

.scenario-connection:hover {
  stroke-width: 3;
}
```

---

## File Upload Zone

```css
.upload-zone {
  border: 2px dashed #E2E8F0;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  transition: all 200ms ease;
  cursor: pointer;
}

.upload-zone:hover {
  border-color: #0369A1;
  background: #EFF6FF;
}

.upload-zone.dragging {
  border-color: #0369A1;
  background: #DBEAFE;
}

.upload-zone-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #94A3B8;
}

.upload-zone-title {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 4px;
}

.upload-zone-description {
  font-size: 14px;
  color: #64748B;
}

.upload-zone-formats {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 12px;
}
```

---

## Empty States

```css
.admin-empty-state {
  text-align: center;
  padding: 64px 24px;
}

.admin-empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: #CBD5E1;
}

.admin-empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 8px;
}

.admin-empty-description {
  font-size: 14px;
  color: #64748B;
  margin-bottom: 24px;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}
```

---

## Integration Cards

```css
.integration-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.integration-card {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 24px;
  transition: all 200ms ease;
  cursor: pointer;
}

.integration-card:hover {
  border-color: #CBD5E1;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.integration-card.connected {
  border-color: #22C55E;
  background: #F0FDF4;
}

.integration-card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.integration-card-logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  object-fit: contain;
}

.integration-card-info {
  flex: 1;
}

.integration-card-name {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.integration-card-category {
  font-size: 12px;
  color: #64748B;
}

.integration-card-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.integration-card-status.connected {
  background: #DCFCE7;
  color: #166534;
}

.integration-card-status.available {
  background: #F1F5F9;
  color: #64748B;
}

.integration-card-description {
  font-size: 13px;
  color: #64748B;
  line-height: 1.5;
}
```

---

## Responsive Behavior

```css
@media (max-width: 1024px) {
  .admin-sidebar {
    width: 64px;
  }

  .admin-sidebar-title,
  .admin-sidebar-item span {
    display: none;
  }

  .admin-sidebar-item {
    justify-content: center;
    padding: 12px;
  }

  .admin-content {
    margin-left: 64px;
  }

  .admin-content-inner {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .admin-sidebar {
    display: none;
  }

  .admin-content {
    margin-left: 0;
  }

  .admin-page-header-content {
    flex-direction: column;
    gap: 16px;
  }

  .admin-page-actions {
    width: 100%;
  }

  .admin-page-actions .btn {
    flex: 1;
  }
}
```
