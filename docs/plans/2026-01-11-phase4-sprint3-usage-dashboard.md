# Phase 4 Sprint 3: Usage Dashboard & Cost Analytics - Design Document

**Date**: 2026-01-11
**Status**: Design Complete, Ready for Implementation
**Target Release**: v0.5.0

---

## Executive Summary

Complete Phase 4 by adding comprehensive AI usage tracking dashboard with cost visualization, budget management, and data export capabilities. This provides full transparency into AI costs and helps users manage spending through monthly budgets and automated alerts.

**Design Philosophy**: Simple, fast, informative. Users should understand their AI costs at a glance and be alerted before overspending.

---

## Architecture

### Component Structure

```
UsageDashboardView (new view, 4th tab in AI Hub)
├── MetricsCards (4 cards: Total Cost, API Calls, Tokens, Budget %)
├── TimeRangeSelector (Last 7d, 30d, This month, Last month)
├── CostTrendChart (simple bar chart showing costs)
├── ProviderBreakdown (horizontal bars per provider)
├── WorkflowBreakdown (sortable table)
├── BudgetSettingsPanel (modal dialog)
└── CSVExportButton (dropdown menu)
```

### Data Flow

1. **View Load**: Fetch current month data via `AIStorage.get_usage_stats()`
2. **Time Range Change**: Re-fetch with new date range
3. **All charts update from same dataset** (single query per range)
4. **Budget data**: Fetched separately via `AIStorage.get_budget_settings()`

### Storage Methods Used

All methods already implemented in `src/ai/storage.py`:

- `get_usage_stats(start_date, end_date)` → Aggregate metrics
- `get_cost_by_provider(month, year)` → Provider breakdown
- `get_cost_by_workflow(month, year)` → Workflow costs
- `get_budget_settings()` → Monthly limit and threshold
- `update_budget_settings(settings)` → Save budget config

---

## UI Design

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Usage Dashboard Header]                                │
│ Time Range: [Last 7d] [Last 30d] [This Month*] [Last M] │
├─────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │ $12.45  │ │  247    │ │  125K   │ │  41%    │        │
│ │ Cost    │ │ Calls   │ │ Tokens  │ │ Budget  │        │
│ │ ▲ +15%  │ │ ▼ -8%   │ │ ▲ +12%  │ │ [bar]   │        │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────────┤
│ Cost by Provider                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ OpenAI    ████████████████░░░░░ $8.20 (66%)        │ │
│ │ Anthropic ██████░░░░░░░░░░░░░░ $3.50 (28%)        │ │
│ │ Local     █░░░░░░░░░░░░░░░░░░░ $0.00 (0%)         │ │
│ │ Groq      █░░░░░░░░░░░░░░░░░░░ $0.75 (6%)         │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Top Workflows by Cost                    [Export CSV ▼] │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Workflow Name           Cost    Calls   Tokens      │ │
│ │ ───────────────────────────────────────────────── │ │
│ │ Data Processing        $6.50     120     65K       │ │
│ │ Report Generator       $3.20      45     28K       │ │
│ │ Customer Analysis      $2.75      82     32K       │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Metric Cards (4 cards in Row)

**Layout**: Container → Column → [Large number, Label, Delta]

- **Large number**: 28px bold, Theme.TEXT_PRIMARY
- **Label**: 12px, Theme.TEXT_SECONDARY
- **Delta indicator**: ↑ +15% (green) or ↓ -8% (red)
- **Budget card**: Shows LinearProgressIndicator below number

**Calculations**:
- Delta = (current_period - previous_period) / previous_period * 100
- Previous period = same length as selected range, ending yesterday

#### 2. Time Range Selector

**Buttons**: Row of TextButton widgets

- Last 7 days
- Last 30 days
- This Month (default, highlighted)
- Last Month

**Behavior**:
- Click updates `start_date` and `end_date`
- Triggers data refresh
- Selected button has `bgcolor=Theme.PRIMARY`

#### 3. Provider Breakdown

**Horizontal bars**: Container with dynamic width

```python
bar_width = (provider_cost / total_cost) * container_max_width
Container(
    width=bar_width,
    height=32,
    bgcolor=provider_color,
    border_radius=4,
)
```

**Provider colors**:
- OpenAI: #10a37f (green)
- Anthropic: #d4a574 (tan)
- Local: #6b7280 (gray)
- Groq: #f55036 (orange)
- Google: #4285f4 (blue)

#### 4. Workflow Breakdown Table

**Columns**: Workflow Name | Cost | Calls | Tokens

**Features**:
- Sortable by clicking column headers
- Shows top 10 by default
- "Show All" button expands to 50 (then paginated)
- Scrollable container (max height 300px)

---

## Budget Management

### Budget Settings Panel

