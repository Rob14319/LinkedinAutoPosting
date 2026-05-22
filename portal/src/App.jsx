import React, { useState, useEffect } from 'react';
import { Send, CheckCircle, Clock, AlertCircle, Share2, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const App = () => {
  const [content, setContent] = useState('');
  const [comment, setComment] = useState('');
  const [payloadType, setPayloadType] = useState('post'); // post, engagement
  const [targetUrl, setTargetUrl] = useState('');
  const [activityId, setActivityId] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [history, setHistory] = useState(() => JSON.parse(localStorage.getItem('publish_history') || '[]'));
  const [error, setError] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [activeTab, setActiveTab] = useState('review'); // review, history

  useEffect(() => {
    // Get content from URL params (p is base64 encoded JSON)
    const params = new URLSearchParams(window.location.search);
    const p = params.get('p');
    const c = params.get('c'); // Backward compatibility
    
    if (p) {
      try {
        const decoded = JSON.parse(atob(p));
        if (decoded.t === 'engagement') {
          setPayloadType('engagement');
          setComment(decoded.c || '');
          setTargetUrl(decoded.url || '');
          setActivityId(decoded.aid || '');
        } else {
          setContent(decoded.c || '');
          if (decoded.i) setImageUrl(decoded.i);
        }
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
      const payload = payloadType === 'engagement' 
        ? { comment, type: 'engagement', activityId }
        : { content, comment };
        
      await axios.post('/api/publish', payload);
      
      // Save to history
      const newEntry = {
        date: new Date().toLocaleString(),
        type: payloadType,
        content: payloadType === 'engagement' ? comment : content,
        url: targetUrl || 'Own Post'
      };
      const updatedHistory = [newEntry, ...history].slice(0, 20);
      setHistory(updatedHistory);
      localStorage.setItem('publish_history', JSON.stringify(updatedHistory));
      
      setStatus('success');
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
          LinkedIn Agent
        </h1>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '1.5rem' }}>
          <button 
            onClick={() => setActiveTab('review')}
            style={{ background: 'none', border: 'none', color: activeTab === 'review' ? 'var(--accent)' : 'var(--text-dim)', fontWeight: '600', cursor: 'pointer', borderBottom: activeTab === 'review' ? '2px solid var(--accent)' : 'none', padding: '0.5rem 1rem' }}
          >
            REVIEW
          </button>
          <button 
            onClick={() => setActiveTab('history')}
            style={{ background: 'none', border: 'none', color: activeTab === 'history' ? 'var(--accent)' : 'var(--text-dim)', fontWeight: '600', cursor: 'pointer', borderBottom: activeTab === 'history' ? '2px solid var(--accent)' : 'none', padding: '0.5rem 1rem' }}
          >
            HISTORY
          </button>
        </div>
      </motion.header>

      <main>
        <div className="glass-card">
          <AnimatePresence mode="wait">
            {activeTab === 'history' ? (
              <motion.div key="history" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <h3 style={{ marginBottom: '2rem' }}>Recent Activity</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {history.length === 0 ? (
                    <p style={{ color: 'var(--text-dim)' }}>No history yet. Start publishing!</p>
                  ) : history.map((item, idx) => (
                    <div key={idx} style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', borderLeft: `4px solid ${item.type === 'engagement' ? '#fbbf24' : '#0a66c2'}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{item.date}</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: item.type === 'engagement' ? '#fbbf24' : '#38bdf8' }}>{item.type.toUpperCase()}</span>
                      </div>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>{item.url}</p>
                      <p style={{ fontSize: '1rem' }}>{item.content.substring(0, 100)}{item.content.length > 100 ? '...' : ''}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : status === 'success' ? (
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
                  <button onClick={() => setStatus('idle')} className="premium-button" style={{ padding: '1.2rem 2.5rem' }}>
                    Done
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div key="review" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: '600', letterSpacing: '-0.02em' }}>
                    {payloadType === 'engagement' ? 'Engagement Review' : 'Daily Draft Review'}
                  </h3>
                  <div style={{ display: 'flex', gap: '0.5rem', color: 'var(--accent)', fontSize: '0.9rem', background: 'rgba(56, 189, 248, 0.1)', padding: '0.4rem 0.8rem', borderRadius: '20px', fontWeight: '500' }}>
                    <Clock size={16} /> <span>{payloadType === 'engagement' ? 'Trending Post Found' : 'Draft Generated Today'}</span>
                  </div>
                </div>

                {payloadType === 'engagement' && (
                  <div style={{ background: 'rgba(251, 191, 36, 0.1)', border: '1px solid #fbbf24', padding: '1rem', borderRadius: '12px', color: '#fcd34d', display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '2rem' }}>
                    <Share2 size={20} /> 
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '0.9rem' }}>Commenting on external post</p>
                      <a href={targetUrl} target="_blank" rel="noreferrer" style={{ color: 'inherit', fontSize: '0.8rem', textDecoration: 'underline' }}>{targetUrl}</a>
                    </div>
                  </div>
                )}

                {error ? (
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', padding: '1rem', borderRadius: '12px', color: '#f87171', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <AlertCircle size={20} /> {error}
                  </div>
                ) : (
                  <>
                      <div className="edit-section">
                        {payloadType !== 'engagement' && (
                          <>
                            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>POST CONTENT</label>
                            <textarea 
                              className="premium-textarea"
                              value={content}
                              onChange={(e) => setContent(e.target.value)}
                              placeholder="What's on your mind?"
                              rows={8}
                            />
                          </>
                        )}
                        
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-dim)', marginTop: payloadType === 'engagement' ? '0' : '1.5rem', marginBottom: '0.5rem' }}>
                          {payloadType === 'engagement' ? 'ENGAGEMENT COMMENT' : 'FIRST COMMENT (Optional - good for links)'}
                        </label>
                        <textarea 
                          className="premium-textarea comment-textarea"
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          placeholder="Add a link or extra thought here..."
                          rows={3}
                        />
                      </div>

                      <div style={{ marginTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '2rem' }}>
                        <h4 style={{ fontSize: '0.9rem', color: 'var(--text-dim)', marginBottom: '1rem', fontWeight: '500' }}>PREVIEW</h4>
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
                          {comment && (
                            <div className="comment-preview">
                              <div className="avatar small">
                                <Share2 size={14} color="#0a66c2" />
                              </div>
                              <div className="comment-bubble">
                                <p><strong>You</strong> • 1st</p>
                                <p>{comment}</p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                    <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                      <button 
                        onClick={handlePublish}
                        disabled={status === 'loading' || (payloadType === 'engagement' ? !comment : !content)}
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
