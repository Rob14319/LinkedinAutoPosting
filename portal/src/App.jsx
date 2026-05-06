import React, { useState, useEffect } from 'react';
import { Send, CheckCircle, Clock, AlertCircle, Share2, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const App = () => {
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [error, setError] = useState('');
  const [imageUrl, setImageUrl] = useState('');

  useEffect(() => {
    // Get content from URL params (p is base64 encoded JSON)
    const params = new URLSearchParams(window.location.search);
    const p = params.get('p');
    const c = params.get('c'); // Backward compatibility
    
    if (p) {
      try {
        const decoded = JSON.parse(atob(p));
        setContent(decoded.c || '');
        if (decoded.i) setImageUrl(decoded.i);
      } catch (e) {
        console.error('Failed to decode payload', e);
        setError('Invalid post payload in URL.');
      }
    } else if (c) {
      try {
        setContent(atob(c));
      } catch (e) {
        setError('Invalid post content in URL.');
      }
    } else {
      setError('No post content found. Please check your email link.');
    }
  }, []);

  const handlePublish = async () => {
    setStatus('loading');
    try {
      await axios.post('/api/publish', { content });
      setStatus('success');
      setPostUrl('https://www.linkedin.com/feed/');
    } catch (err) {
      console.error('Publish error', err);
      setStatus('error');
      const errorDetail = err.response?.data?.details?.message || err.response?.data?.message || err.message;
      setError(`Failed to publish: ${errorDetail}`);
    }
  };

  return (
    <div className="app-container">
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="animate-fade-in"
        style={{ textAlign: 'center', marginBottom: '3rem' }}
      >
        <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem', background: 'var(--gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          LinkedIn Publisher
        </h1>
        <p style={{ color: 'var(--text-dim)' }}>Review your daily draft and publish with one click.</p>
      </motion.header>

      <main>
        <div className="glass-card">
          <AnimatePresence mode="wait">
            {status === 'success' ? (
              <motion.div 
                key="success"
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                style={{ textAlign: 'center', padding: '3rem 2rem' }}
              >
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', damping: 12, stiffness: 200, delay: 0.2 }}
                  style={{ color: '#22c55e', marginBottom: '2rem' }}
                >
                  <CheckCircle size={100} style={{ margin: '0 auto', filter: 'drop-shadow(0 0 20px rgba(34, 197, 94, 0.4))' }} />
                </motion.div>
                <h2 style={{ fontSize: '2.5rem', marginBottom: '1rem', fontWeight: '700' }}>Post Published!</h2>
                <p style={{ color: 'var(--text-dim)', marginBottom: '2.5rem', fontSize: '1.1rem' }}>
                  Your story is now live. Check the impact on LinkedIn!
                </p>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
                  <a href={postUrl} target="_blank" rel="noreferrer" className="premium-button" style={{ padding: '1.2rem 2.5rem' }}>
                    View Live Post <ArrowRight size={20} />
                  </a>
                  <button onClick={() => setStatus('idle')} className="premium-button" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                    Done
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div key="review" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: '600', letterSpacing: '-0.02em' }}>Daily Draft Review</h3>
                  <div style={{ display: 'flex', gap: '0.5rem', color: 'var(--accent)', fontSize: '0.9rem', background: 'rgba(56, 189, 248, 0.1)', padding: '0.4rem 0.8rem', borderRadius: '20px', fontWeight: '500' }}>
                    <Clock size={16} /> <span>Draft Generated Today</span>
                  </div>
                </div>

                {error ? (
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', padding: '1rem', borderRadius: '12px', color: '#f87171', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <AlertCircle size={20} /> {error}
                  </div>
                ) : (
                  <>
                    <div className="linkedin-preview">
                      <div className="preview-header">
                        <div className="avatar">
                          <Share2 size={24} color="#0a66c2" />
                        </div>
                        <div className="profile-info">
                          <h4>You</h4>
                          <p>Entrepreneur & Founder • Just now</p>
                        </div>
                      </div>
                      <div className="preview-content">
                        {content || 'Generating preview...'}
                        {imageUrl && (
                          <div style={{ marginTop: '1rem', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <img src={imageUrl} alt="AI Generated" style={{ width: '100%', display: 'block' }} />
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                      <button 
                        onClick={handlePublish}
                        disabled={status === 'loading' || !content}
                        className="premium-button"
                        style={{ flex: 1, justifyContent: 'center' }}
                      >
                        {status === 'loading' ? 'Publishing...' : 'Publish to LinkedIn Now'}
                        <Send size={20} />
                      </button>
                    </div>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      <footer style={{ marginTop: '4rem', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
        Powered by Antigravity AI • Premium Automation Workflow
      </footer>
    </div>
  );
};

export default App;
