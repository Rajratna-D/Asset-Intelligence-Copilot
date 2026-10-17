import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Bot, 
  User, 
  Send, 
  RefreshCw, 
  AlertTriangle, 
  Flame, 
  Sparkles, 
  RotateCcw, 
  Info, 
  ArrowUp, 
  Compass,
  ShieldCheck, 
  ShieldAlert, 
  X, 
  CheckCircle2,
  FileText,
  ChevronDown,
  ChevronRight,
  Database,
  Sliders,
  Check
} from 'lucide-react';

import StatusCard from './components/StatusCard';
import VisualTable from './components/VisualTable';
import LineChart from './components/LineChart';
import BarChart from './components/BarChart';
import HeatmapView from './components/HeatmapView';
import MapView from './components/MapView';
import GenerativeDashboard from './components/GenerativeDashboard';
import CitationDrawer from './components/CitationDrawer';
import MemoryInspector from './components/MemoryInspector';
import GuardrailsModal from './components/GuardrailsModal';

// Comprehensive Operational Personas (Matching actual SQLite database users)
const ALL_PERSONAS = [
  { id: 'U-201', name: 'Michael Turner', role: 'Production supervisor', dept: 'Northeast Fleet', initials: 'MT' },
  { id: 'U-101', name: 'Emily Carter', role: 'Production supervisor', dept: 'Southwest Fleet', initials: 'EC' },
  { id: 'U-104', name: 'Ryan Brooks', role: 'Field inspector', dept: 'Drone & Thermal Inspections', initials: 'RB' },
  { id: 'U-202', name: 'Jessica Reed', role: 'Field inspector', dept: 'Northeast Telemetry', initials: 'JR' },
  { id: 'U-103', name: 'Sarah Mitchell', role: 'Field inspector', dept: 'Southwest Telemetry', initials: 'SM' },
  { id: 'U-203', name: 'Ashley Bennett', role: 'Field inspector', dept: 'Northeast Audits', initials: 'AB' },
  { id: 'U-102', name: 'Jake Morales', role: 'Field operator', dept: 'Wellhead & Gathering', initials: 'JM' },
  { id: 'U-204', name: 'Tyler Hughes', role: 'Field operator', dept: 'Field Operations', initials: 'TH' },
  { id: 'U-301', name: 'Robert Hayes', role: 'Maintenance lead', dept: 'Workover & Overhaul', initials: 'RH' },
  { id: 'U-302', name: 'Daniel Foster', role: 'Maintenance technician', dept: 'Pump Jack Systems', initials: 'DF' },
  { id: 'U-303', name: 'Kevin Price', role: 'Maintenance technician', dept: 'Flowlines & Valves', initials: 'KP' },
  { id: 'U-304', name: 'Brian Coleman', role: 'Maintenance technician', dept: 'Telemetry Sensors', initials: 'BC' },
  { id: 'U-305', name: 'Megan Ward', role: 'Maintenance technician', dept: 'Downhole Repair', initials: 'MW' },
  { id: 'U-401', name: 'Laura Simmons', role: 'HSE & Regulatory lead', dept: 'Environmental Compliance', initials: 'LS' },
  { id: 'U-402', name: 'Chris Dalton', role: 'HSE officer', dept: 'Spill Containment', initials: 'CD' }
];

