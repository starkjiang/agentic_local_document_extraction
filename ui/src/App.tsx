import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { UploadPage } from './pages/UploadPage';
import { JobsPage } from './pages/JobsPage';
import { SearchPage } from './pages/SearchPage';
import { ChatExtractor } from './components/ChatExtractor';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/chat" element={
            <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 16px'}}>
              <ChatExtractor />
            </div>
          } />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
