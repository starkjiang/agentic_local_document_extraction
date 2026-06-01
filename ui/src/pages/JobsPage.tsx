import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { CheckCircle, XCircle, Loader2, Clock, FileText, Trash2 } from 'lucide-react';

export const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([]);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      const list = await api.listJobs();
      setJobs(list);
    } catch (e) {
      console.error(e);
    }
  };

  const deleteJob = async (id: string) => {
    if (!window.confirm('Delete this job?')) return;
    await api.deleteJob(id);
    loadJobs();
  };

  const statusIcon = (s: string) => {
    switch (s) {
      case 'completed': return <CheckCircle size={16} color="#22c55e" />;
      case 'failed': return <XCircle size={16} color="#dc2626" />;
      case 'pending': return <Clock size={16} color="#94a3b8" />;
      default: return <Loader2 size={16} color="#2563eb" className="spin" />;
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: '#1e293b', margin: '0 0 8px' }}>Extraction Jobs</h1>
      <p style={{ color: '#64748b', margin: '0 0 32px' }}>Monitor all document extractions</p>

      <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '16px 24px', textAlign: 'left', fontWeight: 600, color: '#334155' }}>Document</th>
              <th style={{ padding: '16px 24px', textAlign: 'left', fontWeight: 600, color: '#334155' }}>Status</th>
              <th style={{ padding: '16px 24px', textAlign: 'left', fontWeight: 600, color: '#334155' }}>Created</th>
              <th style={{ padding: '16px 24px', textAlign: 'right', fontWeight: 600, color: '#334155' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: 60, textAlign: 'center', color: '#94a3b8' }}>No jobs yet</td>
              </tr>
            ) : (
              jobs.map(job => (
                <tr key={job.job_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <FileText size={18} color="#94a3b8" />
                      <div>
                        <div style={{ fontWeight: 500, color: '#1e293b' }}>{job.filename}</div>
                        <div style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' }}>{job.job_id.slice(0, 8)}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 20, fontSize: 12, fontWeight: 500, textTransform: 'capitalize', background: job.status === 'completed' ? '#f0fdf4' : job.status === 'failed' ? '#fef2f2' : '#f1f5f9', color: job.status === 'completed' ? '#166534' : job.status === 'failed' ? '#dc2626' : '#475569' }}>
                      {statusIcon(job.status)}
                      {job.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px 24px', color: '#64748b' }}>
                    {new Date(job.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                    <button onClick={() => deleteJob(job.job_id)} style={{ padding: 8, background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', borderRadius: 8 }}>
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
