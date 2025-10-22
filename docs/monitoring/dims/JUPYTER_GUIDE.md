# DIMS Jupyter Notebook Guide

**DIMS Phase 3: Interactive Data Exploration**

**Created:** October 21, 2025
**Status:** ✅ **COMPLETE**

---

## Overview

The DIMS Jupyter Notebook provides a comprehensive, interactive environment for exploring your data inventory metrics with:

- 📊 **Real-time visualizations** - Interactive Plotly charts
- 📈 **Trend analysis** - Historical metric tracking
- 🔍 **Drill-down exploration** - Deep dive into specific metrics
- ✅ **Approval workflow tracking** - Monitor change approvals
- 📝 **Event log analysis** - Track automated updates
- 💾 **Export capabilities** - Generate reports for stakeholders
- 🎯 **Custom queries** - Write SQL queries directly

---

## Quick Start

### Launch the Notebook

```bash
# Simple launch
python scripts/monitoring/dims_cli.py notebook

# Or explicitly
python scripts/monitoring/dims_cli.py notebook launch
```

This will:
1. Start Jupyter Lab server
2. Open notebook in your default browser
3. Connect to DIMS database automatically

### Export as HTML Report

```bash
python scripts/monitoring/dims_cli.py notebook export
```

Generates static HTML report in `inventory/exports/dims_report_YYYYMMDD_HHMMSS.html`

---

## Notebook Structure

The DIMS Explorer notebook contains **10 comprehensive sections**:

### 1. Setup & Initialization
- Import libraries
- Configure display settings
- Initialize DIMS connection
- Verify database connectivity

### 2. System Overview
- System health metrics
- Metrics distribution by category
- Quick status dashboard

### 3. Latest Metrics
- All current metric values
- Filter by category
- Sort and search functionality

### 4. Metric Trend Analysis
- Historical trends for specific metrics
- Drift analysis across all metrics
- Volatility heatmaps

### 5. Verification Run History
- All verification runs timeline
- Execution time analysis
- Drift detection statistics

### 6. Approval Workflow
- Approval request history
- Status breakdown (pending/approved/rejected)
- Average drift analysis

### 7. Event Log Analysis
- Event processing history
- Success/failure rates
- Metrics updated per event

### 8. Custom Queries
- SQL query playground
- Multi-metric comparisons
- Ad-hoc analysis workspace

### 9. Data Export
- Export to CSV
- Export to Excel (multiple sheets)
- Automated report generation

### 10. Summary & Recommendations
- Automated insights
- High drift warnings
- High volatility alerts
- Stable metrics identification

---

## Common Use Cases

### 1. Daily Metric Review

**Goal:** Quick check of system status

```python
# Run cells 1-3 to get:
health = helper.get_system_health()
print(health)

df_latest = helper.get_latest_metrics()
display(df_latest)
```

**Output:** Health summary + all latest metrics

---

### 2. Investigate Metric Drift

**Goal:** Understand why a metric changed

```python
# Section 4: Customize these variables
category = 'code_base'
metric = 'python_files'
days = 30

# Run trend analysis
fig = helper.plot_metric_trend(category, metric, days)
fig.show()

# Get detailed drift summary
df_drift = helper.get_drift_summary(days=30)
df_drift[df_drift['metric'] == metric]
```

**Output:** Interactive trend chart + drift statistics

---

### 3. Approval Workflow Review

**Goal:** Check pending approvals and approval history

```python
# Section 6: Get all approvals
df_approvals = helper.get_approval_log(days=30)

# Filter pending
pending = df_approvals[df_approvals['status'] == 'pending']
print(f"Pending approvals: {len(pending)}")
display(pending)

# Visualize status distribution
fig = helper.plot_approval_status(days=30)
fig.show()
```

**Output:** Pending list + status pie chart

---

### 4. Event-Driven Update Monitoring

**Goal:** Verify event triggers are working

```python
# Section 7: Get event log
df_events = helper.get_event_log(days=7)

# Check success rate
success_rate = (df_events['success'].sum() / len(df_events)) * 100
print(f"Success rate: {success_rate:.1f}%")

# Group by event type
event_counts = df_events.groupby('event_type').size()
display(event_counts)
```

**Output:** Event statistics and success rates

---

### 5. Generate Stakeholder Report

**Goal:** Create comprehensive Excel report for team

```python
# Section 9: Export comprehensive report
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"dims_report_{timestamp}.xlsx"

dataframes = {
    'Latest Metrics': helper.get_latest_metrics(),
    'Drift Summary': helper.get_drift_summary(days=30),
    'Verification Runs': helper.get_verification_runs(days=30),
    'Approvals': helper.get_approval_log(days=30),
    'Events': helper.get_event_log(days=7)
}

path = helper.export_to_excel(dataframes, filename)
print(f"✓ Report: {path}")
```

