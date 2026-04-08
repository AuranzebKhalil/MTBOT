"use client";
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../components/AuthContext';
import { getApiBaseUrl } from '../lib/config';
import toast from 'react-hot-toast';
import { MessageSquare, Plus, Send, ChevronRight, Clock, ShieldCheck, Ticket, Info, Loader2, User as UserIcon } from 'lucide-react';

export default function UserSupportPage() {
  const [tickets, setTickets] = useState([]);
  const [activeTicket, setActiveTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newSubject, setNewSubject] = useState("");
  const [firstMessage, setFirstMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { token, user } = useAuth();
  const chatEndRef = useRef(null);

  const fetchTickets = async () => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/support/tickets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTickets(data);
      }
    } catch (err) {
      console.error("Ticket sync failed", err);
    }
  };

  const fetchMessages = async (ticketId) => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/support/tickets/${ticketId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      }
    } catch (err) {
       console.error("Message sync failed", err);
    }
  };

  useEffect(() => {
    if (token) fetchTickets();
  }, [token]);

  useEffect(() => {
    if (activeTicket) {
      fetchMessages(activeTicket.id);
      const interval = setInterval(() => fetchMessages(activeTicket.id), 5000);
      return () => clearInterval(interval);
    }
  }, [activeTicket]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCreateTicket = async () => {
    if (!newSubject.trim() || !firstMessage.trim()) return toast.error("Provisioning requires full documentation");
    setIsLoading(true);
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/support/tickets`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ subject: newSubject, content: firstMessage })
      });
      if (res.ok) {
        toast.success("Operational Support Ticket Engaged");
        setIsCreating(false);
        setNewSubject("");
        setFirstMessage("");
        fetchTickets();
      } else {
        const errData = await res.json();
        toast.error(errData.detail || "Ticket generation fault");
      }
    } catch (err) {
      toast.error("Network bridge failure during ticket sync");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !activeTicket) return;
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/support/tickets/${activeTicket.id}/messages?content=${encodeURIComponent(newMessage)}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setNewMessage("");
        fetchMessages(activeTicket.id);
      }
    } catch (err) {
      toast.error("Message uplink failed");
    }
  };

  return (
    <div style={{ 
      height: 'calc(100vh - 120px)', 
      display: 'flex', 
      gap: '1.5rem', 
      padding: '1.5rem',
      background: '#020408',
      borderRadius: '32px'
    }}>
      {/* Sidebar: Institutional Ticket Logs */}
      <div style={{ 
        width: '380px', 
        background: '#0a0c10', 
        borderRadius: '24px', 
        border: '1px solid #1a1e26',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
      }}>
        <div style={{ 
            padding: '1.5rem', 
            borderBottom: '1px solid #1a1e26', 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            background: 'rgba(255,255,255,0.02)'
        }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'white', letterSpacing: '0.5px' }}>TICKETS</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>OPERATIONAL SUPPORT LOGS</p>
          </div>
          <button 
            onClick={() => setIsCreating(true)}
            style={{ 
              background: 'white', 
              color: 'black', 
              border: 'none', 
              padding: '10px', 
              borderRadius: '12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
              boxShadow: '0 4px 15px rgba(255,255,255,0.1)'
            }}
            onMouseOver={(e) => e.target.style.background = '#e2e2e2'}
            onMouseOut={(e) => e.target.style.background = 'white'}
          >
            <Plus size={20} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }} className="custom-scrollbar">
          {tickets.length > 0 ? (
            tickets.map(t => (
              <div 
                key={t.id}
                onClick={() => { setActiveTicket(t); setIsCreating(false); }}
                style={{
                  padding: '1.5rem',
                  borderBottom: '1px solid #1a1e26',
                  cursor: 'pointer',
                  background: activeTicket?.id === t.id ? 'rgba(255,255,255,0.04)' : 'transparent',
                  borderLeft: activeTicket?.id === t.id ? '4px solid white' : '4px solid transparent',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: '800', color: 'white' }}>{t.subject}</span>
                  <span style={{ 
                    fontSize: '0.65rem', 
                    padding: '3px 8px', 
                    borderRadius: '8px', 
                    background: t.status === 'open' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)',
                    color: t.status === 'open' ? '#10b981' : 'var(--text-muted)',
                    fontWeight: '800',
                    textTransform: 'uppercase',
                    border: t.status === 'open' ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid transparent'
                  }}>
                    {t.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '500' }}>
                  <Clock size={12} />
                  {new Date(t.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </div>
              </div>
            ))
          ) : (
            <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Info size={32} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                <p style={{ fontSize: '0.85rem', fontWeight: '600' }}>No active support protocols found</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Terminal Area */}
      <div style={{ 
        flex: 1, 
        background: '#0a0c10', 
        borderRadius: '24px', 
        border: '1px solid #1a1e26',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
      }}>
        {isCreating ? (
          <div style={{ padding: '4rem 2rem', maxWidth: '600px', margin: '0 auto', width: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                <div style={{ width: '48px', height: '48px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid #1a1e26', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                    <Plus size={24} color="white" />
                </div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'white', letterSpacing: '1px' }}>NEW SUPPORT PROTOCOL</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>Engaging technical assistance bridge</p>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '10px', textTransform: 'uppercase' }}>Subject Analysis</label>
                <input 
                  type="text" 
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  style={{ 
                    width: '100%', 
                    padding: '16px', 
                    borderRadius: '12px', 
                    background: '#05070a', 
                    border: '1px solid #1a1e26', 
                    color: 'white',
                    fontSize: '14px',
                    outline: 'none',
                    transition: 'border 0.3s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'white'}
                  onBlur={(e) => e.target.style.borderColor = '#1a1e26'}
                  placeholder="Summarize operational fault..."
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '10px', textTransform: 'uppercase' }}>Technical Documentation</label>
                <textarea 
                  value={firstMessage}
                  onChange={(e) => setFirstMessage(e.target.value)}
                  style={{ 
                    width: '100%', 
                    minHeight: '200px', 
                    padding: '16px', 
                    borderRadius: '12px', 
                    background: '#05070a', 
                    border: '1px solid #1a1e26', 
                    color: 'white',
                    fontSize: '14px',
                    outline: 'none',
                    resize: 'none',
                    transition: 'border 0.3s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'white'}
                  onBlur={(e) => e.target.style.borderColor = '#1a1e26'}
                  placeholder="Provide detailed environment assessment..."
                />
              </div>
              <button 
                onClick={handleCreateTicket}
                disabled={isLoading}
                style={{ 
                    background: 'white', 
                    color: 'black', 
                    border: 'none', 
                    padding: '16px', 
                    borderRadius: '12px', 
                    fontWeight: '900', 
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    transition: 'all 0.2s',
                    opacity: isLoading ? 0.7 : 1
                }}
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <>LAUNCH SUPPORT PROTOCOL <ArrowRight size={18} /></>}
              </button>
            </div>
          </div>
        ) : activeTicket ? (
          <>
            <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid #1a1e26', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.01)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '14px', border: '1px solid #1a1e26' }}>
                  <Ticket size={24} color="white" />
                </div>
                <div>
                  <div style={{ fontWeight: '800', fontSize: '1.15rem', color: 'white', letterSpacing: '0.5px' }}>{activeTicket.subject}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>TICKET ID #{activeTicket.id.toString().padStart(4, '0')} | SECURE CHANNEL</div>
                </div>
              </div>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto', padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }} className="custom-scrollbar">
              {messages.map(m => (
                <div 
                  key={m.id}
                  style={{ 
                    maxWidth: '70%',
                    alignSelf: m.sender_email === user.email ? 'flex-end' : 'flex-start',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ 
                      fontSize: '0.7rem', 
                      color: 'var(--text-muted)', 
                      fontWeight: '800', 
                      textTransform: 'uppercase', 
                      alignSelf: m.sender_email === user.email ? 'flex-end' : 'flex-start',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                  }}>
                    {m.sender_email === user.email ? <><ShieldCheck size={10} /> Operator</> : <><UserIcon size={10} /> Technical Support</>}
                  </div>
                  <div style={{ 
                    padding: '1.25rem 1.5rem',
                    borderRadius: '24px',
                    borderTopRightRadius: m.sender_email === user.email ? '4px' : '24px',
                    borderTopLeftRadius: m.sender_email === user.email ? '24px' : '4px',
                    background: m.sender_email === user.email ? 'white' : '#1a1e26',
                    color: m.sender_email === user.email ? 'black' : 'white',
                    fontSize: '0.9rem',
                    fontWeight: '500',
                    lineHeight: '1.5',
                    boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
                  }}>
                    {m.content}
                  </div>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '600', alignSelf: m.sender_email === user.email ? 'flex-end' : 'flex-start' }}>
                    {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <div style={{ padding: '1.5rem 2rem', background: 'rgba(0,0,0,0.15)', borderTop: '1px solid #1a1e26' }}>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <input 
                  type="text" 
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Formulate operational response..."
                  style={{ 
                      flex: 1, 
                      padding: '16px 20px', 
                      borderRadius: '16px', 
                      background: '#05070a', 
                      border: '1px solid #1a1e26', 
                      color: 'white', 
                      fontSize: '0.95rem',
                      outline: 'none'
                  }}
                />
                <button 
                  onClick={handleSendMessage}
                  style={{ 
                      width: '54px', 
                      height: '54px', 
                      borderRadius: '16px', 
                      background: 'white', 
                      color: 'black', 
                      border: 'none', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      boxShadow: '0 4px 15px rgba(255,255,255,0.1)'
                  }}
                >
                  <Send size={20} />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '1.5rem' }}>
            <div style={{ position: 'relative' }}>
                <MessageSquare size={64} style={{ opacity: 0.1 }} />
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Info size={24} style={{ opacity: 0.3 }} />
                </div>
            </div>
            <div style={{ textAlign: 'center' }}>
                <h3 style={{ fontSize: '1.2rem', color: 'white', fontWeight: '800', letterSpacing: '1px' }}>TERMINAL IDLE</h3>
                <p style={{ maxWidth: '300px', fontSize: '0.85rem', marginTop: '8px', color: 'var(--text-muted)' }}>Select an active protocol or initialize a new support session.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const ArrowRight = ({ size }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 12h14m-7-7 7 7-7 7" />
    </svg>
);
