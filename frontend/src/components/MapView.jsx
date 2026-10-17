import React, { useState, useMemo } from 'react';
import { MapPin, Navigation, AlertTriangle, ShieldAlert, Crosshair, Calendar, Droplets } from 'lucide-react';

export default function MapView({ data }) {
  if (!data) return null;
  const rawSpills = data.spills || (Array.isArray(data) ? data : []);
  const spills = useMemo(() => {
    return rawSpills.filter(s => s && s.lat && s.lon);
  }, [rawSpills]);

  const [selectedPin, setSelectedPin] = useState(null);
  const [hoveredPin, setHoveredPin] = useState(null);

  const mapW = 860;
  const mapH = 440;
  const padding = 70;

  // Compute dynamic bounding box from actual data pins
  const bounds = useMemo(() => {
    if (spills.length === 0) {
      return { minLat: 31.75, maxLat: 32.25, minLon: -102.55, maxLon: -102.10 };
    }
    const lats = spills.map(s => Number(s.lat));
    const lons = spills.map(s => Number(s.lon));
    let minLat = Math.min(...lats);
    let maxLat = Math.max(...lats);
    let minLon = Math.min(...lons);
    let maxLon = Math.max(...lons);

    // Ensure minimum span so close points don't collapse
    const latSpan = Math.max(maxLat - minLat, 0.04);
    const lonSpan = Math.max(maxLon - minLon, 0.06);

    const latMargin = latSpan * 0.25;
    const lonMargin = lonSpan * 0.25;

    return {
      minLat: minLat - latMargin,
      maxLat: maxLat + latMargin,
      minLon: minLon - lonMargin,
      maxLon: maxLon + lonMargin
    };
  }, [spills]);

  // Coordinate projection into SVG viewport
  const getX = (lon) => {
    return ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * (mapW - padding * 2) + padding;
  };

  const getY = (lat) => {
    // Invert Y because latitude increases northward
    return mapH - (((lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * (mapH - padding * 2) + padding);
  };

  const activeFocus = selectedPin || hoveredPin;

  return (
    <div className="geospatial-explorer-container" style={{
      background: 'linear-gradient(180deg, #0b0f17 0%, #080c14 100%)',
      borderRadius: '12px',
      border: '1px solid rgba(245, 158, 11, 0.25)',
      padding: '16px',
      marginTop: '12px',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)'
    }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'rgba(245, 158, 11, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              <Navigation size={15} color="#f59e0b" />
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
                Geospatial Oilfield Spill Location Map
              </h4>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Auto-focused bounding sector · {spills.length} confirmed incident locations
              </div>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', background: 'rgba(15, 23, 42, 0.6)', padding: '5px 12px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#cbd5e1' }}>
            <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#f43f5e', display: 'inline-block', boxShadow: '0 0 8px rgba(244, 63, 94, 0.6)' }}></span>
            <span>Reportable (&ge; 5.0 bbl)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', color: '#cbd5e1' }}>
            <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block', boxShadow: '0 0 8px rgba(245, 158, 11, 0.6)' }}></span>
            <span>Minor (&lt; 5.0 bbl)</span>
          </div>
        </div>
      </div>

      {/* Interactive SVG Canvas */}
      <div style={{ position: 'relative', width: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <svg viewBox={`0 0 ${mapW} ${mapH}`} style={{ width: '100%', height: 'auto', display: 'block', background: '#070a10' }}>
          {/* Tactical Grid Pattern */}
          <defs>
            <pattern id="geo-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.8" />
            </pattern>
            <radialGradient id="sector-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(245, 158, 11, 0.08)" />
              <stop offset="100%" stopColor="rgba(0, 0, 0, 0)" />
            </radialGradient>
          </defs>

          {/* Grid Fill */}
          <rect width={mapW} height={mapH} fill="url(#geo-grid)" />
          <circle cx={mapW / 2} cy={mapH / 2} r={mapW / 2} fill="url(#sector-glow)" />

          {/* Radar Range Rings */}
          <circle cx={mapW / 2} cy={mapH / 2} r={mapH * 0.35} fill="none" stroke="rgba(245, 158, 11, 0.08)" strokeDasharray="4 4" />
          <circle cx={mapW / 2} cy={mapH / 2} r={mapH * 0.65} fill="none" stroke="rgba(245, 158, 11, 0.05)" strokeDasharray="4 4" />

          {/* Coordinate Border Labels */}
          <text x={12} y={22} fill="rgba(148, 163, 184, 0.5)" fontSize="9" fontFamily="monospace">
            {bounds.maxLat.toFixed(3)}°N, {bounds.minLon.toFixed(3)}°W
          </text>
          <text x={mapW - 12} y={mapH - 12} fill="rgba(148, 163, 184, 0.5)" fontSize="9" fontFamily="monospace" textAnchor="end">
            {bounds.minLat.toFixed(3)}°N, {bounds.maxLon.toFixed(3)}°W
          </text>

          {/* Crosshair Center */}
          <line x1={mapW / 2 - 12} y1={mapH / 2} x2={mapW / 2 + 12} y2={mapH / 2} stroke="rgba(245, 158, 11, 0.2)" strokeWidth="1" />
          <line x1={mapW / 2} y1={mapH / 2 - 12} x2={mapW / 2} y2={mapH / 2 + 12} stroke="rgba(245, 158, 11, 0.2)" strokeWidth="1" />

          {/* Spill Pins */}
          {spills.map((s, idx) => {
            const px = getX(Number(s.lon));
            const py = getY(Number(s.lat));
            const vol = Number(s.spill_est_volume_bbl || 0);
            const isReportable = vol >= 5.0;
            const isSelected = selectedPin?.asset_id === s.asset_id;
            const isHovered = hoveredPin?.asset_id === s.asset_id;
            const pinColor = isReportable ? '#f43f5e' : '#f59e0b';
            const pinRadius = isReportable ? 10 : 8;

            return (
              <g
                key={s.asset_id || idx}
                onClick={() => setSelectedPin(s)}
                onMouseEnter={() => setHoveredPin(s)}
                onMouseLeave={() => setHoveredPin(null)}
                style={{ cursor: 'pointer', transition: 'transform 0.15s ease' }}
              >
                {/* Outer halo / wave pulse */}
                <circle
                  cx={px}
                  cy={py}
                  r={pinRadius + (isSelected || isHovered ? 12 : 6)}
                  fill={isReportable ? 'rgba(244, 63, 94, 0.18)' : 'rgba(245, 158, 11, 0.18)'}
                />

                {/* Tactical target ring on selection */}
                {(isSelected || isHovered) && (
                  <circle
                    cx={px}
                    cy={py}
                    r={pinRadius + 16}
                    fill="none"
                    stroke={pinColor}
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                  />
                )}

                {/* Core Pin Circle */}
                <circle
                  cx={px}
                  cy={py}
                  r={pinRadius}
                  fill={pinColor}
                  stroke="#ffffff"
                  strokeWidth={isSelected || isHovered ? 2.5 : 1.5}
                  style={{ filter: `drop-shadow(0 0 6px ${pinColor})` }}
                />

                {/* Pin Center Dot */}
                <circle cx={px} cy={py} r={2.5} fill="#0b0f17" />

                {/* High-Legibility Badge Pill */}
                <g transform={`translate(${px}, ${py - pinRadius - 16})`}>
                  {/* Badge Background */}
                  <rect
                    x={-42}
                    y={-11}
                    width={84}
                    height={19}
                    rx={9}
                    fill="rgba(10, 14, 23, 0.92)"
                    stroke={isSelected || isHovered ? pinColor : 'rgba(255, 255, 255, 0.2)'}
                    strokeWidth={isSelected || isHovered ? 1.5 : 1}
                  />
                  {/* Well Label */}
                  <text
                    x={0}
                    y={2}
                    fill="#ffffff"
                    fontSize="9.5"
                    fontWeight="700"
                    textAnchor="middle"
                    fontFamily="monospace"
                  >
                    {s.asset_id}
                  </text>
                </g>

                {/* Volume Tag Underneath */}
                <text
                  x={px}
                  y={py + pinRadius + 14}
                  fill={pinColor}
                  fontSize="9"
                  fontWeight="700"
                  textAnchor="middle"
                  style={{ textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}
                >
                  {vol.toFixed(1)} bbl
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Detail Card for Focused Pin */}
        {activeFocus && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: 'rgba(11, 15, 23, 0.96)',
            backdropFilter: 'blur(10px)',
            border: `1px solid ${Number(activeFocus.spill_est_volume_bbl || 0) >= 5.0 ? '#f43f5e' : '#f59e0b'}`,
            borderRadius: '10px',
            padding: '14px 18px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
            fontSize: '0.8rem',
            width: '260px',
            zIndex: 15,
            animation: 'fadeIn 0.15s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MapPin size={14} color="#f59e0b" />
                <strong style={{ color: '#ffffff', fontSize: '0.95rem', fontFamily: 'monospace' }}>
                  {activeFocus.asset_id}
                </strong>
              </div>
              <button
                onClick={() => setSelectedPin(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '12px',
                  padding: '2px'
                }}
              >
                ✕
              </button>
            </div>

            <div style={{
              display: 'inline-block',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontWeight: 700,
              marginBottom: '10px',
              background: Number(activeFocus.spill_est_volume_bbl || 0) >= 5.0 ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              color: Number(activeFocus.spill_est_volume_bbl || 0) >= 5.0 ? '#f43f5e' : '#fbbf24',
              border: `1px solid ${Number(activeFocus.spill_est_volume_bbl || 0) >= 5.0 ? 'rgba(244, 63, 94, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`
            }}>
              {Number(activeFocus.spill_est_volume_bbl || 0) >= 5.0 ? '⚠️ REPORTABLE INCIDENT' : 'MINOR CONTAINED SPILL'}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', color: '#cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8' }}>Volume:</span>
                <strong style={{ color: '#fbbf24' }}>{Number(activeFocus.spill_est_volume_bbl || 0).toFixed(1)} bbl</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#94a3b8' }}>Date:</span>
                <span>{activeFocus.inspected_date || 'N/A'}</span>
              </div>
              {activeFocus.inspection_id && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Inspection ID:</span>
                  <code style={{ color: '#fbbf24', fontSize: '0.74rem' }}>{activeFocus.inspection_id}</code>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', paddingTop: '6px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', fontSize: '0.72rem', color: '#94a3b8' }}>
                <span>GPS:</span>
                <span>{Number(activeFocus.lat).toFixed(4)}° N, {Number(activeFocus.lon).toFixed(4)}° W</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Structured Spill Roster Table Below Canvas for 100% Readability */}
      <div style={{ marginTop: '14px' }}>
        <div style={{ fontSize: '0.76rem', fontWeight: 600, color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Geolocated Incident Roster ({spills.length} Wells)
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: '10px'
        }}>
          {spills.map((s, idx) => {
            const vol = Number(s.spill_est_volume_bbl || 0);
            const isRep = vol >= 5.0;
            const isSelected = selectedPin?.asset_id === s.asset_id;

            return (
              <div
                key={s.asset_id || idx}
                onClick={() => setSelectedPin(s)}
                onMouseEnter={() => setHoveredPin(s)}
                onMouseLeave={() => setHoveredPin(null)}
                style={{
                  background: isSelected ? 'rgba(245, 158, 11, 0.12)' : 'rgba(15, 23, 42, 0.5)',
                  border: isSelected ? '1px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, color: '#f8fafc', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {s.asset_id}
                  </span>
                  <span style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: isRep ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: isRep ? '#f43f5e' : '#fbbf24'
                  }}>
                    {vol.toFixed(1)} bbl
                  </span>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  {s.inspected_date} · ({Number(s.lat).toFixed(3)}°, {Number(s.lon).toFixed(3)}°)
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
