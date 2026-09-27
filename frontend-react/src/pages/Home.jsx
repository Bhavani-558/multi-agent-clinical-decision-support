import React, { useState } from 'react';
import {
  Activity,
  PlusCircle,
  Users,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Search,
  ArrowRight,
  TrendingUp,
  Database,
  BrainCircuit,
  FileCheck2
} from 'lucide-react';
import '../styles/home.css';

/**
 * Home Page: Professional Clinical Decision Support System Dashboard.
 */
export default function Home({ onNavigate }) {
  const [searchQuery, setSearchQuery] = useState('');

  // Sample recent clinical analyses
  const recentAnalyses = [
    {
      id: 'AN-9842',
      patientId: 'PT-8042 (Sarah Jenkins)',
      condition: 'Type 2 Diabetes Mellitus',
      riskLevel: 'high',
      riskScore: '84.2%',
      time: '12 mins ago'
    },
    {
      id: 'AN-9841',
      patientId: 'PT-7921 (Robert Sterling)',
      condition: 'Ischemic Heart Disease',
      riskLevel: 'moderate',
      riskScore: '58.7%',
      time: '45 mins ago'
    },
    {
      id: 'AN-9840',
      patientId: 'PT-8104 (Elena Rostova)',
      condition: 'Essential Hypertension',
      riskLevel: 'low',
      riskScore: '14.1%',
      time: '2 hours ago'
    },
    {
      id: 'AN-9839',
      patientId: 'PT-7650 (Marcus Vance)',
      condition: 'Type 2 Diabetes Mellitus',
      riskLevel: 'moderate',
      riskScore: '47.5%',
      time: '3 hours ago'
    }
  ];

  return (
    <div className="home-container">

      {/* 1. Welcome Section & Hero */}
      <section className="welcome-hero">
        <div className="welcome-content">
          <div className="welcome-badge-group">
            <span className="clinical-badge">
              <ShieldCheck size={14} /> Production CDSS Pipeline
            </span>
            <div className="system-status-indicator">
              <span className="status-dot"></span>
              <span>Autonomous Agents Active</span>
            </div>
          </div>

          <h1 className="welcome-title">Welcome, Dr. Miller</h1>
          <h2 className="welcome-subtitle">Clinical Decision Support System (CDSS)</h2>
          <p className="welcome-description">
            Multi-agent diagnostic reasoning framework integrating machine learning risk ensembles,
            explainable AI (SHAP), and biomedical knowledge graphs (Neo4j / PrimeKG) for evidence-backed
            physician recommendations.
          </p>
        </div>

        {/* Quick New Analysis Call To Action */}
        <div className="hero-action-group">
          <button
            type="button"
            className="btn-new-analysis"
            onClick={() => onNavigate && onNavigate('patient-data')}
          >
            <PlusCircle size={18} />
            <span>Launch New Analysis</span>
          </button>
          <span className="hero-meta-note">Target conditions: T2D, Hypertension, Cardiac</span>
        </div>
      </section>

      {/* 2. Clinical Metrics Overview Cards */}
      <section className="metrics-grid" aria-label="Clinical Metrics Overview">
        <div className="metric-card">
          <div className="metric-icon-box cyan">
            <Users size={22} />
          </div>
          <div className="metric-details">
            <span className="metric-label">Active Monitored Patients</span>
            <span className="metric-value">1,248</span>
            <span className="metric-trend">↑ 4.2% from last week</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-box emerald">
            <FileCheck2 size={22} />
          </div>
          <div className="metric-details">
            <span className="metric-label">Screened Today</span>
            <span className="metric-value">42</span>
            <span className="metric-trend">100% agent consensus</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-box amber">
            <AlertTriangle size={22} />
          </div>
          <div className="metric-details">
            <span className="metric-label">High Risk Triage Flags</span>
            <span className="metric-value">3</span>
            <span className="metric-trend" style={{ color: 'var(--status-warning)' }}>
              Requires physician sign-off
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-box indigo">
            <TrendingUp size={22} />
          </div>
          <div className="metric-details">
            <span className="metric-label">Model Diagnostic F1</span>
            <span className="metric-value">96.4%</span>
            <span className="metric-trend">Calibrated ensemble</span>
          </div>
        </div>
      </section>

      {/* 3. Main Dashboard Grid: Patient Overview & Recent Analyses */}
      <section className="dashboard-main-grid">

        {/* Card A: Patient Overview Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <div className="card-title-group">
              <Users className="card-icon" size={20} />
              <h3>Patient Census & Triage Breakdown</h3>
            </div>
            <button
              type="button"
              className="card-action-link"
              onClick={() => onNavigate && onNavigate('patient-data')}
            >
              <span>View All</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div className="patient-overview-content">
            {/* Quick Filter Search */}
            <div className="patient-search-bar">
              <Search size={16} />
              <input
                type="text"
                className="patient-search-input"
                placeholder="Search patient by MRN, Name, or Risk level..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Triage Distribution Bars */}
            <div className="triage-bars-section">
              <div className="triage-bar-item">
                <div className="triage-bar-header">
                  <span>Low Risk (Routine Follow-up)</span>
                  <strong>68% (848 Patients)</strong>
                </div>
                <div className="triage-progress-bg">
                  <div className="triage-progress-fill fill-emerald" style={{ width: '68%' }}></div>
                </div>
              </div>

              <div className="triage-bar-item">
                <div className="triage-bar-header">
                  <span>Moderate Risk (Requires Clinical Monitoring)</span>
                  <strong>24% (302 Patients)</strong>
                </div>
                <div className="triage-progress-bg">
                  <div className="triage-progress-fill fill-amber" style={{ width: '24%' }}></div>
                </div>
              </div>

              <div className="triage-bar-item">
                <div className="triage-bar-header">
                  <span>High Risk (Immediate Decision Escalation)</span>
                  <strong>8% (98 Patients)</strong>
                </div>
                <div className="triage-progress-bg">
                  <div className="triage-progress-fill fill-rose" style={{ width: '8%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Card B: Recent Analyses Card */}
        <div className="dashboard-card">
          <div className="card-header">
            <div className="card-title-group">
              <Clock className="card-icon" size={20} />
              <h3>Recent Analyses & Reports</h3>
            </div>
            <button
              type="button"
              className="card-action-link"
              onClick={() => onNavigate && onNavigate('history')}
            >
              <span>Full History</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div className="analyses-list">
            {recentAnalyses.map((item) => (
              <div key={item.id} className="analysis-item">
                <div className="analysis-main-info">
                  <span className="analysis-patient-tag">{item.patientId}</span>
                  <span className="analysis-disease-type">{item.condition}</span>
                </div>
                <div className="analysis-meta">
                  <span className={`risk-badge ${item.riskLevel}`}>
                    {item.riskScore} Risk
                  </span>
                  <span className="analysis-time">{item.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </section>

      {/* 4. Multi-Agent System Ecosystem Status Cards */}
      <section className="agent-suite-grid" aria-label="Autonomous Multi-Agent Status">
        <div className="agent-suite-card">
          <div className="agent-suite-card-header">
            <div className="agent-title-wrap">
              <Activity size={18} className="card-icon" />
              <h4>Prediction Agent</h4>
            </div>
            <span className="agent-pill">Online</span>
          </div>
          <p className="agent-desc">
            Executes ML risk estimation utilizing CatBoost, LightGBM, and XGBoost ensembles with SHAP-driven local feature attribution.
          </p>
          <span className="agent-tech-tag">models: /diabetes, /hypertension, /heart_disease</span>
        </div>

        <div className="agent-suite-card">
          <div className="agent-suite-card-header">
            <div className="agent-title-wrap">
              <Database size={18} className="card-icon" />
              <h4>Evidence Agent</h4>
            </div>
            <span className="agent-pill">Synced</span>
          </div>
          <p className="agent-desc">
            Cross-references patient clinical markers against Neo4j PrimeKG knowledge graph nodes and contraindication literature.
          </p>
          <span className="agent-tech-tag">protocol: Neo4j Cypher / Subgraph Expansion</span>
        </div>

        <div className="agent-suite-card">
          <div className="agent-suite-card-header">
            <div className="agent-title-wrap">
              <BrainCircuit size={18} className="card-icon" />
              <h4>Reasoning Agent</h4>
            </div>
            <span className="agent-pill">Ready</span>
          </div>
          <p className="agent-desc">
            Synthesizes quantitative risk scores and biomedical facts into coherent, actionable clinical diagnostic recommendations.
          </p>
          <span className="agent-tech-tag">engine: Rule Synthesis & Decision Fusion</span>
        </div>
      </section>

    </div>
  );
}