// Helper to generate dynamic multi-modal pipeline steps contextual to current topic/asset
const getPipelineSteps = (context) => {
  const { type, entity, label } = context || { type: 'well', entity: 'WELL-0001', label: 'WELL-0001' };

  if (type === 'well') {
    return [
      { 
        id: 1, 
        label: 'Text answer', 
        icon: '≡', 
        title: `Operational status and overview for ${entity}`,
        query: `Is ${entity} producing oil right now? When was it last inspected, and by whom?`
      },
      { 
        id: 2, 
        label: 'Table', 
        icon: '⊞', 
        title: `Telemetry and repair records table for ${entity}`,
        query: `Show inspection telemetry and maintenance records for ${entity} in a table.`
      },
      { 
        id: 3, 
        label: 'Trend chart', 
        icon: '📈', 
        title: `13-week temperature line chart for ${entity}`,
        query: `Show the 13-week temperature history for ${entity} as a line chart.`
      },
      { 
        id: 4, 
        label: 'Spill heatmap', 
        icon: '▦', 
        title: `Spill containment and history for ${entity}`,
        query: `How many oil spills has ${entity} had in the last 4 years, and was containment timely?`
      },
      { 
        id: 5, 
        label: 'Generative dashboard', 
        icon: '✨', 
        title: `Operations dashboard for ${entity}`,
        query: `Make an operations dashboard for each sector and refinery.`
      }
    ];
  }

  if (type === 'area') {
    return [
      { 
        id: 1, 
        label: 'Text answer', 
        icon: '≡', 
        title: `Overview and well health in ${entity}`,
        query: `Which wells in ${entity} are not producing oil right now, and why?`
      },
      { 
        id: 2, 
        label: 'Table', 
        icon: '⊞', 
        title: `Tabular fleet breakdown for ${entity}`,
        query: `Which wells in ${entity} are not producing oil right now, and why? Show them in a table.`
      },
      { 
        id: 3, 
        label: 'Trend chart', 
        icon: '📈', 
        title: `Temperature trends in ${entity}`,
        query: `Show temperature series and production trends for ${entity}.`
      },
      { 
        id: 4, 
        label: 'Spill heatmap', 
        icon: '▦', 
        title: `Spill map and leak history in ${entity}`,
        query: `Show on a map every well in ${entity} with a real spill in the last 90 days.`
      },
      { 
        id: 5, 
        label: 'Generative dashboard', 
        icon: '✨', 
        title: `Operations dashboard for ${entity}`,
        query: `Make an operations dashboard for each sector and refinery.`
      }
    ];
  }

  if (type === 'spills') {
    return [
      { 
        id: 1, 
        label: 'Text answer', 
        icon: '≡', 
        title: `2026 spill incidents summary`,
        query: `What are the reportable oil spills recorded across field sectors in 2026?`
      },
      { 
        id: 2, 
        label: 'Table', 
        icon: '⊞', 
        title: `Spill records and containment log table`,
        query: `Show all 2026 spill incidents, estimated volumes, and containment times in a table.`
      },
      { 
        id: 3, 
        label: 'Trend chart', 
        icon: '📈', 
        title: `Monthly spill volume trends`,
        query: `Show the monthly spill trend and volume chart for 2026.`
      },
      { 
        id: 4, 
        label: 'Spill heatmap', 
        icon: '▦', 
        title: `Spatial heatmap of 2026 spills`,
        query: `Show a heatmap of 2026 spills by geographic area and month.`
      },
      { 
        id: 5, 
        label: 'Generative dashboard', 
        icon: '✨', 
        title: `Operations dashboard`,
        query: `Make an operations dashboard for each sector and refinery.`
      }
    ];
  }

  // Generic query fallback
  return [
    { 
      id: 1, 
      label: 'Text answer', 
      icon: '≡', 
      title: `Operational text answer for: "${label}"`,
      query: entity
    },
    { 
      id: 2, 
      label: 'Table', 
      icon: '⊞', 
      title: `Detailed tabular records for: "${label}"`,
      query: `Show the records and telemetry related to: "${entity}" in a table.`
    },
    { 
      id: 3, 
      label: 'Trend chart', 
      icon: '📈', 
      title: `Operational trends related to: "${label}"`,
      query: `Show trends and metric history related to: "${entity}" as a chart.`
    },
    { 
      id: 4, 
      label: 'Spill heatmap', 
      icon: '▦', 
      title: `Spill and environmental map`,
      query: `Show a heatmap of 2026 spills by geographic area and month.`
    },
    { 
      id: 5, 
      label: 'Generative dashboard', 
      icon: '✨', 
      title: `Operations dashboard`,
      query: `Make an operations dashboard for each sector and refinery.`
    }
  ];
};