**Output:** Excel file with 5 sheets in `inventory/exports/`

---

### 6. Custom SQL Analysis

**Goal:** Write custom queries for specific insights

```python
# Section 8: Custom query example
query = """
    SELECT
        DATE(recorded_at) as date,
        COUNT(*) as metrics_updated
    FROM dims_metrics_history
    WHERE recorded_at >= NOW() - INTERVAL '7 days'
    GROUP BY DATE(recorded_at)
    ORDER BY date
"""

conn = dims.database.pool.getconn()
try:
    df_custom = pd.read_sql_query(query, conn)
    display(df_custom)

    # Visualize
    fig = px.bar(df_custom, x='date', y='metrics_updated',
                 title='Daily Metric Updates')
    fig.show()
finally:
    dims.database.pool.putconn(conn)
```

**Output:** Custom query results + visualization

---

## Advanced Features

### Multi-Metric Comparison

Compare multiple metrics on the same chart:

```python
metrics_to_compare = [
    ('code_base', 'python_files'),
    ('code_base', 'test_files'),
    ('documentation', 'markdown_files')
]

fig = go.Figure()

for category, metric in metrics_to_compare:
    df_history = helper.get_metric_history(category, metric, days=30)
    if not df_history.empty:
        fig.add_trace(go.Scatter(
            x=df_history['recorded_at'],
            y=df_history['numeric_value'],
            mode='lines+markers',
            name=f"{category}.{metric}"
        ))

fig.update_layout(
    title="Multi-Metric Comparison",
    xaxis_title="Date",
    yaxis_title="Value",
    template='plotly_white'
)

fig.show()
```

### Volatility Analysis

Find most volatile metrics:

```python
df_drift = helper.get_drift_summary(days=30)

top_volatile = df_drift.nlargest(10, 'volatility_pct')[
    ['category', 'metric', 'volatility_pct', 'drift_pct']
]

print("🔥 TOP 10 MOST VOLATILE METRICS")
display(top_volatile)
```

### Verification Performance Analysis

Analyze verification run performance:

```python
df_verifications = helper.get_verification_runs(days=30)

print("📊 VERIFICATION STATISTICS")
print(f"Total Runs: {len(df_verifications)}")
print(f"Avg Execution Time: {df_verifications['execution_time_ms'].mean()/1000:.1f}s")
print(f"Min: {df_verifications['execution_time_ms'].min()/1000:.1f}s")
print(f"Max: {df_verifications['execution_time_ms'].max()/1000:.1f}s")

# Plot execution time trend
fig = px.line(df_verifications,
              x='run_timestamp',
              y=df_verifications['execution_time_ms']/1000,
              title='Verification Execution Time Trend',
              labels={'y': 'Execution Time (s)'})
fig.show()
```

---

## Keyboard Shortcuts

**Jupyter Lab Shortcuts:**

| Shortcut | Action |
|----------|--------|
| `Shift + Enter` | Run cell and move to next |
| `Ctrl + Enter` | Run cell in place |
| `A` | Insert cell above (command mode) |
| `B` | Insert cell below (command mode) |
| `DD` | Delete cell (command mode) |
| `M` | Convert to Markdown (command mode) |
| `Y` | Convert to Code (command mode) |
| `Ctrl + S` | Save notebook |
| `Shift + Tab` | Show function tooltip |

---

## Customization

### Change Default Time Window

Modify the `days` variable in trend analysis:

```python
# Default
days = 30

# Change to 7 days
days = 7

# Or 90 days
days = 90

# Then re-run visualization cells
```

### Add Custom Metrics

To analyze specific metrics:

```python
# Your custom metrics list
custom_metrics = [
    ('s3_storage', 'total_objects'),
    ('prediction_system', 'total_lines'),
    ('plus_minus_system', 'total_lines')
]

for category, metric in custom_metrics:
    fig = helper.plot_metric_trend(category, metric, days=30)
    fig.show()
```

### Customize Visualizations

All Plotly charts are customizable:

```python
fig = helper.plot_metric_trend('code_base', 'python_files', 30)

# Customize
fig.update_layout(
    title="Custom Title",
    template='plotly_dark',  # Dark theme
    height=600,              # Taller chart
    showlegend=True
)

fig.update_traces(
    line=dict(color='red', width=3),  # Red line, thicker
    marker=dict(size=10)               # Larger markers
)

fig.show()
```

---

## Troubleshooting

### Jupyter Not Installed

**Error:** `jupyter: command not found`

**Fix:**
```bash
pip install jupyterlab plotly matplotlib seaborn pandas ipywidgets
```

### Database Connection Failed

**Error:** `Database not available`

**Check:**
1. Credentials loaded: `source ~/nba-sim-credentials.env`
2. Database enabled: `features.database_backend: true` in config.yaml
3. Migration run: `python scripts/monitoring/dims_cli.py migrate`

