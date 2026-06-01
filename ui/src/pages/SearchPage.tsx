import React, { useState } from 'react';
import { api } from '../api';
import { Search, FileText, ArrowRight } from 'lucide-react';

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.search(query, 10);
      setResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: '#1e293b', margin: '0 0 8px' }}>Semantic Search</h1>
      <p style={{ color: '#64748b', margin: '0 0 32px' }}>Search across all extracted documents</p>

      <form onSubmit={handleSearch} style={{ position: 'relative', marginBottom: 32 }}>
        <Search size={20} color="#94a3b8" style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)' }} />
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask anything about your documents..."
          style={{
            width: '100%', padding: '16px 16px 16px 48px', fontSize: 15,
            border: '1px solid #e2e8f0', borderRadius: 16, background: '#fff',
            outline: 'none', boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
            padding: '10px 20px', background: '#2563eb', color: '#fff', border: 'none',
            borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer'
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results.length > 0 && (
        <div>
          <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>{results.length} results found</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {results.map((r, i) => (
              <div key={i} style={{ padding: 20, background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <FileText size={16} color="#2563eb" />
                  <span style={{ fontSize: 12, fontWeight: 500, color: '#64748b', background: '#f1f5f9', padding: '4px 12px', borderRadius: 20 }}>{r.metadata?.filename}</span>
                  <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 'auto' }}>{(r.distance * 100).toFixed(1)}% match</span>
                </div>
                <p style={{ fontSize: 14, color: '#334155', lineHeight: 1.6, margin: 0 }}>{r.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
