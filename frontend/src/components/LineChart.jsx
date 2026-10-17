import React, { useState } from 'react';

export default function LineChart({ data }) {
  if (!data) return null;
  const series = data.data || data;
  if (!Array.isArray(series) || series.length === 0) return null;

  const [hoveredIdx, setHoveredIdx] = useState(null);

  // SVG Chart Dimensions
  const width = 760;
  const height = 280;
  const padding = { top: 20, right: 30, bottom: 40, left: 50 };

  // Calculate scales
  const temps = series.flatMap(s => [s.wellhead_temp_c, s.ambient_temp_c].filter(v => v !== null));
  const minTemp = Math.floor(Math.min(...temps, 10));
  const maxTemp = Math.ceil(Math.max(...temps, 60));

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const getX = (idx) => padding.left + (idx / (series.length - 1)) * chartW;
  const getY = (temp) => padding.top + chartH - ((temp - minTemp) / (maxTemp - minTemp)) * chartH;

  // Build SVG path strings
  const wellheadPoints = series.map((s, idx) => `${getX(idx)},${getY(s.wellhead_temp_c)}`).join(' ');
  const ambientPoints = series.map((s, idx) => `${getX(idx)},${getY(s.ambient_temp_c)}`).join(' ');

  return (
    <div style={{ marginTop: '14px', background: 'var(--bg-secondary)', padding: '18px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h5 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          13-Week Wellhead vs. Ambient Air Temperature Telemetry
        </h5>
        <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b' }}>
            <span style={{ width: '12px', height: '3px', background: '#f59e0b', borderRadius: '2px' }}></span> Wellhead Temp (°C)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b' }}>
            <span style={{ width: '12px', height: '3px', background: '#f59e0b', borderRadius: '2px' }}></span> Ambient Air Temp (°C)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f43f5e' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f43f5e' }}></span> Not Producing (Stop)
          </span>
        </div>
      </div>

      <div style={{ position: 'relative' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
          {/* Y Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
            const val = Math.round(minTemp + ratio * (maxTemp - minTemp));
            const y = padding.top + chartH - ratio * chartH;
            return (
              <g key={i}>
                <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#1e293b" strokeDasharray="4 4" />
                <text x={padding.left - 10} y={y + 4} fill="#64748b" fontSize="10" textAnchor="end">{val}°C</text>
              </g>
            );
          })}

          {/* Lines */}
          <polyline fill="none" stroke="#f59e0b" strokeWidth="2.5" points={ambientPoints} strokeLinejoin="round" />
          <polyline fill="none" stroke="#f59e0b" strokeWidth="2.5" points={wellheadPoints} strokeLinejoin="round" />

          {/* Data Points */}
          {series.map((s, idx) => {
            const x = getX(idx);
            const yWh = getY(s.wellhead_temp_c);
            const isNonProd = !s.is_producing;

            return (
              <g key={idx} onMouseEnter={() => setHoveredIdx(idx)} onMouseLeave={() => setHoveredIdx(null)} style={{ cursor: 'pointer' }}>
                {/* Date label on X axis */}
                <text x={x} y={height - padding.bottom + 18} fill="#64748b" fontSize="9" textAnchor="middle" transform={`rotate(25, ${x}, ${height - padding.bottom + 18})`}>
                  {s.inspected_date.slice(5)}
                </text>

                {/* Point */}
                <circle cx={x} cy={yWh} r={isNonProd ? 6 : 4} fill={isNonProd ? '#f43f5e' : '#f59e0b'} stroke="#0f172a" strokeWidth="2" />
                {isNonProd && (
                  <circle cx={x} cy={yWh} r="10" fill="none" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="2 2" />
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hoveredIdx !== null && (
          <div style={{
            position: 'absolute',
            top: '10px',
            right: '20px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid var(--border-glow)',
            borderRadius: '6px',
            padding: '8px 12px',
            fontSize: '0.75rem',
            boxShadow: 'var(--shadow-card)',
            pointerEvents: 'none'
          }}>
            <div style={{ fontWeight: 700, color: 'white', marginBottom: '4px' }}>
              Date: {series[hoveredIdx].inspected_date} ({series[hoveredIdx].inspection_id})
            </div>
            <div style={{ color: '#f59e0b' }}>Wellhead: {series[hoveredIdx].wellhead_temp_c} °C</div>
            <div style={{ color: '#f59e0b' }}>Ambient: {series[hoveredIdx].ambient_temp_c} °C</div>
            <div style={{ color: series[hoveredIdx].is_producing ? 'var(--accent-green)' : 'var(--accent-rose)', fontWeight: 700 }}>
              Delta: +{series[hoveredIdx].temp_delta_c} °C ({series[hoveredIdx].is_producing ? 'Producing' : 'STOPPED - Non-Producing'})
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
