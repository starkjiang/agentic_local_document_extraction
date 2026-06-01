import React, { useState, useCallback } from 'react';
import { Upload, FileText, Settings, ChevronDown } from 'lucide-react';

interface Props {
  onUpload: (file: File, strategy: string) => void;
  isUploading: boolean;
}

export const UploadZone: React.FC<Props> = ({ onUpload, isUploading }) => {
  const [strategy, setStrategy] = useState('auto');
  const [showMenu, setShowMenu] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const strategies = [
    { value: 'auto', label: 'Auto', desc: 'Automatically select best strategy' },
    { value: 'hi_res', label: 'High Resolution', desc: 'Best quality, slower' },
    { value: 'ocr_only', label: 'OCR Only', desc: 'Force OCR for scanned docs' },
    { value: 'fast', label: 'Fast', desc: 'Quick extraction' },
  ];

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
  }, []);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = () => {
    if (file) onUpload(file, strategy);
  };

  return (
    <div>
      {/* Strategy Selector */}
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <button
          onClick={() => setShowMenu(!showMenu)}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '10px 16px', background: '#fff', border: '1px solid #e2e8f0',
            borderRadius: 10, fontSize: 13, fontWeight: 500, color: '#334155', cursor: 'pointer'
          }}
        >
          <Settings size={16} />
          Strategy: {strategies.find(s => s.value === strategy)?.label}
          <ChevronDown size={14} />
        </button>
        
        {showMenu && (
          <div style={{
            position: 'absolute', top: '100%', left: 0, marginTop: 8,
            width: 280, background: '#fff', borderRadius: 12,
            boxShadow: '0 10px 40px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0', zIndex: 50
          }}>
            {strategies.map(s => (
              <button
                key={s.value}
                onClick={() => { setStrategy(s.value); setShowMenu(false); }}
                style={{
                  width: '100%', textAlign: 'left', padding: '12px 16px',
                  border: 'none', background: strategy === s.value ? '#eff6ff' : '#fff',
                  borderLeft: strategy === s.value ? '3px solid #2563eb' : '3px solid transparent',
                  cursor: 'pointer'
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{s.label}</div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{s.desc}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Drop Zone */}
      <div
        onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? '#2563eb' : '#cbd5e1'}`,
          borderRadius: 20, padding: 60, textAlign: 'center',
          background: dragActive ? '#eff6ff' : '#fff',
          transition: 'all 0.3s', cursor: 'pointer', opacity: isUploading ? 0.6 : 1
        }}
      >
        <input type="file" accept=".pdf" onChange={handleFile} style={{ display: 'none' }} id="file-input" />
        <label htmlFor="file-input" style={{ cursor: 'pointer' }}>
          <div style={{
            display: 'inline-flex', padding: 20, borderRadius: 20,
            background: dragActive ? '#dbeafe' : '#f1f5f9', marginBottom: 20
          }}>
            {isUploading ? (
              <div style={{ width: 40, height: 40, border: '3px solid #2563eb', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
            ) : (
              <Upload size={40} color={dragActive ? '#2563eb' : '#94a3b8'} />
            )}
          </div>
          
          <p style={{ fontSize: 18, fontWeight: 600, color: '#334155', margin: '0 0 4px' }}>
            {isUploading ? 'Uploading...' : dragActive ? 'Drop PDF here' : 'Drag & drop your PDF'}
          </p>
          <p style={{ fontSize: 13, color: '#64748b' }}>
            or <span style={{ color: '#2563eb', fontWeight: 500 }}>click to browse</span>
          </p>
        </label>

        {file && !isUploading && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            marginTop: 16, padding: '8px 16px', background: '#f0fdf4',
            color: '#166534', borderRadius: 8, fontSize: 13, fontWeight: 500
          }}>
            <FileText size={16} />
            {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}
      </div>

      {file && (
        <button
          onClick={handleSubmit}
          disabled={isUploading}
          style={{
            marginTop: 16, width: '100%', padding: 14,
            background: '#2563eb', color: '#fff', border: 'none',
            borderRadius: 12, fontSize: 15, fontWeight: 600,
            cursor: isUploading ? 'not-allowed' : 'pointer',
            opacity: isUploading ? 0.6 : 1
          }}
        >
          {isUploading ? 'Processing...' : 'Start Extraction'}
        </button>
      )}
    </div>
  );
};