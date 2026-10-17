import React from 'react';
import { X, FileText, CheckCircle, ExternalLink, ShieldAlert, Wrench, Thermometer } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function CitationDrawer({ citation, onClose }) {
  if (!citation) return null;

  const getTypeIcon = (type) => {
    switch (type) {
      case 'inspection':
        return <Thermometer size={16} color="#f59e0b" />;
      case 'maintenance':
        return <Wrench size={16} color="#f59e0b" />;
      case 'manual':
        return <FileText size={16} color="#34d399" />;
      case 'regulatory':
        return <ShieldAlert size={16} color="#f43f5e" />;
      default:
        return <FileText size={16} color="#a855f7" />;
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      justifyContent: 'flex-end',
      zIndex: 9999,
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '560px',
        height: '100%',
        background: '#0f172a',
        borderLeft: '1px solid rgba(56, 189, 248, 0.3)',
        boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.8)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '18px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(15, 23, 42, 0.95)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              {getTypeIcon(citation.type)}
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>
                {citation.category || 'Source Evidence Grounding'}
              </div>
              <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#ffffff', margin: '2px 0 0 0' }}>
                {citation.id}
              </h4>
            </div>
          </div>

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
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{
          padding: '20px',
          overflowY: 'auto',
          flex: 1,
          color: '#cbd5e1',
          fontSize: '0.85rem',
          lineHeight: 1.6
        }}>
          <div style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '10px',
            padding: '14px',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            marginBottom: '16px'
          }}>
            <h5 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f59e0b', margin: '0 0 8px 0' }}>
              {citation.title}
            </h5>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
              Verified ground-truth record from the primary asset registry.
            </div>
          </div>

          {/* Excerpt Markdown */}
          <div className="citation-markdown-body" style={{
            background: 'rgba(255, 255, 255, 0.02)',
            padding: '16px',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {citation.content || 'No text content available.'}
            </ReactMarkdown>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(15, 23, 42, 0.95)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.74rem',
          color: '#64748b'
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle size={14} color="#10b981" />
            Verified Source Grounding
          </span>
          <button
            onClick={onClose}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#f59e0b',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
