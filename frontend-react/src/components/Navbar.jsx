import React, { useState } from 'react';
import {
  Home,
  User,
  BarChart3,
  FileText,
  History,
  UserCircle,
  Stethoscope,
  Menu,
  X
} from 'lucide-react';
import '../styles/navbar.css';

/**
 * Primary Application Navbar for MEDINTEL Clinical Decision Support System.
 * Adheres strictly to the single horizontal row desktop layout constraint.
 */
export default function Navbar({ activePage, setActivePage }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Navigation schema using Lucide React SVG icons
  const navItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'patient-data', label: 'Patient Data', icon: User },
    { id: 'analysis', label: 'Analysis', icon: BarChart3 },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'history', label: 'History', icon: History },
    { id: 'profile', label: 'Profile', icon: UserCircle }
  ];

  const handleNavClick = (id) => {
    setActivePage(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="medintel-navbar">
      <div className="navbar-container">

        {/* LEFT: MEDINTEL Branding */}
        <div
          className="brand-container"
          onClick={() => handleNavClick('home')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && handleNavClick('home')}
        >
          <div className="brand-icon-wrapper" aria-hidden="true">
            <Stethoscope size={22} strokeWidth={2.2} />
          </div>
          <div className="brand-text-group">
            <span className="brand-title">
              MEDINTEL <span className="brand-accent">CDSS</span>
            </span>
            <span className="brand-subtitle">Clinical Decision Support</span>
          </div>
        </div>

        {/* TOP-RIGHT: Desktop Navigation (Single Horizontal Row) */}
        <nav className="nav-menu-wrapper" aria-label="Main Navigation">
          <ul className="nav-links-list">
            {navItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = activePage === item.id;

              return (
                <li key={item.id} className="nav-item">
                  <button
                    type="button"
                    className={`nav-btn ${isActive ? 'active' : ''}`}
                    onClick={() => handleNavClick(item.id)}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <span className="nav-btn-icon" aria-hidden="true">
                      <IconComponent size={17} strokeWidth={isActive ? 2.2 : 1.9} />
                    </span>
                    <span className="nav-btn-label">{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>

          {/* Mobile Menu Hamburger (Visible only on genuinely narrow screens) */}
          <button
            type="button"
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </nav>
      </div>

      {/* Mobile Drawer (Only shown when hamburger is triggered) */}
      {mobileMenuOpen && (
        <div className="mobile-drawer">
          <ul className="mobile-nav-list">
            {navItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = activePage === item.id;

              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`mobile-nav-btn ${isActive ? 'active' : ''}`}
                    onClick={() => handleNavClick(item.id)}
                  >
                    <IconComponent size={18} />
                    <span>{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </header>
  );
}
