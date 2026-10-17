import React from 'react';

export default function BarChart({ data }) {
  if (!data) return null;

  // Format data
  let items = [];
  let unit = '';
  let title = 'Comparison Analysis';

  if (data.data && Array.isArray(data.data)) {
    // Downtime format (Q6)
    items = data.data.map(d => ({
      label: d.asset_id,
      sublabel: d.well_type,
      value: d.downtime_days || 0
    }));
    unit = 'days';
    title = `Top Downtime Wells (${data.area || 'Area'})`;
  } else if (data.costs && data.costs.well_costs) {
    // Repair costs format (Q11)
    const wellCosts = data.costs.well_costs;
    items = Object.keys(wellCosts).map(wid => ({
      label: wid,
      sublabel: '2026 Repairs',
      value: wellCosts[wid] || 0
    }));
    unit = 'USD';
    title = `2026 Repair Costs Breakdown (${items.length} Wells)`;
  }

  if (items.length === 0) return null;

  const maxValue = Math.max(...items.map(i => i.value), 1);

  return (
    <div style={{ marginTop: '14px', background: 'var(--bg-secondary)', padding: '18px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
      <h5 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' }}>
        {title}
      </h5>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {items.map((item, idx) => {
          const pct = Math.round((item.value / maxValue) * 100);
          return (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600 }}>
                <span style={{ color: 'white', display: 'flex', gap: '6px' }}>
                  <span>{item.label}</span>
                  {item.sublabel && <span style={{ color: '#94a3b8', fontWeight: 400 }}>({item.sublabel})</span>}
                </span>
                <span style={{ color: 'var(--accent-cyan)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {unit === 'USD' ? `$${item.value.toLocaleString()}` : `${item.value} ${unit}`}
                </span>
              </div>
              <div style={{ height: '12px', background: 'var(--bg-primary)', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <div 
                  style={{ 
                    height: '100%', 
                    width: `${pct}%`, 
                    background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-blue))',
                    borderRadius: '6px',
                    transition: 'width 0.6s ease'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
