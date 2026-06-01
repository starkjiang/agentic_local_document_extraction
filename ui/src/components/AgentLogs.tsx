import React, { useState } from 'react';
import { Info, AlertTriangle, AlertCircle, Filter } from 'lucide-react';

interface Props {
  logs: Array<{ timestamp: string; step: string; message: string; level: string }>;
  errors: string[];
  warnings: string[];
}

export const AgentLogs: React.FC<Props> = ({ logs, errors, warnings }) => {
  const [filter, setFilter] = useState<'all' | 'info' | 'warning' | 'error'>('all');

  const all = [
    ...logs.map(l => ({ ...l, type: l.level })),
    ...errors.map(e => ({ timestamp: new Date().toISOString(), step: 'system', message: e, level: 'error', type: 'error' })),
    ...warnings.map(w => ({ timestamp: new Date().toISOString(), step: 'system', message: w, level: 'warning', type: 'warning' })),
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  const filtered = filter === 'all' ? all : all.filter(e => e.type === filter);

  const icons = {
    error: <AlertCircle size={14} color="#dc2626" />,
    warning: <AlertTriangle size={14} color="#d97706" />,
    info: <Info size={14} color="#2563eb" />,
  };

  const bgColors = {
    error: '#fef2f2',
    warning: '#fffbeb',
    info: '#fff',
  };

  return (
    <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden', marginBottom: 24 }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#334155' }}>Agent Logs</h3>
          <div style={{ display: 'flex', gap: 6, fontSize: 11 }}>
            <span style={{ padding: '2px 8px', background: '#f1f5f9', borderRadius: 10, color: '#64748b' }}>{logs.length}</span>
            {errors.length > 0 && <span style={{ padding: '2px 8px', background: '#fef2f2', borderRadius: 10, color: '#dc2626' }}>{errors.length} errors</span>}
            {warnings.length > 0 && <span style={{ padding: '2px 8px', background: '#fffbeb', borderRadius: 10, color: '#d97706' }}>{warnings.length} warnings</span>}
          </div>
        </div>
        <Filter size={16} color="#94a3b8" />
      </div>

      <div style={{ padding: '12px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', gap: 8 }}>
        {(['all', 'info', 'warning', 'error'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '6px 14px', borderRadius: 8, fontSize: 12, fontWeight: 500,
              border: 'none', cursor: 'pointer', textTransform: 'capitalize',
              background: filter === f ? '#334155' : '#f1f5f9',
              color: filter === f ? '#fff' : '#64748b'
            }}
          >
            {f}
          </button>
        ))}
      </div>

      <div style={{ maxHeight: 300, overflow: 'auto', padding: 12 }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', fontSize: 13 }}>No logs to display</div>
        ) : (
          filtered.map((entry, idx) => (
            <div key={idx} style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              padding: '10px 14px', borderRadius: 10, marginBottom: 6,
              background: bgColors[entry.type as keyof typeof bgColors] || '#fff',
              border: '1px solid #f1f5f9', fontSize: 13
            }}>
              <div style={{ marginTop: 2 }}>{icons[entry.type as keyof typeof icons] || icons.info}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, fontSize: 11, color: '#64748b' }}>
                  <span style={{ fontFamily: 'monospace', fontWeight: 600, background: '#f1f5f9', padding: '2px 6px', borderRadius: 4, color: '#475569' }}>{entry.step}</span>
                  <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
                </div>
                <div style={{ color: '#334155', lineHeight: 1.5 }}>{entry.message}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};