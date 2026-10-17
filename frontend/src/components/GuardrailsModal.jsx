import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  X, 
  Lock, 
  AlertTriangle, 
  Terminal, 
  CheckCircle2, 
  RefreshCw,
  EyeOff,
  DatabaseZap
} from 'lucide-react';

export default function GuardrailsModal({ onClose }) {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [logsRes, statsRes] = await Promise.all([
        fetch('/api/security/audit-logs?limit=50'),
        fetch('/api/security/stats')
      ]);
      if (logsRes.ok) {
        const d = await logsRes.json();
        setLogs(d.logs || []);
      }
      if (statsRes.ok) {
        const s = await statsRes.json();
        setStats(s);
      }
    } catch (e) {
      console.error("Failed to load security audit data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalEvents = stats?.total_security_events || logs.length || 0;
  const blockedInjections = stats?.event_breakdown?.PROMPT_INJECTION_BLOCKED || 0;
  const dataCorrections = stats?.event_breakdown?.DATA_CORRECTION || 0;
  const operationalNotes = stats?.event_breakdown?.OPERATIONAL_NOTE || 0;

  return (
    <div 
      className="guardrails-modal-overlay"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 10, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div 
        className="guardrails-modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '920px',
          maxHeight: '88vh',
          backgroundColor: '#12161f',
          border: '1px solid #2a3241',
          borderRadius: '16px',
          boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 30px rgba(245, 158, 11, 0.1)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'modalFadeIn 0.2s ease-out'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid #1e2638',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(180deg, #181f2c 0%, #12161f 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <ShieldCheck size={20} color="#f59e0b" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Enterprise Security Guardrails & Audit System
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
                OWASP LLM Top 10 Protection · Immutable SQLite Audit Trail · Zero-Width Evasion Defense
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={fetchData}
              disabled={loading}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid #2a3241',
                borderRadius: '8px',
                padding: '6px 12px',
                color: '#cbd5e1',
                fontSize: '0.8rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
            <button 
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Modal Scroll Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          {/* 4 Stats Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '14px',
            marginBottom: '22px'
          }}>
            <div style={{
              background: '#161c27',
              border: '1px solid #232c3d',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Total Audited Events
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginTop: '6px' }}>
                {totalEvents}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={12} /> 100% telemetry verified
              </div>
            </div>

            <div style={{
              background: '#161c27',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#fca5a5', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Injections Blocked
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ef4444', marginTop: '6px' }}>
                {blockedInjections}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#f87171', marginTop: '4px' }}>
                Prompt exfiltration & rule bypass
              </div>
            </div>

            <div style={{
              background: '#161c27',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#fcd34d', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Audited State Changes
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f59e0b', marginTop: '6px' }}>
                {dataCorrections + operationalNotes}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#fbbf24', marginTop: '4px' }}>
                L1 truth & broadcast notes
              </div>
            </div>

            <div style={{
              background: '#161c27',
              border: '1px solid #232c3d',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Active Shields
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#10b981', marginTop: '8px' }}>
                NFKD + SQLi Guard
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                Zero-width unicode normalization
              </div>
            </div>
          </div>

          {/* Active Defense Architecture */}
          <div style={{
            background: 'rgba(245, 158, 11, 0.05)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: '12px',
            padding: '14px 18px',
            marginBottom: '22px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Lock size={18} color="#f59e0b" />
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fbbf24' }}>
                  Enterprise Defense-in-Depth Active
                </div>
                <div style={{ fontSize: '0.78rem', color: '#cbd5e1' }}>
                  Requests pass through Pydantic V2 input validation, regex command shields, FTS5 parameterization, and output leak redaction.
                </div>
              </div>
            </div>
            <span style={{
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '4px 10px',
              borderRadius: '20px',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              whiteSpace: 'nowrap'
            }}>
              ENFORCING
            </span>
          </div>

          {/* Table Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '10px'
          }}>
            <h4 style={{
              margin: 0,
              fontSize: '0.85rem',
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontWeight: 700
            }}>
              Immutable Security Audit Trail ({logs.length} entries)
            </h4>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Stored in SQLite <code>security_audit_logs</code>
            </span>
          </div>

          {/* Audit Log Table */}
          <div style={{
            border: '1px solid #232c3d',
            borderRadius: '10px',
            overflow: 'hidden',
            backgroundColor: '#0f131a'
          }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.8rem',
              textAlign: 'left'
            }}>
              <thead>
                <tr style={{
                  backgroundColor: '#161c26',
                  color: '#94a3b8',
                  borderBottom: '1px solid #232c3d'
                }}>
                  <th style={{ padding: '10px 14px' }}>Time (UTC)</th>
                  <th style={{ padding: '10px 14px' }}>Event Type</th>
                  <th style={{ padding: '10px 14px' }}>Severity</th>
                  <th style={{ padding: '10px 14px' }}>User ID</th>
                  <th style={{ padding: '10px 14px' }}>Audit Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                      No security audit events recorded yet.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => {
                    const isCrit = log.severity === 'CRITICAL';
                    const isHigh = log.severity === 'HIGH';
                    const isMed = log.severity === 'MEDIUM';

                    let detailsStr = '';
                    if (typeof log.details === 'object' && log.details !== null) {
                      detailsStr = log.details.reason || log.details.trigger || log.details.description || JSON.stringify(log.details);
                    } else {
                      detailsStr = String(log.details || '');
                    }

                    return (
                      <tr key={log.event_id} style={{
                        borderBottom: '1px solid #1a2230',
                        color: '#e2e8f0'
                      }}>
                        <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: '#94a3b8', fontFamily: 'monospace' }}>
                          {log.timestamp ? log.timestamp.replace('T', ' ').slice(0, 19) : '--'}
                        </td>
                        <td style={{ padding: '10px 14px' }}>
                          <code style={{
                            backgroundColor: 'rgba(255, 255, 255, 0.06)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            color: '#fbbf24',
                            fontSize: '0.75rem'
                          }}>
                            {log.event_type}
                          </code>
                        </td>
                        <td style={{ padding: '10px 14px' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            backgroundColor: isCrit ? 'rgba(239, 68, 68, 0.2)' : isHigh ? 'rgba(245, 158, 11, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                            color: isCrit ? '#f87171' : isHigh ? '#fbbf24' : '#60a5fa',
                            border: `1px solid ${isCrit ? 'rgba(239, 68, 68, 0.4)' : isHigh ? 'rgba(245, 158, 11, 0.4)' : 'rgba(59, 130, 246, 0.4)'}`
                          }}>
                            {log.severity}
                          </span>
                        </td>
                        <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: '#cbd5e1' }}>
                          {log.user_id}
                        </td>
                        <td style={{ 
                          padding: '10px 14px', 
                          maxWidth: '320px', 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis', 
                          whiteSpace: 'nowrap',
                          color: '#94a3b8'
                        }} title={detailsStr}>
                          {detailsStr}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid #1e2638',
          backgroundColor: '#10141d',
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#f59e0b',
              color: '#000000',
              fontWeight: 700,
              border: 'none',
              borderRadius: '8px',
              padding: '8px 18px',
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            Close Shield Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
