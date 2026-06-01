import React, { useState, useEffect } from 'react';
import { UploadZone } from '../components/UploadZone';
import { WorkflowGraph } from '../components/WorkflowGraph';
import { AgentLogs } from '../components/AgentLogs';
import { ResultViewer } from '../components/ResultViewer';
import { api } from '../api';
import { Loader2, FileText, CheckCircle, XCircle, Clock } from 'lucide-react';

export const UploadPage: React.FC = () => {
  const [job, setJob] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pollInterval, setPollInterval] = useState<any>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [pollInterval]);

  const handleUpload = async (file: File, strategy: string) => {
    setIsUploading(true);
    setIsProcessing(false);
    setJob(null);
    if (pollInterval) clearInterval(pollInterval);

    try {
      const { job_id } = await api.uploadPDF(file, strategy);
      
      setIsUploading(false);
      setIsProcessing(true);
      
      setJob({
        job_id,
        status: 'pending',
        filename: file.name,
        current_step: 'pending',
        logs: [],
        errors: [],
        warnings: [],
      });

      // Poll for updates every 1.5 seconds
      const interval = setInterval(async () => {
        try {
          const status = await api.getStatus(job_id);
          setJob(status);

          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
            setPollInterval(null);
            setIsProcessing(false);
          }
        } catch (e) {
          clearInterval(interval);
          setIsProcessing(false);
        }
      }, 1500);

      setPollInterval(interval);

    } catch (error) {
      setIsUploading(false);
      setIsProcessing(false);
      alert('Upload failed: ' + (error as any).message);
    }
  };

  const getProgressPercent = () => {
    if (!job) return 0;
    const steps = ['pending', 'extracting', 'validating', 'synthesizing', 'completed'];
    const idx = steps.indexOf(job.status);
    if (idx === -1) return 0;
    return Math.min((idx / (steps.length - 1)) * 100, 100);
  };

  const getStatusIcon = () => {
    if (isUploading) return <Loader2 size={20} className="spin" color="#2563eb" />;
    if (job?.status === 'completed') return <CheckCircle size={20} color="#22c55e" />;
    if (job?.status === 'failed') return <XCircle size={20} color="#dc2626" />;
    if (isProcessing) return <Loader2 size={20} className="spin" color="#2563eb" />;
    return <Clock size={20} color="#94a3b8" />;
  };

  const getStatusText = () => {
    if (isUploading) return 'Uploading PDF...';
    if (job?.status === 'completed') return 'Extraction Complete!';
    if (job?.status === 'failed') return 'Extraction Failed';
    if (job?.status === 'extracting') return 'Extracting content with Docling...';
    if (job?.status === 'validating') return 'Validating extraction quality...';
    if (job?.status === 'synthesizing') return 'Synthesizing final output...';
    if (job?.status === 'retrying') return 'Retrying with better strategy...';
    if (isProcessing) return 'Starting extraction...';
    return 'Ready to extract';
  };

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: '#1e293b', margin: '0 0 8px' }}>Document Extraction</h1>
      <p style={{ color: '#64748b', margin: '0 0 32px' }}>Upload a PDF and watch our multi-agent system process it</p>

      <UploadZone onUpload={handleUpload} isUploading={isUploading} />

      {/* PROGRESS INDICATOR */}
      {(isUploading || isProcessing || job) && (
        <div style={{
          marginTop: 24,
          padding: 24,
          background: '#fff',
          borderRadius: 16,
          border: '1px solid #e2e8f0',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <div style={{
              padding: 12,
              background: isUploading || isProcessing ? '#eff6ff' : job?.status === 'completed' ? '#f0fdf4' : '#fef2f2',
              borderRadius: 12
            }}>
              {getStatusIcon()}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 4 }}>
                {getStatusText()}
              </div>
              <div style={{ fontSize: 13, color: '#64748b' }}>
                {job?.filename && <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><FileText size={14} /> {job.filename}</span>}
              </div>
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: '#2563eb' }}>
              {Math.round(getProgressPercent())}%
            </div>
          </div>

          {/* Progress Bar */}
          <div style={{
            width: '100%',
            height: 8,
            background: '#f1f5f9',
            borderRadius: 4,
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${getProgressPercent()}%`,
              height: '100%',
              background: job?.status === 'failed' ? '#dc2626' : job?.status === 'completed' ? '#22c55e' : '#2563eb',
              borderRadius: 4,
              transition: 'width 0.5s ease',
              backgroundImage: isProcessing ? 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)' : 'none',
              backgroundSize: '200% 100%',
              animation: isProcessing ? 'shimmer 1.5s infinite' : 'none'
            }} />
          </div>

          {/* Step indicators */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12 }}>
            {['Upload', 'Extract', 'Validate', 'Synthesize', 'Done'].map((step, i) => {
              const percent = getProgressPercent();
              const isActive = (i / 4) * 100 <= percent;
              return (
                <div key={step} style={{ textAlign: 'center' }}>
                  <div style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: isActive ? '#2563eb' : '#e2e8f0',
                    margin: '0 auto 4px',
                    transition: 'all 0.3s'
                  }} />
                  <span style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: isActive ? '#2563eb' : '#94a3b8'
                  }}>{step}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* WORKFLOW GRAPH */}
      {job && (
        <div style={{ marginTop: 24 }}>
          <WorkflowGraph
            status={job.status}
            currentStep={job.current_step}
            retryCount={job.retry_count || 0}
          />
        </div>
      )}

      {/* AGENT LOGS */}
      {job && (
        <div style={{ marginTop: 24 }}>
          <AgentLogs
            logs={job.logs || []}
            errors={job.errors || []}
            warnings={job.warnings || []}
          />
        </div>
      )}

      {/* RESULTS */}
      {job?.result && (
        <div style={{ marginTop: 24 }}>
          <ResultViewer result={job.result} extractionResult={job.extraction_result} />
        </div>
      )}

      {/* ERROR STATE */}
      {job?.status === 'failed' && !job?.result && (
        <div style={{
          marginTop: 24,
          padding: 40,
          textAlign: 'center',
          background: '#fef2f2',
          borderRadius: 16,
          border: '1px solid #fecaca',
          color: '#dc2626'
        }}>
          <XCircle size={48} style={{ margin: '0 auto 16px' }} />
          <h3 style={{ margin: '0 0 8px', fontSize: 18, fontWeight: 600 }}>Extraction Failed</h3>
          <p style={{ margin: 0, fontSize: 14 }}>{job.errors?.[0] || 'Unknown error occurred'}</p>
        </div>
      )}
    </div>
  );
};
