import React from 'react';

export default function HeatmapView({ data }) {
  if (!data) return null;
  const matrix = data.matrix || data;
  const months = data.months || ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"];
  const areas = Object.keys(matrix);

  if (areas.length === 0) return null;

  const getCellClass = (val) => {
    if (val === 0) return 'heatmap-cell level-0';
    if (val <= 2) return 'heatmap-cell level-1';
    if (val <= 4) return 'heatmap-cell level-2';
    if (val <= 6) return 'heatmap-cell level-3';
    return 'heatmap-cell level-4';
  };

  return (
    <div className="heatmap-container">
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '0.72rem', color: '#94a3b8' }}>
          <span style={{ fontWeight: 600 }}>Spill Density:</span>
          <span style={{ padding: '2px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)' }}>0</span>
          <span style={{ padding: '2px 8px', background: 'rgba(15, 118, 110, 0.7)', color: 'white', borderRadius: '4px' }}>1-2</span>
          <span style={{ padding: '2px 8px', background: 'rgba(13, 148, 136, 0.85)', color: 'white', borderRadius: '4px' }}>3-4</span>
          <span style={{ padding: '2px 8px', background: 'rgba(217, 119, 6, 0.85)', color: 'white', borderRadius: '4px' }}>5-6</span>
          <span style={{ padding: '2px 8px', background: 'rgba(220, 38, 38, 0.9)', color: 'white', borderRadius: '4px' }}>7+</span>
        </div>
      </div>

      <table className="heatmap-table">
        <thead>
          <tr>
            <th style={{ textAlign: 'left', minWidth: '160px' }}>Geographic Area</th>
            {months.map(m => (
              <th key={m}>{m}</th>
            ))}
            <th style={{ color: '#fbbf24' }}>Total</th>
          </tr>
        </thead>
        <tbody>
          {areas.map(areaName => {
            const rowData = matrix[areaName];
            return (
              <tr key={areaName}>
                <td style={{ fontWeight: 600, color: 'white', fontSize: '0.825rem' }}>{areaName}</td>
                {months.map(m => {
                  const val = rowData[m] || 0;
                  return (
                    <td key={m} className={getCellClass(val)} title={`${areaName} - ${m}: ${val} spills`}>
                      {val}
                    </td>
                  );
                })}
                <td className="heatmap-cell total" style={{ color: '#fbbf24', fontSize: '0.9rem' }}>
                  {rowData.Total || 0}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