### Notebook Cells Not Executing

**Issue:** Cells run but produce no output

**Fix:**
1. Restart kernel: `Kernel → Restart Kernel`
2. Re-run Setup cells (1-3)
3. Check database connection in cell output

### Empty DataFrames

**Issue:** Queries return no data

**Possible Causes:**
1. No data in database yet - run verification first: `dims_cli.py verify --update`
2. Time window too narrow - increase `days` parameter
3. Metric name incorrect - check `dims_cli.py info` for metric names

### Export Fails

**Error:** `nbconvert not found`

**Fix:**
```bash
pip install jupyter nbconvert
```

---

## Performance Tips

### Large Result Sets

For large queries, limit results:

```python
# Limit to recent data
df = helper.get_metric_history(category, metric, days=7)  # Instead of 30

# Or use SQL LIMIT
query = """
    SELECT * FROM dims_metrics_history
    ORDER BY recorded_at DESC
    LIMIT 100
"""
```

### Slow Visualizations

For faster rendering:

```python
# Reduce data points
df_sampled = df.sample(n=1000)  # Random sample

# Or downsample
df_downsampled = df.iloc[::10]  # Every 10th row
```

### Memory Management

Clear large DataFrames:

```python
del df_large
import gc
gc.collect()
```

---

## Best Practices

### 1. Document Your Analysis

Add markdown cells to explain your findings:

```markdown
## Analysis: Python File Growth

Between Oct 1-21, python_files increased from 1,252 to 1,255 (+3 files).

Key observations:
- Steady growth trend
- No significant spikes
- Consistent with development pace
```

### 2. Save Intermediate Results

Export important results:

```python
# Save important finding
df_important = df_drift[df_drift['drift_pct'] > 20]
helper.export_to_csv(df_important, 'high_drift_metrics.csv')
```

### 3. Use Comments

Comment complex queries:

```python
# Get all verification runs with drift detected
# excluding auto-updated runs (manual review needed)
df_manual_review = df_verifications[
    (df_verifications['drift_detected'] == True) &
    (df_verifications['auto_updated'] == False)
]
```

### 4. Regular Backups

Export notebook regularly:

```bash
# Export executed notebook as HTML
dims_cli.py notebook export
```

---

## Integration with CLI

The notebook complements DIMS CLI:

```bash
# Workflow:
# 1. Run verification
dims_cli.py verify --update

# 2. Launch notebook to analyze results
dims_cli.py notebook

# 3. Export findings
dims_cli.py notebook export
```

---

## Scheduled Reports

Automate notebook execution with cron:

```bash
# Add to crontab (weekly Monday 9 AM)
0 9 * * 1 cd /path/to/project && python scripts/monitoring/dims_cli.py notebook export && mail -s "DIMS Weekly Report" team@example.com < inventory/exports/dims_report_*.html
```

---

## API Reference

### DIMSNotebookHelper Methods

**Query Methods:**
- `get_latest_metrics()` → DataFrame of all current metrics
- `get_metric_history(category, metric, days)` → Historical data
- `get_verification_runs(days)` → Verification run history
- `get_approval_log(days)` → Approval workflow history
- `get_event_log(days)` → Event processing history

**Visualization Methods:**
- `plot_metric_trend(category, metric, days)` → Line chart
- `plot_metrics_overview()` → Bar chart by category
- `plot_verification_timeline(days)` → Dual timeline chart
- `plot_drift_heatmap(days)` → Drift heatmap
- `plot_approval_status(days)` → Pie chart

**Analysis Methods:**
- `get_drift_summary(days)` → Drift analysis DataFrame
- `get_system_health()` → Health metrics dictionary

**Export Methods:**
- `export_to_csv(df, filename)` → Export to CSV
- `export_to_excel(dataframes, filename)` → Multi-sheet Excel

---

## Examples Gallery

See `notebooks/examples/` for additional notebooks:
- `metric_correlation_analysis.ipynb` - Find correlated metrics
- `anomaly_detection.ipynb` - Detect unusual patterns
- `forecast_metrics.ipynb` - Predict future values
- `custom_dashboards.ipynb` - Build custom visualizations

---

## Next Steps

1. **Explore** all 10 sections to understand capabilities
2. **Customize** queries for your specific metrics
3. **Export** reports for your team
4. **Schedule** automated runs
5. **Share** insights with stakeholders

---

## Related Documentation

- **Phase 2 Summary:** `docs/DIMS_PHASE_2_SUMMARY.md`
- **Quick Reference:** `docs/DIMS_QUICK_REFERENCE.md`
- **Configuration:** `inventory/config.yaml`
- **Notebook Source:** `notebooks/dims_explorer.ipynb`

---

**Questions or Issues?** Check troubleshooting section above or review notebook comments.

**Phase 3 Jupyter Integration is fully operational!** 🚀