**Access**: Button in Usage Dashboard header → Opens AlertDialog

```
┌─────────────────────────────────────────────┐
│ Budget Settings                    [Save]   │
├─────────────────────────────────────────────┤
│ Monthly Limit (USD):                        │
│ [$___50.00_______]                          │
│                                              │
│ Alert Threshold: 80%                        │
│ [──────────●────────] (50% - 100%)         │
│                                              │
│ Reset Day: [1▼] (day of month)             │
│                                              │
│ ☐ Email Notifications                       │
│   Email: [_________________]                │
│                                              │
│ Current Usage: $41.25 (83% of limit)       │
│ ⚠️ Alert: You've exceeded your threshold!  │
└─────────────────────────────────────────────┘
```

**Fields**:
- `monthly_limit_usd`: TextField (float, required)
- `alert_threshold`: Slider (0.5 - 1.0, default 0.8)
- `reset_day`: Dropdown (1-31, default 1)
- `email_notifications`: Checkbox
- `notification_email`: TextField (conditional, validated)

**Validation**:
- Monthly limit > 0
- Alert threshold between 50% and 100%
- Email validation if notifications enabled

### Budget Alert System

#### Trigger Conditions

**1. Threshold Alert (80% by default)**:
```python
if current_cost / monthly_limit >= threshold:
    trigger_threshold_alert()
```

**2. Limit Exceeded (100%)**:
```python
if current_cost >= monthly_limit:
    trigger_limit_exceeded_alert()
```

#### Alert Display

**In-App Alerts**:
- **AI Hub tab badge**: "⚠️ Usage Alert"
- **Dashboard banner**: Yellow (threshold) or Red (exceeded) alert box at top
- **Provider status bar**: Orange/Red indicator icon
- **Snackbar notification**: Dismissible, appears on threshold crossing

**Alert Messages**:
- Threshold: "⚠️ You've used 85% of your monthly AI budget ($42.50 of $50.00)"
- Exceeded: "🚨 Monthly AI budget exceeded! $52.30 spent of $50.00 limit"

#### Alert Logic

**Anti-spam**:
- Track `last_alert_sent` timestamp in `ai_budgets` table
- Only alert once per threshold crossing
- Reset alerts when new month begins

