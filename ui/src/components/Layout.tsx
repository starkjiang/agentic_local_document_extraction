import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Upload, History, Search, FileText, Activity } from 'lucide-react';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  
  const nav = [
    { path: '/', label: 'Upload', icon: <Upload size={20} /> },
    { path: '/jobs', label: 'Jobs', icon: <History size={20} /> },
    { path: '/search', label: 'Search', icon: <Search size={20} /> },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f1f5f9', fontFamily: 'system-ui, sans-serif' }}>
      <aside style={{ width: 240, background: '#fff', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: 24, borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ padding: 10, background: '#2563eb', borderRadius: 12 }}>
              <FileText size={24} color="white" />
            </div>
            <div>
              <h1 style={{ fontSize: 16, fontWeight: 700, color: '#1e293b', margin: 0 }}>PDF Extract</h1>
              <p style={{ fontSize: 11, color: '#64748b', margin: 0 }}>Multi-Agent System</p>
            </div>
          </div>
        </div>

        <nav style={{ padding: 16, flex: 1 }}>
          {nav.map(item => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 16px', borderRadius: 12,
                textDecoration: 'none', fontSize: 14, fontWeight: 500,
                marginBottom: 4, transition: 'all 0.2s',
                background: location.pathname === item.path ? '#eff6ff' : 'transparent',
                color: location.pathname === item.path ? '#2563eb' : '#475569',
              }}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>

        <div style={{ padding: 16, borderTop: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#64748b' }}>
            <Activity size={16} />
            <span>API: localhost:8000</span>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', marginLeft: 'auto' }} />
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: 32 }}>
          {children}
        </div>
      </main>
    </div>
  );
};
