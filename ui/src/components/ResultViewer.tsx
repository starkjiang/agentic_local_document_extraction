import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText, Table, Database, Code, CheckCircle } from 'lucide-react';

interface Props {
  result: any;
  extractionResult?: any;
}

export const ResultViewer: React.FC<Props> = ({ result, extractionResult }) => {
  const [tab, setTab] = useState<'markdown' | 'tables' | 'entities' | 'json'>('markdown');

  const tabs = [
    { id: 'markdown' as const, label: 'Markdown', icon: <FileText size={16} /> },
    { id: 'tables' as const, label: 'Tables', icon: <Table size={16} /> },
    { id: 'entities' as const, label: 'Entities', icon: <Database size={16} /> },
    { id: 'json' as const, label: 'JSON', icon: <Code size={16} /> },
  ];

  const confidence = result?.confidence || 0;
  const confColor = confidence >= 0.8 ? '#22c55e' : confidence >= 0.6 ? '#d97706' : '#dc2626';
  const confLabel = confidence >= 0.8 ? 'High' : confidence >= 0.6 ? 'Medium' : 'Low';

  return (
    <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '24px 28px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div>
            <h2 style={{ margin: '0 0 4px', fontSize: 18, fontWeight: 700, color: '#1e293b' }}>{result?.filename}</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13, color: '#64748b' }}>
              <span style={{ textTransform: 'capitalize', background: '#f1f5f9', padding: '4px 12px', borderRadius: 20, fontWeight: 500 }}>{result?.document_type}</span>
              <span>{result?.processing_metadata?.total_time_ms?.toFixed(0)}ms</span>
              {result?.processing_metadata?.retry_count > 0 && (
                <span style={{ color: '#d97706', background: '#fffbeb', padding: '4px 12px', borderRadius: 20 }}>{result.processing_metadata.retry_count} retries</span>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: '#fff', borderRadius: 12, border: `2px solid ${confColor}` }}>
            <CheckCircle size={18} color={confColor} />
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: confColor }}>{confLabel} Confidence</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: confColor }}>{(confidence * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>
        
        <div style={{ padding: 16, background: '#eff6ff', borderRadius: 12, fontSize: 14, color: '#1e3a5f', lineHeight: 1.6 }}>
          <strong style={{ color: '#1d4ed8' }}>Summary:</strong> {result?.summary}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '16px 24px', fontSize: 13, fontWeight: 500,
              border: 'none', borderBottom: `2px solid ${tab === t.id ? '#2563eb' : 'transparent'}`,
              background: tab === t.id ? '#eff6ff' : 'transparent',
              color: tab === t.id ? '#2563eb' : '#64748b', cursor: 'pointer'
            }}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: 28, maxHeight: 600, overflow: 'auto' }}>
        {tab === 'markdown' && (
          <div style={{ fontSize: 14, lineHeight: 1.8, color: '#334155' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{result?.markdown_content || ''}</ReactMarkdown>
          </div>
        )}

        {tab === 'tables' && (
          <div>
            {(extractionResult?.pages?.flatMap((p: any) => p.tables) || []).length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>No tables extracted</div>
            ) : (
              (extractionResult?.pages?.flatMap((p: any) => p.tables) || []).map((table: any, i: number) => (
                <div key={i} style={{ marginBottom: 24, border: '1px solid #e2e8f0', borderRadius: 12, overflow: 'hidden' }}>
                  <div style={{ padding: '12px 16px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', fontSize: 13, fontWeight: 600, color: '#334155' }}>
                    Table on Page {table.page_number}
                  </div>
                  <div style={{ overflow: 'auto' }}>
                    <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ background: '#f8fafc' }}>
                          {table.headers?.map((h: string, j: number) => (
                            <th key={j} style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#334155', borderBottom: '1px solid #e2e8f0' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {table.rows?.map((row: string[], j: number) => (
                          <tr key={j} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            {row.map((cell: string, k: number) => (
                              <td key={k} style={{ padding: '10px 16px', color: '#475569' }}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {tab === 'entities' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            {(result?.key_entities || []).length === 0 ? (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 60, color: '#94a3b8' }}>No entities extracted</div>
            ) : (
              result.key_entities.map((entity: any, i: number) => (
                <div key={i} style={{ padding: 16, border: '1px solid #e2e8f0', borderRadius: 12, background: '#fff' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, color: '#64748b', background: '#f1f5f9', padding: '4px 10px', borderRadius: 6 }}>{entity.type}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: entity.confidence > 0.8 ? '#22c55e' : '#d97706' }}>{(entity.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 500, color: '#1e293b' }}>{entity.value}</div>
                </div>
              ))
            )}
          </div>
        )}

        {tab === 'json' && (
          <pre style={{ background: '#0f172a', color: '#e2e8f0', padding: 20, borderRadius: 12, overflow: 'auto', fontSize: 12, fontFamily: 'monospace', lineHeight: 1.6 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};
