import React, { useState } from 'react';
import { Download, Search } from 'lucide-react';

export default function VisualTable({ data }) {
  if (!data) return null;
  const [searchTerm, setSearchTerm] = useState('');

  // Normalize data payload
  let rows = [];
  if (Array.isArray(data)) {
    rows = data;
  } else if (data.data && Array.isArray(data.data)) {
    rows = data.data;
  } else if (data.wells && Array.isArray(data.wells)) {
    rows = data.wells;
  } else if (data.inspections && Array.isArray(data.inspections)) {
    rows = data.inspections.map(i => ({
      'Inspection ID': i.inspection_id,
      'Date': i.inspected_date,
      'Wellhead Temp': `${i.wellhead_temp_c} °C`,
      'Delta T': `${i.delta_c ? i.delta_c.toFixed(1) : (i.wellhead_temp_c - (i.ambient_temp_c || 0)).toFixed(1)} °C`,
      'Spill Detected': i.spill_detected ? `⚠️ ${i.spill_est_volume_bbl || 0} bbl` : 'None',
      'Inspector': i.inspector_name || 'Autonomous Drone'
    }));
  } else if (data.maintenance && Array.isArray(data.maintenance)) {
    rows = data.maintenance.map(m => ({
      'Work Order': m.maintenance_id,
      'Date': m.started_date,
      'Equipment': m.equipment_kind,
      'Issue': m.issue,
      'Downtime': `${m.downtime_hours || 0} hrs`,
      'Cost': m.cost_total_usd ? `$${m.cost_total_usd.toLocaleString()}` : '$0'
    }));
  } else if (data.records && Array.isArray(data.records)) {
    rows = data.records;
  }

  if (rows.length === 0) {
    return <div style={{ padding: '12px', color: '#94a3b8', fontSize: '0.85rem' }}>No tabular records to display.</div>;
  }

  // Get headers from first row
  const headers = Object.keys(rows[0]).filter(k => typeof rows[0][k] !== 'object');

  // Filter rows
  const filteredRows = rows.filter(r => {
    if (!searchTerm) return true;
    return Object.values(r).some(val => 
      String(val).toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const downloadCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(",")].concat(filteredRows.map(r => headers.map(h => `"${r[h] || ''}"`).join(","))).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "oilfield_wells_report.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ marginTop: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-secondary)', padding: '4px 10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
          <Search size={14} color="#94a3b8" />
          <input 
            type="text" 
            placeholder="Search records..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '0.78rem', outline: 'none' }}
          />
        </div>
        <button onClick={downloadCSV} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
          <Download size={13} /> Export CSV ({filteredRows.length})
        </button>
      </div>

      <div className="gen-table-container">
        <table className="gen-table">
          <thead>
            <tr>
              {headers.map(h => (
                <th key={h}>{h.replace(/_/g, ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, idx) => (
              <tr key={idx}>
                {headers.map(h => {
                  const val = row[h];
                  if (h === 'Type') {
                    return (
                      <td key={h}>
                        <span style={{ 
                          fontSize: '0.72rem', 
                          fontWeight: 700, 
                          padding: '2px 8px', 
                          borderRadius: '4px',
                          background: val === 'Breach' ? 'rgba(244,63,94,0.15)' : (val === 'Pending' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)'),
                          color: val === 'Breach' ? 'var(--accent-rose)' : (val === 'Pending' ? 'var(--accent-amber)' : 'var(--accent-green)')
                        }}>
                          {val}
                        </span>
                      </td>
                    );
                  }
                  if (h === 'asset_id' || h === 'inspection_id' || h === 'maintenance_id') {
                    return <td key={h}><code style={{ color: 'var(--accent-cyan)' }}>{val}</code></td>;
                  }
                  return <td key={h}>{val !== null && val !== undefined ? String(val) : '--'}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