**Budget Reset**:
- Runs at app startup (check if new month started based on `reset_day`)
- Automatic, no user action needed
- Preserves historical usage data (doesn't delete)

---

## CSV Export

### Export Options

**Dropdown Menu**:
1. Export This Month
2. Export Custom Range → Opens date picker
3. Export All

### CSV Format

```csv
Timestamp,Workflow ID,Workflow Name,Node ID,Provider,Model,Prompt Tokens,Completion Tokens,Total Tokens,Cost (USD),Latency (ms),Success,Error
2026-01-11 14:23:45,wf-123,Data Processing,node-456,openai,gpt-4,150,75,225,0.0068,1250,true,
2026-01-11 14:25:12,wf-123,Data Processing,node-457,anthropic,claude-3-sonnet,200,120,320,0.0096,980,true,
2026-01-11 14:30:05,wf-789,Report Generator,node-890,openai,gpt-3.5-turbo,80,45,125,0.0002,450,false,"API rate limit"
```

### Implementation

```python
async def export_usage_csv(start_date: date, end_date: date) -> str:
    """Export usage records as CSV."""
    records = await ai_storage.get_usage_records(start_date, end_date)

    # Limit to 10,000 records
    if len(records) > 10000:
        show_warning("Export limited to 10,000 most recent records")
        records = records[-10000:]

    # Build CSV
    csv_lines = [CSV_HEADER]
    for record in records:
        csv_lines.append(format_record_as_csv(record))

    return "\n".join(csv_lines)
```

**File Download**:
- Filename: `skynette-ai-usage-{YYYY-MM-DD}-to-{YYYY-MM-DD}.csv`
- Use Flet's file picker to save
- Show progress indicator for large exports (>1000 records)

---

## Visualization Strategy

### Flet-Native Charts

**Why no external charting library**:
- Zero dependencies (keeps app lightweight)
- Fast rendering (<500ms for 1000+ data points)
- Consistent styling with existing UI
- Easy to iterate and customize
- Can upgrade later if needed (YAGNI)

### Chart Components

#### Horizontal Bar Chart (Provider Breakdown)

```python
def build_provider_bar(provider_name: str, cost: float, total: float, color: str):
    percentage = (cost / total) * 100
    bar_width = (cost / total) * 400  # Max width 400px

    return ft.Container(
        content=ft.Row([
            ft.Icon(get_provider_icon(provider_name), size=16, color=color),
            ft.Text(provider_name, width=100),
            ft.Container(
                width=bar_width,
                height=24,
                bgcolor=color,
                border_radius=4,
            ),
            ft.Text(f"${cost:.2f} ({percentage:.0f}%)", size=12),
        ]),
        padding=ft.Padding.symmetric(vertical=4),
    )
```

#### Progress Bar (Budget Usage)

```python
budget_progress = ft.LinearProgressIndicator(
    value=current_cost / monthly_limit,
    color=get_budget_color(current_cost, monthly_limit, threshold),
    bgcolor=Theme.BG_TERTIARY,
    height=8,
)
```

**Colors**:
- Green: < threshold
- Yellow: >= threshold, < limit
- Red: >= limit

---

## Error Handling

### Edge Cases

#### 1. No Usage Data

```
┌─────────────────────────────────────────┐
│  No AI Usage Yet                        │
│                                          │
│  Start using AI nodes in workflows to   │
│  see usage analytics here.               │
│                                          │
│  [Go to AI Hub →]  [View Sample Data]  │
└─────────────────────────────────────────┘
```

**Empty state**:
- Friendly message with guidance
- Link to AI Hub Setup
- Optional: Show demo data toggle

#### 2. Budget Not Set

Budget card shows setup prompt:
```
─────────────
  Set Budget
  Configure monthly
  spending limit
  [Set Up →]
─────────────
```

**Behavior**:
- Budget alerts disabled until configured
- Metric card prompts setup
- One-click opens budget settings dialog

#### 3. Database Query Failures

```python
try:
    stats = await ai_storage.get_usage_stats(start, end)
except Exception as e:
    logger.error(f"Failed to fetch usage stats: {e}")
    show_error_banner("Unable to load usage data. Please refresh.")
    # Graceful degradation
    stats = {"total_calls": 0, "total_cost": 0.0, "total_tokens": 0, "avg_latency": 0.0}
```

**User feedback**:
- Error banner at top of dashboard
- "Refresh" button to retry
- Metrics show zero (not broken UI)

#### 4. Large Dataset Performance

**Optimization for >1000 records**:
- Aggregate by day instead of individual calls
- Show warning: "Showing aggregated data (1,234 calls)"
- Pagination for workflow breakdown (50 per page)
- CSV export limited to 10,000 records

#### 5. Data Validation

**Future dates**:
```python
if end_date > date.today():
    end_date = date.today()
```

**Invalid ranges**:
```python
if end_date < start_date:
    raise ValueError("end_date must be >= start_date")
```

#### 6. Currency Formatting

**Consistent display**:
- Format: `$12.45` (always USD, 2 decimals)
- Zero cost: `$0.00` (not blank)
- Large numbers: `$1,234.56` (comma separators)
- Very small: `$0.0012` (4 decimals if needed)

#### 7. Timezone Handling

**All timestamps in UTC**:
- Storage: UTC (already implemented in AIStorage)
- Display: Convert to user's local timezone
- Budget reset: Midnight UTC on configured day

---

## Performance Requirements

### Target Metrics

- **Dashboard Load**: < 1s with 1000+ usage records
- **Chart Render**: < 500ms per chart
- **Time Range Switch**: < 200ms
- **CSV Export**: Show progress for >1000 records
- **Budget Check**: < 10ms (runs on every AI call)

### Optimization Strategies

**1. Data Aggregation**:
```python
if record_count > 1000:
    # Aggregate by day instead of by-call
    stats = aggregate_by_day(records)
```

**2. Caching**:
- Cache current month's data in memory
- Refresh button to reload
- Auto-refresh on new usage logged

**3. Pagination**:
- Workflow table: 50 rows per page
- Load more on scroll or button click

**4. Async Loading**:
- Fetch metrics, provider breakdown, workflow breakdown in parallel
- Show skeleton loaders while loading
- Don't block UI thread

---

## Implementation Tasks

### Sprint 3 Task List (10 tasks)

**Task 1: Usage Dashboard View Structure**
- Create `UsageDashboardView` class
- Add 4th "Usage" tab to AI Hub
- Basic layout with placeholders
- Commit: `feat(ai-ui): create usage dashboard view structure`

**Task 2: Metrics Cards**
- Implement 4 metric cards (Cost, Calls, Tokens, Budget)
- Delta calculation from previous period
- Responsive layout
- Commit: `feat(ai-ui): implement usage metrics cards`

**Task 3: Time Range Selector**
- Add time range buttons (7d, 30d, This month, Last month)
- Update dashboard on selection
- Highlight selected range
- Commit: `feat(ai-ui): add time range selector`

**Task 4: Provider Breakdown Chart**
- Horizontal bar chart for provider costs
- Provider icons and colors
- Percentage display
- Commit: `feat(ai-ui): add provider breakdown visualization`

**Task 5: Workflow Breakdown Table**
- Sortable table (Name, Cost, Calls, Tokens)
- Top 10 workflows by cost
- Pagination for large datasets
- Commit: `feat(ai-ui): implement workflow cost breakdown table`

**Task 6: Budget Settings Panel**
- AlertDialog with budget configuration
- Monthly limit, threshold, reset day fields
- Save to database via AIStorage
- Commit: `feat(ai-ui): add budget settings panel`

**Task 7: Budget Alert System**
- Check budget on every usage log
- Trigger in-app alerts at threshold
- Badge on AI Hub tab
- Banner on dashboard
- Commit: `feat(ai): implement budget alert system`

**Task 8: CSV Export**
- Export usage data to CSV format
- Date range selection
- File download via file picker
- Progress indicator
- Commit: `feat(ai): add CSV export functionality`

**Task 9: Error Handling & Empty States**
- No data empty state
- Budget not set state
- Database error handling
- Loading states
- Commit: `feat(ai-ui): add error handling and empty states`

**Task 10: E2E Tests for Usage Dashboard**
- 20 tests covering dashboard UI
- Budget alert tests
- CSV export tests
- Time range selection tests
- Commit: `test(ai-ui): add E2E tests for usage dashboard`

---

## Success Criteria

### Functional Requirements

- ✅ **Dashboard displays accurate metrics** for selected time range
- ✅ **Provider breakdown** shows cost distribution correctly
- ✅ **Workflow table** is sortable and shows top workflows
- ✅ **Budget alerts** trigger at configured threshold
- ✅ **CSV export** works for any date range
- ✅ **Time range selector** updates all charts correctly

### Testing Requirements

- ✅ **E2E Tests**: 20+ tests for dashboard interactions
- ✅ **Budget Alert Tests**: Verify threshold and limit alerts
- ✅ **Data Accuracy**: Costs match AIStorage calculations
- ✅ **Empty States**: All edge cases handled gracefully

### Performance Requirements

- ✅ **Dashboard Load**: < 1s with 1000+ records
- ✅ **Chart Render**: < 500ms per visualization
- ✅ **Budget Check**: < 10ms per AI call
- ✅ **CSV Export**: Progress indicator for large exports

### User Experience Requirements

- ✅ **Intuitive Navigation**: Clear tab structure in AI Hub
- ✅ **Helpful Empty States**: Guide users to take action
- ✅ **Clear Error Messages**: Actionable feedback on failures
- ✅ **Responsive Layout**: Works on different screen sizes

---

## Technical Decisions

### Decision: Flet-Native Visualizations

**Choice**: Use native Flet components (Containers, Rows, LinearProgressIndicator) instead of external charting libraries.

**Rationale**:
- Zero external dependencies (lighter app)
- Fast rendering with 1000+ data points
- Consistent styling with rest of UI
- Easier to debug and iterate
- Can upgrade to matplotlib/Plotly later if needed (YAGNI)

**Trade-offs**:
- Less interactive than Plotly
- Manual implementation required
- Limited animation options

### Decision: Monthly Budget Cycle

**Choice**: Budget resets monthly, not on custom cycles.

**Rationale**:
- Aligns with most API billing cycles (OpenAI, Anthropic bill monthly)
- Simpler to implement and understand
- Matches user mental model ("How much did I spend this month?")

**Alternative Considered**: Weekly or custom cycles → Rejected as too complex for MVP

### Decision: In-App Alerts Only (Email Optional)

**Choice**: Budget alerts shown in-app by default. Email notifications are opt-in.

**Rationale**:
- No email infrastructure required initially
- Users check app regularly (desktop app)
- Email can be added later without breaking changes

**Future Enhancement**: Integrate with notification service (SendGrid, Mailgun)

---

## Phase 4 Completion Checklist

After Sprint 3, Phase 4 is complete when:

- ✅ **Sprint 1**: AI Core Testing & Foundation (110+ tests, storage, security)
- ✅ **Sprint 2**: AI Hub UI & Model Management (setup wizard, providers, models)
- ✅ **Sprint 3**: Usage Dashboard & Analytics (metrics, budgets, export)

**Total for Phase 4**:
- 130+ tests passing
- 90%+ code coverage for AI modules
- Complete AI integration from setup → usage → tracking
- Production-ready cost management

---

## Next Steps After Design Approval

1. **Create implementation plan** with detailed step-by-step tasks
2. **Set up git worktree** for isolated development
3. **Execute via Subagent-Driven Development** (same as Sprints 1 & 2)
4. **Test thoroughly** (E2E tests for all interactions)
5. **Release v0.5.0** with complete Phase 4

---

**Design Status**: ✅ Complete and Ready for Implementation

**Estimated Development Time**: 10 tasks × 30-45 minutes = 5-7 hours

**Target Release**: v0.5.0 (Phase 4 Complete)
