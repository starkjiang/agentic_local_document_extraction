import React from 'react';
import { Bot, FileSearch, CheckCircle, Sparkles } from 'lucide-react';

interface Props {
  status: string;
  currentStep: string;
  retryCount: number;
}

const steps = [
  { id: 'supervisor', label: 'Supervisor', icon: <Bot size={20} /> },
  { id: 'extractor', label: 'Extractor', icon: <FileSearch size={20} /> },
  { id: 'validator', label: 'Validator', icon: <CheckCircle size={20} /> },
  { id: 'synthesizer', label: 'Synthesizer', icon: <Sparkles size={20} /> },
];

export const WorkflowGraph: React.FC<Props> = ({ status, currentStep, retryCount }) => {
  const getStatus = (stepId: string) => {
    if (status === 'failed') return currentStep.includes(stepId) ? 'error' : 'idle';
    const order = ['supervisor', 'extractor', 'validator', 'synthesizer'];
    const currentIdx = order.findIndex(s => currentStep.includes(s));
    const stepIdx = order.indexOf(stepId);
    if (currentStep.includes(stepId) && status !== 'completed') return 'active';
    if (stepIdx < currentIdx || status === 'completed') return 'completed';
    return 'idle';
  };

  const colors = {
    idle: { border: '#cbd5e1', bg: '#f8fafc', text: '#94a3b8' },
    active: { border: '#2563eb', bg: '#eff6ff', text: '#1d4ed8' },
    completed: { border: '#22c55e', bg: '#f0fdf4', text: '#15803d' },
    error: { border: '#ef4444', bg: '#fef2f2', text: '#b91c1c' },
  };

  return (
    <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden', marginBottom: 24 }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#334155' }}>Agent Workflow</h3>
      </div>
      
      <div style={{ padding: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
        {steps.map((step, i) => {
          const s = getStatus(step.id) as keyof typeof colors;
          const c = colors[s];
          
          return (
            <React.Fragment key={step.id}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '16px 24px', borderRadius: 16,
                border: `2px solid ${c.border}`, background: c.bg,
                color: c.text, minWidth: 160,
                boxShadow: s === 'active' ? '0 0 20px rgba(37,99,235,0.15)' : 'none',
                transition: 'all 0.5s'
              }}>
                <div style={{ padding: 8, background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                  {step.icon}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{step.label}</div>
                  {step.id === 'extractor' && retryCount > 0 && (
                    <div style={{ fontSize: 11, opacity: 0.8 }}>Retry {retryCount}</div>
                  )}
                  {s === 'active' && (
                    <div style={{ fontSize: 11, opacity: 0.8, animation: 'pulse 2s infinite' }}>Running...</div>
                  )}
                </div>
              </div>
              
              {i < steps.length - 1 && (
                <div style={{
                  width: 40, height: 2, background: s === 'completed' ? '#22c55e' : '#e2e8f0',
                  transition: 'all 0.5s'
                }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
