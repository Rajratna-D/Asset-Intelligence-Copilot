import React from 'react';
import { Activity, AlertTriangle, ShieldCheck, Thermometer, User, Calendar, MapPin, Gauge } from 'lucide-react';

export default function StatusCard({ data }) {
  if (!data) return null;
  const d = data.data || data;

  const isProducing = d.is_producing;
  const tempDelta = d.temp_delta_c !== null ? Number(d.temp_delta_c).toFixed(1) : '--';
  const threshold = d.threshold_c !== null ? Number(d.threshold_c).toFixed(1) : '--';

  return (
    <div className="gen-card" style={{ background: 'rgba(15, 23, 42, 0.7)', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '18px' }}>
      {/* Header */}
      <div className="gen-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '12px' }}>
        <div className="gen-card-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', letterSpacing: '-0.01em' }}>{d.asset_id}</h4>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>({d.name || d.asset_id})</span>
          <span style={{ 
            fontSize: '0.7rem', 
            fontWeight: 800, 
            padding: '2px 8px', 
            borderRadius: '4px', 
            background: 'rgba(6, 182, 212, 0.15)', 
            color: '#f59e0b', 
            border: '1px solid rgba(6, 182, 212, 0.3)',
            fontFamily: 'JetBrains Mono, monospace'
          }}>
            {d.well_type}
          </span>
          {d.area_name && (
            <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <MapPin size={12} /> {d.area_name}
            </span>
          )}
        </div>
        <div>
          {isProducing ? (
            <div className="badge-producing">
              <span className="pulse-dot green"></span>
              PRODUCING OIL
            </div>
          ) : (
            <div className="badge-down">
              <span className="pulse-dot red"></span>
              NOT PRODUCING
            </div>
          )}
        </div>
      </div>

      {/* 4 Thermal Telemetry Boxes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '16px' }}>
        {/* 1. Wellhead Temp */}
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '10px', padding: '12px 14px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <Thermometer size={13} color="#f59e0b" /> Wellhead Temp
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f59e0b', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
            {d.eff_wellhead_temp_c !== null ? `${Number(d.eff_wellhead_temp_c).toFixed(1)} °C` : '--'}
          </div>
        </div>

        {/* 2. Ambient Temp */}
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '10px', padding: '12px 14px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <Activity size={13} color="#94a3b8" /> Ambient Air Temp
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f1f5f9', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
            {d.ambient_temp_c !== null ? `${Number(d.ambient_temp_c).toFixed(1)} °C` : '--'}
          </div>
        </div>

        {/* 3. Temp Difference */}
        <div style={{ 
          background: isProducing ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)', 
          borderRadius: '10px', 
          padding: '12px 14px', 
          border: `1px solid ${isProducing ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)'}` 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.68rem', fontWeight: 700, color: isProducing ? '#34d399' : '#fb7185', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <Gauge size={13} color={isProducing ? '#34d399' : '#fb7185'} /> Temp Difference
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: isProducing ? '#34d399' : '#fb7185', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
            +{tempDelta} °C
          </div>
        </div>

        {/* 4. Threshold */}
        <div style={{ background: 'rgba(0, 0, 0, 0.3)', borderRadius: '10px', padding: '12px 14px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            <ShieldCheck size={13} color="#f59e0b" /> Required Threshold
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f1f5f9', marginTop: '4px', fontFamily: 'JetBrains Mono, monospace' }}>
            ≥ {threshold} °C
          </div>
        </div>
      </div>

      {/* Inspection Metadata Pill Row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '12px' }}>
        {d.inspection_id && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Activity size={13} color="#f59e0b" /> Inspection: <code style={{ color: 'white' }}>{d.inspection_id}</code>
          </span>
        )}
        {d.inspected_date && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Calendar size={13} /> {d.inspected_date}
          </span>
        )}
        {d.inspector_name && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <User size={13} /> {d.inspector_name} {d.method ? `(${d.method})` : ''}
          </span>
        )}
      </div>

      {/* Recorded status staleness alert */}
      {d.is_recorded_status_out_of_date && (
        <div className="stale-warning">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>System of Record Discrepancy:</strong> Database lists status as <code>{d.recorded_status}</code>, but weekly thermal inspection confirms well is <strong>{isProducing ? 'PRODUCING' : 'STOPPED'}</strong>. Recorded status is refreshed only monthly and is out of date.
          </div>
        </div>
      )}

      {/* Operational Context note */}
      {d.reason && (
        <div style={{ marginTop: '12px', padding: '10px 14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', fontSize: '0.8rem', border: '1px solid rgba(255,255,255,0.05)' }}>
          <strong style={{ color: '#94a3b8' }}>Operational Context: </strong>
          <span style={{ color: '#f1f5f9' }}>{d.reason}</span>
        </div>
      )}
    </div>
  );
}
