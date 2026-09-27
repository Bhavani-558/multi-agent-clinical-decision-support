import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import {
  User,
  BarChart3,
  FileText,
  History,
  UserCircle,
  AlertCircle,
  ArrowLeft
} from 'lucide-react';
import './styles/global.css';

/**
 * Placeholder view for navigation tabs being implemented in subsequent phases.
 */
function PagePlaceholder({ title, description, icon: Icon, onBackHome }) {
  return (
    <div style={{
      maxWidth: '1440px',
      margin: '0 auto',
      padding: '4rem 1.5rem',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center'
    }}>
      <div style={{
        width: '64px',
        height: '64px',
        borderRadius: '16px',
        background: 'rgba(6, 182, 212, 0.12)',
        border: '1px solid rgba(6, 182, 212, 0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#06b6d4',
        marginBottom: '1.25rem'
      }}>
        <Icon size={32} />
      </div>
      <h2 style={{ fontSize: '1.85rem', marginBottom: '0.5rem' }}>{title}</h2>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', marginBottom: '2rem', lineHeight: '1.6' }}>
        {description}
      </p>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.65rem 1.25rem',
        borderRadius: '8px',
        background: 'rgba(255, 255, 255, 0.04)',
        border: '1px solid var(--border-subtle)',
        fontSize: '0.85rem',
        color: 'var(--accent-teal)',
        marginBottom: '2rem'
      }}>
        <AlertCircle size={16} />
        <span>Phase 1 Scope: Navbar & Home Page Active</span>
      </div>
      <button
        type="button"
        onClick={onBackHome}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1.5rem',
          borderRadius: '8px',
          background: 'var(--bg-surface-elevated)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-subtle)',
          cursor: 'pointer',
          fontWeight: '500'
        }}
      >
        <ArrowLeft size={16} />
        <span>Return to Clinical Dashboard</span>
      </button>
    </div>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState('home');

  const renderActiveScreen = () => {
    switch (activePage) {
      case 'home':
        return <Home onNavigate={setActivePage} />;

      case 'patient-data':
        return (
          <PagePlaceholder
            title="Patient Intake & Clinical Markers"
            description="Dynamic disease-specific patient intake forms and diagnostic parameter entry connected to the CDSS prediction pipeline."
            icon={User}
            onBackHome={() => setActivePage('home')}
          />
        );

      case 'analysis':
        return (
          <PagePlaceholder
            title="Multi-Agent Diagnostic Analysis"
            description="Run CatBoost/LightGBM risk estimators, SHAP feature importance explainability, and Neo4j knowledge graph evidence synthesis."
            icon={BarChart3}
            onBackHome={() => setActivePage('home')}
          />
        );

      case 'reports':
        return (
          <PagePlaceholder
            title="7-Section Clinical Reports"
            description="Evidence-backed clinical diagnostic summaries, contraindication reviews, and physician export formats (PDF / JSON)."
            icon={FileText}
            onBackHome={() => setActivePage('home')}
          />
        );

      case 'history':
        return (
          <PagePlaceholder
            title="Historical Diagnostic Audit Trail"
            description="Review longitudinal patient assessments, previous risk distributions, and counterfactual simulation logs."
            icon={History}
            onBackHome={() => setActivePage('home')}
          />
        );

      case 'profile':
        return (
          <PagePlaceholder
            title="Physician Profile & Credentials"
            description="Manage clinical credentials, Supabase authenticated session tokens, and specialist department assignments."
            icon={UserCircle}
            onBackHome={() => setActivePage('home')}
          />
        );

      default:
        return <Home onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="app-layout">
      {/* 1. Header & Navigation (Phase 1 Target Requirement) */}
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      {/* 2. Main Content Viewport */}
      <main style={{ flex: 1 }}>
        {renderActiveScreen()}
      </main>

      {/* 3. Clinical Platform Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgba(10, 15, 29, 0.95)',
        padding: '1.5rem',
        marginTop: 'auto'
      }}>
        <div style={{
          maxWidth: '1440px',
          margin: '0 auto',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          fontSize: '0.8rem',
          color: 'var(--text-muted)'
        }}>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>MEDINTEL CDSS v2.0</strong> — Multi-Agent Clinical Decision Support System.
          </div>
          <div style={{ maxWidth: '600px', textAlign: 'right', fontSize: '0.74rem' }}>
            <em>Research & Decision-Support System Only. NOT an autonomous diagnostic tool. Final medical decisions must always be made by qualified healthcare professionals.</em>
          </div>
        </div>
      </footer>
    </div>
  );
}