export default function App() {
  const [sessionId, setSessionId] = useState(() => 'sess_' + Math.random().toString(36).substr(2, 9));
  const [userId, setUserId] = useState('U-201');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // Interactive Modals
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [showMemoryInspector, setShowMemoryInspector] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [citationLoading, setCitationLoading] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [activeStep, setActiveStep] = useState(null);
  const [expandedSteps, setExpandedSteps] = useState({});

  const [securityLogs, setSecurityLogs] = useState([]);
  const [securityStats, setSecurityStats] = useState(null);

  const latestMessageRef = useRef(null);
  const inputRef = useRef(null);
  const userDropdownRef = useRef(null);

  const currentUser = ALL_PERSONAS.find(p => p.id === userId) || ALL_PERSONAS[0];

  // Extract currently discussed topic, well, area, or question context
  const getCurrentContext = () => {
    if (!messages || messages.length === 0) {
      return { type: 'well', entity: 'WELL-0001', label: 'WELL-0001' };
    }

    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      const text = (msg.content || '') + ' ' + (msg.entities_discussed || []).join(' ');

      // 1. Check for specific well ID (WELL-XXXX)
      const wellMatch = text.match(/\bWELL-\d{4}\b/i);
      if (wellMatch) {
        const wid = wellMatch[0].toUpperCase();
        return { type: 'well', entity: wid, label: wid };
      }

      // 2. Check for Area / Block / Sector
      if (/block\s*8|ne-?08|northeast\s*block\s*8/i.test(text)) {
        return { type: 'area', entity: 'Northeast Block 8', label: 'NE Block 8' };
      }
      if (/block\s*24|sw-?24|southwest\s*block\s*24|southwest\s*sector\s*24/i.test(text)) {
        return { type: 'area', entity: 'Southwest Block 24', label: 'SW Block 24' };
      }
      if (/block\s*23|sw-?23|southwest\s*block\s*23|southwest\s*sector\s*23/i.test(text)) {
        return { type: 'area', entity: 'Southwest Block 23', label: 'SW Block 23' };
      }
      if (/block\s*7|nw-?07|northwest\s*block\s*7/i.test(text)) {
        return { type: 'area', entity: 'Northwest Block 7', label: 'NW Block 7' };
      }

      // 3. Check for Spills / HSE
      if (/spill|leak|containment|hse|environmental/i.test(text)) {
        return { type: 'spills', entity: '2026 Spills', label: '2026 Spills' };
      }
    }

    // 4. Fallback to latest user question
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMsg && lastUserMsg.content) {
      const q = lastUserMsg.content.trim();
      return { 
        type: 'query', 
        entity: q, 
        label: q.length > 25 ? q.slice(0, 22) + '...' : q 
      };
    }

    return { type: 'well', entity: 'WELL-0001', label: 'WELL-0001' };
  };

  const activeContext = getCurrentContext();
  const pipelineSteps = getPipelineSteps(activeContext);

  // Fetch security audit data
  const fetchSecurityData = async () => {
    try {
      const [logsRes, statsRes] = await Promise.all([
        fetch('/api/security/audit-logs?limit=20'),
        fetch('/api/security/stats')
      ]);
      if (logsRes.ok) {
        const d = await logsRes.json();
        setSecurityLogs(d.logs || []);
      }
      if (statsRes.ok) {
        const s = await statsRes.json();
        setSecurityStats(s);
      }
    } catch (e) {
      console.error("Failed to load security audit data", e);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (userDropdownRef.current && !userDropdownRef.current.contains(event.target)) {
        setShowUserDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Auto-scroll chat to bring the newest response into view
  useEffect(() => {
    if (messages.length > 0) {
      latestMessageRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [messages, isSending]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Click citation to fetch full record and open drawer
  const handleCitationClick = async (citationId) => {
    if (!citationId) return;
    setCitationLoading(true);
    try {
      const clean = citationId.replace(/[\[\]\(\)]/g, '').trim();
      const res = await fetch(`/api/citation/preview?citation_id=${encodeURIComponent(clean)}`);
      if (res.ok) {
        const citData = await res.json();
        setSelectedCitation(citData);
      } else {
        setSelectedCitation({
          id: clean,
          title: `Document ${clean}`,
          category: 'Fleet Knowledge Base',
          type: 'general',
          content: `Citation reference for ${clean}.`
        });
      }
    } catch (e) {
      console.error("Failed to load citation", e);
    } finally {
      setCitationLoading(false);
    }
  };

  const handleSendMessage = async (textToSend, stepId = null) => {
    const query = (textToSend || input).trim();
    if (!query || isSending) return;

    if (stepId) {
      setActiveStep(stepId);
    }

    const userMsg = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsSending(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          message: query
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const copilotData = await res.json();

      // Determine appropriate rationale text based on visual type
      let rationale = 'A yes/no question about one well, so I answered in text. No visual needed.';
      if (copilotData.visual_type === 'table') {
        rationale = 'Extracted multi-asset telemetry and cross-referenced with maintenance records in a table.';
      } else if (copilotData.visual_type === 'line_chart') {
        rationale = 'Aggregated weekly temperature time-series against the ambient baseline.';
      } else if (copilotData.visual_type === 'heatmap') {
        rationale = 'Synthesized 2026 spatial spill distribution matrix by area and month.';
      } else if (copilotData.visual_type === 'card' || copilotData.visual_type === 'status_card') {
        rationale = 'Calculated physical operating status from thermal sensor telemetry.';
      } else if (copilotData.visual_type === 'generative_dashboard') {
        rationale = 'Synthesized live multi-tier operational telemetry across upstream sectors and downstream refinery units.';
      }

      const copilotMsg = {
        id: 'msg_' + Date.now() + '_ai',
        role: 'copilot',
        content: copilotData.answer_markdown || copilotData.message || '',
        visual_component: copilotData.visual_type || copilotData.visual_component,
        visual_data: copilotData.visual_data,
        citations: copilotData.citations || [],
        rationale: rationale,
        tools_called: copilotData.tools_called || ['truth_engine_audit', 'thermal_delta_calc', 'fts5_docs_search'],
        conflict_warning: copilotData.conflict_warning,
        entities_discussed: copilotData.entities_discussed || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, copilotMsg]);
      if (stepId) {
        setActiveStep(stepId);
      }
    } catch (err) {
      const errorMsg = {
        id: 'msg_' + Date.now() + '_err',
        role: 'copilot',
        content: `⚠️ **Error processing request:** ${err.message}. Please check connection.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
    setSessionId('sess_' + Math.random().toString(36).substr(2, 9));
    setActiveStep(1);
    inputRef.current?.focus();
  };

  const toggleAccordion = (msgId) => {
    setExpandedSteps(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  // Render Visual Component dynamically inside message
  const renderVisual = (componentType, data) => {
    if (!componentType || !data) return null;
    switch (componentType) {
      case 'generative_dashboard':
        return <GenerativeDashboard data={data} onActionClick={handleSendMessage} />;
      case 'status_card':
      case 'card':
        return <StatusCard data={data} />;
      case 'table':
        return <VisualTable data={data} />;
      case 'line_chart':
        return <LineChart data={data} />;
      case 'bar_chart':
        return <BarChart data={data} />;
      case 'heatmap':
        return <HeatmapView data={data} />;
      case 'map':
        return <MapView data={data} />;
      default:
        return null;
    }
  };


  return (
    <div className="copilot-app">
      {/* Top Header - Matching Mentor UI exactly */}
      <header className="mentor-header">
        {/* Left: Brand & Prototype Subtitle */}
        <div className="mentor-brand">
          <div className="mentor-brand-icon">
            <Flame size={17} color="#f59e0b" />
          </div>
          <div>
            <div className="mentor-brand-title">Asset Intelligence Copilot</div>
            <div className="mentor-brand-subtitle">Prototype · sample data as of 16 Oct 2026</div>
          </div>
        </div>

        {/* Center: Stepper Multi-Modal Lens Pipeline */}
        <div className="mentor-stepper">
          {pipelineSteps.map((step, idx) => {
            const isActive = activeStep === step.id;
            return (
              <React.Fragment key={step.id}>
                <button
                  className={`stepper-pill ${isActive ? 'active' : ''}`}
                  onClick={() => handleSendMessage(step.query, step.id)}
                  title={step.title}
                >
                  {isActive ? (
                    <span className="stepper-check"><Check size={12} strokeWidth={3} /></span>
                  ) : (
                    <span className="stepper-number">{step.id}</span>
                  )}
                  <span className="stepper-icon">{step.icon}</span>
                  <span className="stepper-label">{step.label}</span>
                </button>
                {idx < pipelineSteps.length - 1 && <span className="stepper-divider">—</span>}
              </React.Fragment>
            );
          })}
        </div>

        {/* Right: Actions & User Avatar Profile */}
        <div className="mentor-header-right">
          {/* Memory & Conflict Inspector Button */}
          <button 
            className="mentor-action-btn"
            onClick={() => setShowMemoryInspector(true)}
            title="Inspect Part B Multi-User Memory, Shared Feedback & Conflict Resolution"
          >
            <Database size={13} color="#f59e0b" />
            <span>Memory & Conflicts</span>
          </button>

          {/* Security Guardrails Button */}
          <button 
            className="mentor-action-btn"
            onClick={() => {
              fetchSecurityData();
              setShowSecurityModal(true);
            }}
            title="Active Security Guardrails Audit"
          >
            <ShieldCheck size={13} color="#10b981" />
            <span>Guardrails</span>
          </button>

          {/* New Chat Button */}
          <button 
            className="mentor-action-btn new-chat-btn"
            onClick={handleResetChat} 
            title="Start New Conversation"
          >
            <RotateCcw size={13} />
            <span>New chat</span>
          </button>

          {/* User Profile Pill & Dropdown Switcher */}
          <div className="user-profile-container" ref={userDropdownRef}>
            <div 
              className="user-profile-pill"
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              title="Switch Active Operating Persona"
            >
              <div className="user-avatar-circle">
                {currentUser.initials}
              </div>
              <div className="user-info-text">
                <div className="user-display-name">{currentUser.name}</div>
                <div className="user-display-role">{currentUser.role.replace('_', ' ')}</div>
              </div>
              <ChevronDown size={13} color="#94a3b8" />
            </div>

            {/* Dropdown Menu for all 15 users */}
            {showUserDropdown && (
              <div className="user-dropdown-menu">
                <div className="dropdown-header">
                  Select Active Persona (Multi-User Memory Testing)
                </div>
                <div className="dropdown-scroll-list">
                  {ALL_PERSONAS.map(u => (
                    <div
                      key={u.id}
                      className={`dropdown-user-item ${u.id === userId ? 'active' : ''}`}
                      onClick={() => {
                        setUserId(u.id);
                        setShowUserDropdown(false);
                        setMessages([]);
                        setSessionId('sess_' + Math.random().toString(36).substr(2, 9));
                      }}
                    >
                      <div className="item-avatar">{u.initials}</div>
                      <div className="item-details">
                        <div className="item-name">{u.name}</div>
                        <div className="item-sub">{u.role.replace('_', ' ')} · {u.dept}</div>
                      </div>
                      {u.id === userId && <Check size={14} color="#f59e0b" />}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Single-Window Copilot Feed */}
      <main className="copilot-body">
        <div className="copilot-feed">
          {messages.length === 0 ? (
            /* Empty State Hero with Suggestion Chips */
            <div className="copilot-empty-hero">
              <div className="hero-avatar">
                <Flame size={34} color="#f59e0b" />
              </div>
              <h1 className="hero-title">Asset Intelligence Copilot</h1>
              <p className="hero-desc">
                Autonomous Permian Basin operations intelligence across 200 monitored wellheads and downstream refinery conversion trains.
              </p>

              <div className="suggestion-grid">
                <button 
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Is WELL-0001 producing oil right now? When was it last inspected, and by whom?", 1)}
                  style={{ border: '1px solid rgba(56, 189, 248, 0.4)' }}
                >
                  <div className="suggestion-title">⚡ Step 1: Operational Truth</div>
                  <div className="suggestion-query">"Is WELL-0001 producing oil right now?"</div>
                </button>

                <button 
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.", 2)}
                >
                  <div className="suggestion-title">📋 Step 2: Area Status Table</div>
                  <div className="suggestion-query">"Which wells in Northeast Block 8 are not producing?"</div>
                </button>

                <button 
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Show the 13-week temperature history for WELL-0001 as a line chart.", 3)}
                >
                  <div className="suggestion-title">📈 Step 3: Temperature Trend</div>
                  <div className="suggestion-query">"Show 13-week temperature history for WELL-0001."</div>
                </button>

                <button 
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Show a heatmap of 2026 spills by geographic area and month.", 4)}
                >
                  <div className="suggestion-title">🗺️ Step 4: Spill Heatmap</div>
                  <div className="suggestion-query">"Show heatmap of 2026 spills by area & month."</div>
                </button>

                <button 
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Make an operations dashboard for each sector and refinery.", 5)}
                  style={{ background: 'linear-gradient(180deg, rgba(14, 165, 233, 0.1) 0%, rgba(15, 23, 42, 0.6) 100%)' }}
                >
                  <div className="suggestion-title" style={{ color: '#f59e0b' }}>✨ Step 5: Generative Dashboard</div>
                  <div className="suggestion-query">"Make an operations dashboard for each sector and refinery."</div>
                </button>

                <button 
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Explain the refinery crude distillation unit process and how fractions are separated.")}
                >
                  <div className="suggestion-title">🏭 Refinery Intelligence</div>
                  <div className="suggestion-query">"Explain refinery crude distillation unit process."</div>
                </button>
              </div>
            </div>
          ) : (
            /* Chat Turns */
            <div className="messages-stream">
              {messages.map((msg, idx) => (
                <div 
                  key={msg.id} 
                  className={`message-turn ${msg.role}`}
                  ref={idx === messages.length - 1 ? latestMessageRef : null}
                >
                  {msg.role === 'user' ? (
                    /* User Query Bubble (Matching Screenshot) */
                    <div className="user-message-wrapper">
                      <div className="user-bubble">
                        {msg.content}
                      </div>
                      <div className="user-sent-indicator">
                        <Check size={11} color="#10b981" />
                        <span>Sent</span>
                      </div>
                    </div>
                  ) : (
                    /* Copilot Response (Matching Screenshot exactly) */
                    <div className="copilot-message-wrapper">
                      {/* Copilot Header */}
                      <div className="copilot-msg-header">
                        <div className="copilot-avatar-box">
                          <Flame size={15} color="#f59e0b" />
                        </div>
                        <div className="copilot-header-info">
                          <div className="copilot-title-row">
                            <span className="copilot-name">Copilot</span>
                            <span className="copilot-badge">
                              {msg.visual_component === 'table' ? '⊞ Table' :
                               msg.visual_component === 'line_chart' ? '📈 Trend chart' :
                               msg.visual_component === 'heatmap' ? '▦ Spill heatmap' :
                               msg.visual_component === 'generative_dashboard' ? '✨ Generative UI' :
                               msg.visual_component === 'status_card' || msg.visual_component === 'card' ? '⚡ Status card' :
                               '≡ Text'}
                            </span>
                          </div>
                          {msg.rationale && (
                            <div className="copilot-rationale">
                              {msg.rationale}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Expandable Reasoning / Steps Accordion */}
                      <div className="reasoning-accordion-box">
                        <button 
                          className="accordion-toggle-btn"
                          onClick={() => toggleAccordion(msg.id)}
                        >
                          <ChevronRight 
                            size={13} 
                            style={{ 
                              transform: expandedSteps[msg.id] ? 'rotate(90deg)' : 'none',
                              transition: 'transform 0.2s ease'
                            }} 
                          />
                          <span>Checked {msg.citations?.length || 4} sources · {msg.tools_called?.length || 3} steps</span>
                        </button>

                        {expandedSteps[msg.id] && (
                          <div className="accordion-content">
                            <div className="reasoning-step-item">
                              <span className="step-dot">1</span>
                              <span>Calculated physical operational truth from thermal sensor delta telemetry</span>
                            </div>
                            <div className="reasoning-step-item">
                              <span className="step-dot">2</span>
                              <span>FTS5 BM25 search across operating manuals and regulatory SOP compliance protocols</span>
                            </div>
                            <div className="reasoning-step-item">
                              <span className="step-dot">3</span>
                              <span>Cross-checked stale database status and evaluated context notes for scheduled workovers</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Conflict Warning Banner if triggered */}
                      {msg.conflict_warning && (
                        <div className="conflict-warning-card">
                          <AlertTriangle size={15} color="#f59e0b" />
                          <div>
                            <strong>Operational Conflict Flagged:</strong> {msg.conflict_warning}
                          </div>
                        </div>
                      )}

                      {/* Formatted Markdown Content */}
                      <div className="copilot-content-body">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>

                      {/* Visual Component Render */}
                      {renderVisual(msg.visual_component, msg.visual_data)}

                      {/* Sources Footer with Clickable Interactive Pills */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="sources-footer">
                          <span className="sources-label">Sources</span>
                          <div className="sources-pills-row">
                            {msg.citations.map((cit, cIdx) => (
                              <button
                                key={cIdx}
                                className="source-citation-pill"
                                onClick={() => handleCitationClick(cit)}
                                title={`Click to preview verified grounding document: ${cit}`}
                              >
                                <FileText size={11} />
                                <span>{cit}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {isSending && (
                <div className="copilot-message-wrapper is-loading">
                  <div className="copilot-msg-header">
                    <div className="copilot-avatar-box">
                      <Flame size={15} color="#f59e0b" />
                    </div>
                    <div className="copilot-header-info">
                      <span className="copilot-name">Copilot</span>
                      <div className="copilot-rationale">Auditing telemetry sensors & synthesizing response...</div>
                    </div>
                  </div>
                  <div className="loading-shimmer-box">
                    <div className="shimmer-line line-1"></div>
                    <div className="shimmer-line line-2"></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Bottom Input Area with Stepper Guidance */}
      <footer className="mentor-footer">
        <form 
          className="mentor-input-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <input
            ref={inputRef}
            type="text"
            className="mentor-text-input"
            placeholder="Ask about wells, areas, spills or repairs"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isSending}
          />
          <button 
            type="submit" 
            className="mentor-send-btn"
            disabled={!input.trim() || isSending}
            title="Send query"
          >
            <ArrowUp size={16} />
          </button>
        </form>

        {/* Guided Step Helper Text */}
        <div className="mentor-helper-text">
          {activeStep === null ? (
            <span>
              Next: click <button onClick={() => handleSendMessage(pipelineSteps[0].query, 1)} className="helper-link">1. Text answer</button> at the top to explore {activeContext.label}.
            </span>
          ) : activeStep < pipelineSteps.length ? (
            <span>
              Next: click <button onClick={() => handleSendMessage(pipelineSteps[activeStep].query, activeStep + 1)} className="helper-link">{pipelineSteps[activeStep].id}. {pipelineSteps[activeStep].label}</button> at the top to see {activeContext.label} as a {pipelineSteps[activeStep].label.toLowerCase()} in this chat.
            </span>
          ) : (
            <span>
              All representations explored for <strong style={{ color: '#fbbf24' }}>{activeContext.label}</strong>. Ask any follow-up question below or switch steps above.
            </span>
          )}
        </div>
      </footer>

      {/* Interactive Citation Drawer */}
      {selectedCitation && (
        <CitationDrawer 
          citation={selectedCitation} 
          onClose={() => setSelectedCitation(null)} 
        />
      )}

      {/* Memory & Conflict Inspector Modal */}
      {showMemoryInspector && (
        <MemoryInspector 
          activeUserId={userId} 
          onClose={() => setShowMemoryInspector(false)}
        />
      )}

      {/* Security Guardrails Audit Modal */}
      {showSecurityModal && (
        <GuardrailsModal onClose={() => setShowSecurityModal(false)} />
      )}
    </div>
  );
}
