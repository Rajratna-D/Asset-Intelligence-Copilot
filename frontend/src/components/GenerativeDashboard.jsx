import React, { useState } from 'react';
import { 
  Activity, 
  Layers, 
  Flame, 
  Droplet, 
  ShieldAlert, 
  ChevronRight, 
  CheckCircle2, 
  AlertTriangle, 
  Gauge, 
  Sparkles, 
  Download, 
  ExternalLink,
  Compass,
  Zap,
  BarChart3,
  Factory,
  Sliders,
  RotateCw
} from 'lucide-react';

export default function GenerativeDashboard({ data, onActionClick }) {
  if (!data) return null;
  const d = data.data || data;

  const [activeTab, setActiveTab] = useState(d.default_tab || 'sectors'); // 'sectors' | 'refinery' | 'yields' | 'hse'
  const [selectedSector, setSelectedSector] = useState(null);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [filterQuery, setFilterQuery] = useState('');

  const kpis = d.kpi_metrics || [];
  const sectors = d.sectors || [];
  const units = d.refinery_units || [];
  const yields = d.refinery_yields || [];
  const actions = d.quick_actions || [];

  const handlePromptClick = (prompt) => {
    if (onActionClick && prompt) {
      onActionClick(prompt);
    }
  };

  const downloadReport = () => {
    const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(d, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", jsonStr);
    dlAnchor.setAttribute("download", `generative_dashboard_${Date.now()}.json`);
    dlAnchor.click();
  };

  return (
    <div className="generative-dashboard" style={{
      background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(10, 15, 28, 0.98) 100%)',
      borderRadius: '16px',
      border: '1px solid rgba(56, 189, 248, 0.25)',
      boxShadow: '0 20px 40px -15px rgba(0, 0, 0, 0.7), 0 0 30px rgba(14, 165, 233, 0.08)',
      padding: '22px',
      marginTop: '16px',
      marginBottom: '16px',
      color: '#e2e8f0',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Ambient background glow */}
      <div style={{
        position: 'absolute',
        top: '-60px',
        right: '-60px',
        width: '260px',
        height: '260px',
        background: 'radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, transparent 70%)',
        pointerEvents: 'none'
      }} />

      {/* Header bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px',
        paddingBottom: '16px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        marginBottom: '20px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 9px',
              borderRadius: '999px',
              background: 'linear-gradient(90deg, rgba(14, 165, 233, 0.2), rgba(168, 85, 247, 0.2))',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              fontSize: '0.72rem',
              fontWeight: 700,
              color: '#f59e0b',
              letterSpacing: '0.04em',
              textTransform: 'uppercase'
            }}>
              <Sparkles size={12} color="#f59e0b" />
              Generative UI · Gemini 3.8 Flash
            </span>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Reference Date: {d.timestamp || '2026-10-17'}
            </span>
          </div>
          <h3 style={{
            fontSize: '1.35rem',
            fontWeight: 800,
            color: '#ffffff',
            letterSpacing: '-0.02em',
            margin: 0
          }}>
            {d.title || 'Fleet & Refinery Operations Intelligence Dashboard'}
          </h3>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '4px 0 0 0' }}>
            {d.subtitle || 'Real-time multi-tier asset telemetry, thermal production ground truth & downstream conversion analysis'}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            onClick={downloadReport}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              color: '#cbd5e1',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            title="Export Generative UI JSON Schema"
          >
            <Download size={13} />
            Export Schema
          </button>
        </div>
      </div>

      {/* KPI Stat Cards Strip */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        marginBottom: '20px'
      }}>
        {kpis.map((kpi, idx) => {
          const isGood = kpi.status === 'good';
          const isWarn = kpi.status === 'warning';
          const isAlert = kpi.status === 'alert';
          const accentColor = isGood ? '#10b981' : isWarn ? '#f59e0b' : isAlert ? '#f43f5e' : '#f59e0b';

          return (
            <div key={idx} style={{
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '12px',
              padding: '14px',
              border: `1px solid ${accentColor}25`,
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '3px',
                height: '100%',
                background: accentColor
              }} />
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                {kpi.label}
              </div>
              <div style={{
                fontSize: '1.45rem',
                fontWeight: 800,
                color: '#ffffff',
                margin: '6px 0 2px 0',
                fontFamily: 'JetBrains Mono, monospace'
              }}>
                {kpi.value}
              </div>
              <div style={{ fontSize: '0.74rem', color: accentColor, fontWeight: 600 }}>
                {kpi.subvalue || kpi.change || ''}
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        paddingBottom: '12px',
        marginBottom: '18px',
        overflowX: 'auto'
      }}>
        <button
          onClick={() => setActiveTab('sectors')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: activeTab === 'sectors' ? 'rgba(14, 165, 233, 0.2)' : 'transparent',
            border: activeTab === 'sectors' ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
            color: activeTab === 'sectors' ? '#f59e0b' : '#94a3b8',
            padding: '7px 14px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <Layers size={14} />
          Sector Performance ({sectors.length})
        </button>

        <button
          onClick={() => setActiveTab('refinery')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: activeTab === 'refinery' ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
            border: activeTab === 'refinery' ? '1px solid rgba(192, 132, 252, 0.4)' : '1px solid transparent',
            color: activeTab === 'refinery' ? '#c084fc' : '#94a3b8',
            padding: '7px 14px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <Factory size={14} />
          Refinery & Conversion Units ({units.length})
        </button>

        <button
          onClick={() => setActiveTab('yields')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: activeTab === 'yields' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
            border: activeTab === 'yields' ? '1px solid rgba(52, 211, 153, 0.4)' : '1px solid transparent',
            color: activeTab === 'yields' ? '#34d399' : '#94a3b8',
            padding: '7px 14px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <BarChart3 size={14} />
          Product Yield Distribution
        </button>

        <button
          onClick={() => setActiveTab('hse')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: activeTab === 'hse' ? 'rgba(244, 63, 94, 0.2)' : 'transparent',
            border: activeTab === 'hse' ? '1px solid rgba(251, 113, 133, 0.4)' : '1px solid transparent',
            color: activeTab === 'hse' ? '#fb7185' : '#94a3b8',
            padding: '7px 14px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <ShieldAlert size={14} />
          HSE & Compliance Rules
        </button>
      </div>

      {/* Tab 1: Sector Performance */}
      {activeTab === 'sectors' && (
        <div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '14px',
            marginBottom: '18px'
          }}>
            {sectors.map((sec, idx) => {
              const prodRate = Math.round((sec.producing / sec.total_wells) * 100);
              const isHigh = prodRate >= 90;
              const isSelected = selectedSector === sec.sector_id;

              return (
                <div 
                  key={idx}
                  onClick={() => setSelectedSector(isSelected ? null : sec.sector_id)}
                  style={{
                    background: isSelected ? 'rgba(14, 165, 233, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '12px',
                    padding: '16px',
                    border: isSelected ? '1px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.07)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#ffffff' }}>
                      {sec.name}
                    </div>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      background: isHigh ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: isHigh ? '#34d399' : '#fbbf24',
                      border: `1px solid ${isHigh ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                    }}>
                      {sec.status || (isHigh ? 'Optimal' : 'Action Required')}
                    </span>
                  </div>

                  {/* Efficiency Progress Bar */}
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                      <span style={{ color: '#94a3b8' }}>Operational Efficiency</span>
                      <span style={{ fontWeight: 700, color: '#f59e0b' }}>{prodRate}%</span>
                    </div>
                    <div style={{ height: '8px', background: 'rgba(0,0,0,0.4)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${prodRate}%`,
                        background: 'linear-gradient(90deg, #f59e0b, #10b981)',
                        borderRadius: '4px'
                      }} />
                    </div>
                  </div>

                  {/* Metrics grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', textAlign: 'center', background: 'rgba(0,0,0,0.25)', padding: '10px', borderRadius: '8px' }}>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Total</div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>{sec.total_wells}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#34d399' }}>Producing</div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#34d399' }}>{sec.producing}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#fb7185' }}>Down</div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fb7185' }}>{sec.non_producing}</div>
                    </div>
                  </div>

                  {/* Spills line */}
                  <div style={{ marginTop: '10px', fontSize: '0.74rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                    <span>2026 Spills: <strong style={{ color: '#fff' }}>{sec.spill_count_2026 || 0}</strong></span>
                    <span>Total Vol: <strong style={{ color: '#fff' }}>{Number(sec.spill_volume_bbl || 0).toFixed(1)} bbl</strong></span>
                  </div>

                  {/* Drilldown button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePromptClick(`Which wells in ${sec.name} are not producing oil right now, and why? Show them in a table.`);
                    }}
                    style={{
                      width: '100%',
                      marginTop: '12px',
                      padding: '6px',
                      background: 'rgba(56, 189, 248, 0.1)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      borderRadius: '6px',
                      color: '#f59e0b',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px'
                    }}
                  >
                    Inspect Non-Producing Wells <ChevronRight size={12} />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Comparative SVG Bar Chart */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '12px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            marginBottom: '16px'
          }}>
            <h5 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', margin: '0 0 14px 0', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Sector Fleet Distribution (Producing vs Down Wells)
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {sectors.map((sec, idx) => {
                const prodPct = Math.round((sec.producing / sec.total_wells) * 100);
                const downPct = 100 - prodPct;
                return (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '150px', fontSize: '0.78rem', fontWeight: 600, color: '#ffffff', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {sec.name}
                    </div>
                    <div style={{ flex: 1, display: 'flex', height: '18px', borderRadius: '4px', overflow: 'hidden', background: 'rgba(0,0,0,0.5)' }}>
                      <div 
                        style={{ 
                          width: `${prodPct}%`, 
                          background: 'linear-gradient(90deg, #0284c7, #10b981)', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          fontSize: '0.68rem', 
                          fontWeight: 700, 
                          color: '#fff' 
                        }}
                        title={`Producing: ${sec.producing} (${prodPct}%)`}
                      >
                        {prodPct >= 20 ? `${sec.producing} Active` : ''}
                      </div>
                      <div 
                        style={{ 
                          width: `${downPct}%`, 
                          background: 'linear-gradient(90deg, #f43f5e, #e11d48)', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          fontSize: '0.68rem', 
                          fontWeight: 700, 
                          color: '#fff' 
                        }}
                        title={`Down: ${sec.non_producing} (${downPct}%)`}
                      >
                        {downPct >= 10 ? `${sec.non_producing}` : ''}
                      </div>
                    </div>
                    <div style={{ width: '45px', fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', textAlign: 'right' }}>
                      {prodPct}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Refinery & Conversion Units */}
      {activeTab === 'refinery' && (
        <div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '14px',
            marginBottom: '18px'
          }}>
            {units.map((unit, idx) => {
              const isSelected = selectedUnit === unit.unit_id;
              return (
                <div 
                  key={idx}
                  onClick={() => setSelectedUnit(isSelected ? null : unit.unit_id)}
                  style={{
                    background: isSelected ? 'rgba(168, 85, 247, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '12px',
                    padding: '16px',
                    border: isSelected ? '1px solid #c084fc' : '1px solid rgba(255, 255, 255, 0.07)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        padding: '2px 7px',
                        background: 'rgba(168, 85, 247, 0.2)',
                        color: '#c084fc',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        fontFamily: 'JetBrains Mono, monospace'
                      }}>
                        {unit.unit_id}
                      </span>
                      <strong style={{ fontSize: '0.92rem', color: '#ffffff' }}>{unit.name}</strong>
                    </div>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      background: 'rgba(16, 185, 129, 0.15)',
                      color: '#34d399'
                    }}>
                      {unit.status || 'Normal'}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '10px' }}>
                    Category: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{unit.type}</span>
                  </div>

                  {/* Telemetry specs grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', marginBottom: '10px' }}>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Design Capacity</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f59e0b' }}>{unit.capacity}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Operating Temp</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fb923c' }}>{unit.operating_temp}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Current Load</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#34d399' }}>{unit.current_load}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Pressure</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#c084fc' }}>{unit.operating_press}</div>
                    </div>
                  </div>

                  {unit.catalyst && (
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginBottom: '8px' }}>
                      Catalyst: <strong style={{ color: '#cbd5e1' }}>{unit.catalyst}</strong>
                    </div>
                  )}

                  {/* Output fractions pills */}
                  {unit.products && unit.products.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                      {unit.products.map((p, pIdx) => (
                        <span key={pIdx} style={{
                          fontSize: '0.65rem',
                          background: 'rgba(255, 255, 255, 0.05)',
                          color: '#cbd5e1',
                          padding: '2px 6px',
                          borderRadius: '4px'
                        }}>
                          {p}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Ask unit deep dive */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePromptClick(`Explain the ${unit.name} (${unit.unit_id}) process, catalyst, and operating conditions.`);
                    }}
                    style={{
                      width: '100%',
                      marginTop: '10px',
                      padding: '5px',
                      background: 'rgba(168, 85, 247, 0.1)',
                      border: '1px solid rgba(168, 85, 247, 0.25)',
                      borderRadius: '6px',
                      color: '#c084fc',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px'
                    }}
                  >
                    Deep Dive Technical Specs <ChevronRight size={12} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 3: Product Yields */}
      {activeTab === 'yields' && (
        <div>
          {/* Stacked Proportional Bar */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '12px',
            padding: '18px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            marginBottom: '18px'
          }}>
            <h5 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', margin: '0 0 14px 0', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Refinery Crude Conversion Yields (207,500 bpd Input)
            </h5>

            <div style={{ display: 'flex', height: '24px', borderRadius: '6px', overflow: 'hidden', marginBottom: '14px' }}>
              {yields.map((y, idx) => (
                <div 
                  key={idx}
                  style={{
                    width: `${y.pct}%`,
                    background: y.color || '#f59e0b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: '#000'
                  }}
                  title={`${y.product}: ${y.pct}% (${y.bpd.toLocaleString()} bpd)`}
                >
                  {y.pct >= 10 ? `${y.pct}%` : ''}
                </div>
              ))}
            </div>

            {/* Yield cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
              {yields.map((y, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '8px',
                  padding: '12px',
                  borderLeft: `4px solid ${y.color || '#f59e0b'}`
                }}>
                  <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>{y.product}</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', margin: '4px 0' }}>
                    {y.pct}%
                  </div>
                  <div style={{ fontSize: '0.72rem', color: y.color || '#f59e0b', fontWeight: 600 }}>
                    {y.bpd?.toLocaleString()} bpd
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: HSE & Compliance Rules */}
      {activeTab === 'hse' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '14px',
          marginBottom: '16px'
        }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', padding: '16px', border: '1px solid rgba(255, 255, 255, 0.07)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: '#f59e0b' }}>
              <ShieldAlert size={16} />
              <strong style={{ fontSize: '0.9rem', color: '#fff' }}>SOP-SR §7 False Positive Filter</strong>
            </div>
            <p style={{ fontSize: '0.76rem', color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
              Autonomous detection exclusion actively filters unconfirmed mud, rainwater, and optical shadow artifacts confirmed via context correction notes.
            </p>
            <div style={{ marginTop: '10px', padding: '8px', background: 'rgba(56, 189, 248, 0.08)', borderRadius: '6px', fontSize: '0.72rem', color: '#f59e0b' }}>
              Active Ground Truth: 17 false positives completely isolated from official spill counts.
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', padding: '16px', border: '1px solid rgba(255, 255, 255, 0.07)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: '#fb923c' }}>
              <AlertTriangle size={16} />
              <strong style={{ fontSize: '0.9rem', color: '#fff' }}>SR-02 Containment Protocol</strong>
            </div>
            <p style={{ fontSize: '0.76rem', color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
              All reportable and major spills (&gt;= 1.0 bbl) must have source stopped and contained within 4.0 hours of discovery.
            </p>
            <div style={{ marginTop: '10px', padding: '8px', background: 'rgba(251, 146, 60, 0.08)', borderRadius: '6px', fontSize: '0.72rem', color: '#fb923c' }}>
              Compliance Rating: 98.4% within benchmark window.
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', padding: '16px', border: '1px solid rgba(255, 255, 255, 0.07)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: '#34d399' }}>
              <CheckCircle2 size={16} />
              <strong style={{ fontSize: '0.9rem', color: '#fff' }}>Flare & Emissions Compliance</strong>
            </div>
            <p style={{ fontSize: '0.76rem', color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
              Flare gas recovery systems and Claus sulfur units maintain 99.85% sulfur recovery efficiency with zero permit exceedances.
            </p>
            <div style={{ marginTop: '10px', padding: '8px', background: 'rgba(52, 211, 153, 0.08)', borderRadius: '6px', fontSize: '0.72rem', color: '#34d399' }}>
              EPA Subpart Ja Compliant · 0 Flaring Events YTD.
            </div>
          </div>
        </div>
      )}

      {/* Actionable Prompt Pill Strip (Google GenUI signature interactive buttons) */}
      <div style={{
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
          <Zap size={13} color="#f59e0b" />
          Interactive Follow-up Exploration (Click to Prompt Copilot):
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {actions.map((act, idx) => (
            <button
              key={idx}
              onClick={() => handlePromptClick(act.prompt)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#e2e8f0',
                padding: '6px 12px',
                borderRadius: '999px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)';
                e.currentTarget.style.borderColor = '#f59e0b';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.3)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <span style={{ color: '#f59e0b' }}>✦</span>
              {act.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
