import React, { useState } from 'react';
import { Send, Bot, User, Loader2, FileText } from 'lucide-react';
import { api } from '../api';

export const ChatExtractor: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [feedback, setFeedback] = useState('');

  const handleSubmit = async () => {
    if (!file || !prompt) return;
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('prompt', prompt);
      
      const response = await fetch('http://localhost:8000/extract/chat', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRefine = async () => {
    if (!result?.session_id || !feedback) return;
    
    const formData = new FormData();
    formData.append('feedback', feedback);
    
    const response = await fetch(`http://localhost:8000/chat/${result.session_id}/refine`, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    setResult({ ...result, custom_extraction: { content: data.refined_extraction } });
    setFeedback('');
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Chat-Driven Extraction</h2>
      <p style={{ color: '#64748b', marginBottom: 24 }}>
        Tell me what you want to extract — e.g., "Extract methods as bullet points"
      </p>

      {/* File Upload */}
      <div style={{ 
        border: '2px dashed #cbd5e1', borderRadius: 16, padding: 32, 
        textAlign: 'center', marginBottom: 24, background: '#fff'
      }}>
        <input 
          type="file" accept=".pdf" 
          onChange={e => setFile(e.target.files?.[0] || null)}
          style={{ display: 'none' }} id="chat-file"
        />
        <label htmlFor="chat-file" style={{ cursor: 'pointer' }}>
          <FileText size={40} color="#94a3b8" />
          <p style={{ marginTop: 8, color: '#334155' }}>
            {file ? file.name : 'Click to upload PDF'}
          </p>
        </label>
      </div>

      {/* Prompt Input */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <input
          type="text"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="e.g., Extract methods section as bullet points..."
          style={{
            flex: 1, padding: '14px 18px', borderRadius: 12,
            border: '1px solid #e2e8f0', fontSize: 15,
            outline: 'none'
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !file || !prompt}
          style={{
            padding: '14px 24px', background: '#2563eb', color: '#fff',
            border: 'none', borderRadius: 12, fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? <Loader2 size={20} className="spin" /> : <Send size={20} />}
        </button>
      </div>

      {/* Example Prompts */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Try these:</p>
        {[
          "Summarize key findings in 3 bullet points",
          "Extract only the methods section",
          "Find all authors and institutions mentioned",
          "Compare results vs discussion sections",
          "Extract as JSON with title, authors, date"
        ].map(ex => (
          <button
            key={ex}
            onClick={() => setPrompt(ex)}
            style={{
              display: 'inline-block', margin: '4px 8px 4px 0',
              padding: '8px 14px', background: '#f1f5f9',
              border: 'none', borderRadius: 20, fontSize: 13,
              color: '#475569', cursor: 'pointer'
            }}
          >
            {ex}
          </button>
        ))}
      </div>

      {/* Results */}
      {result && (
        <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          {/* Interpretation */}
          <div style={{ padding: 20, borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Bot size={18} color="#2563eb" />
              <span style={{ fontWeight: 600, color: '#334155' }}>I understood:</span>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ padding: '4px 12px', background: '#eff6ff', color: '#2563eb', borderRadius: 20, fontSize: 13 }}>
                Intent: {result.interpretation.intent}
              </span>
              <span style={{ padding: '4px 12px', background: '#f0fdf4', color: '#166534', borderRadius: 20, fontSize: 13 }}>
                Format: {result.interpretation.output_format}
              </span>
              {result.interpretation.target_sections.map((s: string) => (
                <span key={s} style={{ padding: '4px 12px', background: '#fffbeb', color: '#d97706', borderRadius: 20, fontSize: 13 }}>
                  Section: {s}
                </span>
              ))}
            </div>
          </div>

          {/* Extraction Output */}
          <div style={{ padding: 24 }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, color: '#64748b' }}>Extracted Content:</h4>
            <div style={{ 
              background: '#f8fafc', padding: 20, borderRadius: 12,
              fontSize: 14, lineHeight: 1.8, color: '#334155',
              whiteSpace: 'pre-wrap'
            }}>
              {result.custom_extraction?.content || result.standard_result?.markdown_content || 'No content extracted'}
            </div>
          </div>

          {/* Refinement */}
          <div style={{ padding: '0 24px 24px' }}>
            <div style={{ display: 'flex', gap: 12 }}>
              <input
                type="text"
                value={feedback}
                onChange={e => setFeedback(e.target.value)}
                placeholder="Refine: e.g., 'Make it shorter' or 'Add more detail'"
                style={{
                  flex: 1, padding: '12px 16px', borderRadius: 10,
                  border: '1px solid #e2e8f0', fontSize: 14
                }}
              />
              <button
                onClick={handleRefine}
                disabled={!feedback}
                style={{
                  padding: '12px 20px', background: '#334155', color: '#fff',
                  border: 'none', borderRadius: 10, fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                Refine
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
