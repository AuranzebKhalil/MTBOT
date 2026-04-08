"use client";
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../components/AuthContext';
import { getApiBaseUrl } from '../../lib/config';
import toast from 'react-hot-toast';
import { MessageSquare, Send, Clock, Ticket, User as UserIcon, CheckCircle, Info } from 'lucide-react';

export default function AdminSupportPage() {
  const [tickets, setTickets] = useState([]);
  const [activeTicket, setActiveTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const { token, user } = useAuth();
  const chatEndRef = useRef(null);

  const fetchTickets = async () => {
    const res = await fetch(`${getApiBaseUrl()}/v1/admin/tickets`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) setTickets(await res.json());
  };

  const fetchMessages = async (ticketId) => {
    const res = await fetch(`${getApiBaseUrl()}/v1/support/tickets/${ticketId}/messages`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) setMessages(await res.json());
  };

  useEffect(() => {
    if (token) fetchTickets();
  }, [token]);

  useEffect(() => {
    if (activeTicket) {
      fetchMessages(activeTicket.id);
      const interval = setInterval(() => fetchMessages(activeTicket.id), 4000);
      return () => clearInterval(interval);
    }
  }, [activeTicket, token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !activeTicket) return;
    const res = await fetch(`${getApiBaseUrl()}/v1/support/tickets/${activeTicket.id}/messages?content=${encodeURIComponent(newMessage)}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      setNewMessage("");
      fetchMessages(activeTicket.id);
    }
  };

  const handleCloseTicket = async (ticketId) => {
    if (!confirm("Close this ticket as resolved?")) return;
    const res = await fetch(`${getApiBaseUrl()}/v1/admin/tickets/${ticketId}/close`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      toast.success("Ticket closed and locked.");
      fetchTickets();
      if (activeTicket?.id === ticketId) setActiveTicket(null);
    }
  };

  return (
    <div style={{ padding: '1.5rem', height: 'calc(100vh - 120px)', display: 'flex', gap: '1.5rem', background: 'var(--background)' }}>
      {/* Sidebar: Global Ticket List */}
      <div style={{ 
        width: '400px', 
        background: 'rgba(255, 255, 255, 0.02)', 
        backdropFilter: 'blur(10px)',
        borderRadius: '28px', 
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 20px 40px rgba(0,0,0,0.2)'
      }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)', background: 'linear-gradient(to bottom, rgba(255,255,255,0.05), transparent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent)', boxShadow: '0 0 10px var(--accent)' }}></div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: '900', letterSpacing: '-0.5px' }}>Universal Console</h2>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-sub)', fontWeight: '500' }}>Active Support Ecosystem</p>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }} className="custom-scrollbar">
          {tickets.map(t => (
            <div 
              key={t.id}
              onClick={() => setActiveTicket(t)}
              style={{
                margin: '4px 0',
                padding: '1.5rem',
                borderRadius: '18px',
                border: activeTicket?.id === t.id ? '1px solid var(--accent)' : '1px solid transparent',
                cursor: 'pointer',
                background: activeTicket?.id === t.id ? 'rgba(0, 122, 255, 0.08)' : 'transparent',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
              className="hover:scale-[1.02] transition-transform"
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '1rem', fontWeight: '800', color: activeTicket?.id === t.id ? 'var(--accent)' : 'var(--text-main)' }}>{t.subject}</span>
                <span style={{ 
                  fontSize: '0.65rem', 
                  padding: '3px 10px', 
                  borderRadius: '20px', 
                  background: t.status === 'open' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)',
                  color: t.status === 'open' ? '#10b981' : 'var(--text-sub)',
                  fontWeight: '800',
                  textTransform: 'uppercase',
                  border: t.status === 'open' ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.1)'
                }}>
                  {t.status}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-sub)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                   <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                     <UserIcon size={10} />
                   </div>
                   {t.user_email}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-sub)', opacity: 0.6 }}>
                  {new Date(t.updated_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Interface */}
      <div style={{ 
        flex: 1, 
        background: 'rgba(255, 255, 255, 0.01)',
        backdropFilter: 'blur(20px)',
        borderRadius: '28px', 
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 30px 60px rgba(0,0,0,0.3)'
      }}>
        {activeTicket ? (
          <>
            <header style={{ 
              padding: '1.8rem 2.5rem', 
              borderBottom: '1px solid var(--glass-border)', 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              background: 'linear-gradient(to right, rgba(0,0,0,0.2), transparent)' 
            }}>
               <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem' }}>
                  <div style={{ 
                    padding: '14px', 
                    background: 'linear-gradient(135deg, var(--accent) 0%, #00f2ff 100%)', 
                    borderRadius: '16px', 
                    color: 'white',
                    boxShadow: '0 8px 25px rgba(0, 122, 255, 0.4)' 
                  }}>
                    <MessageSquare size={22} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.3rem', fontWeight: '900', letterSpacing: '-0.5px' }}>{activeTicket.subject}</h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-sub)', fontWeight: '500' }}>
                      <span style={{ color: 'var(--accent)' }}>ID: #{activeTicket.id}</span> • Client Registry: {activeTicket.user_email}
                    </p>
                  </div>
               </div>
               <button 
                onClick={() => handleCloseTicket(activeTicket.id)}
                style={{ 
                  background: 'rgba(16, 185, 129, 0.1)', 
                  color: '#10b981', 
                  border: '1px solid #10b981', 
                  padding: '12px 24px', 
                  borderRadius: '14px', 
                  fontWeight: '800', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                className="hover-lift"
               >
                 <CheckCircle size={18} /> Mark Resolved
               </button>
            </header>

            <div style={{ flex: 1, overflowY: 'auto', padding: '2.5rem', display: 'flex', flexDirection: 'column', gap: '1.2rem' }} className="custom-scrollbar">
               {messages.map(m => {
                 const isSelf = m.sender_email === user.email;
                 return (
                  <div 
                    key={m.id}
                    style={{
                      maxWidth: '70%',
                      alignSelf: isSelf ? 'flex-end' : 'flex-start',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px'
                    }}
                  >
                    <div style={{ 
                      fontSize: '0.75rem', 
                      fontWeight: '800',
                      color: isSelf ? 'var(--accent)' : 'var(--text-sub)', 
                      marginBottom: '2px', 
                      alignSelf: isSelf ? 'flex-end' : 'flex-start',
                      letterSpacing: '0.5px'
                    }}>
                       {isSelf ? 'ALPHA OVERSEER' : 'CLIENT'}
                    </div>
                    <div style={{
                      padding: '16px 22px',
                      borderRadius: isSelf ? '22px 22px 4px 22px' : '22px 22px 22px 4px',
                      background: isSelf ? 'linear-gradient(135deg, var(--accent) 0%, #0066cc 100%)' : 'rgba(255,255,255,0.03)',
                      border: isSelf ? 'none' : '1px solid var(--glass-border)',
                      color: '#fff',
                      fontSize: '1rem',
                      lineHeight: '1.6',
                      boxShadow: isSelf ? '0 10px 30px rgba(0, 122, 255, 0.2)' : 'none'
                    }}>
                      {m.content}
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-sub)', opacity: 0.5, alignSelf: isSelf ? 'flex-end' : 'flex-start' }}>
                      {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
               )})}
               <div ref={chatEndRef} />
            </div>

            <div style={{ padding: '2rem 2.5rem', background: 'rgba(0,0,0,0.3)', borderTop: '1px solid var(--glass-border)' }}>
              <div style={{ display: 'flex', gap: '1.2rem', alignItems: 'center' }}>
                <input 
                  type="text" 
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Initiate administrative directive..."
                  style={{ 
                    flex: 1, 
                    padding: '16px 24px', 
                    borderRadius: '16px', 
                    background: 'rgba(255,255,255,0.02)', 
                    border: '1px solid var(--glass-border)', 
                    color: '#fff', 
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
                />
                <button 
                  onClick={handleSendMessage}
                  style={{ 
                    background: 'var(--accent)', 
                    color: '#000', 
                    border: 'none', 
                    width: '58px', 
                    height: '58px', 
                    borderRadius: '16px', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    cursor: 'pointer',
                    boxShadow: '0 8px 25px rgba(0, 122, 255, 0.3)',
                    transition: 'all 0.2s'
                  }}
                  className="hover:scale-105"
                >
                  <Send size={22} color="#fff" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2rem', color: 'var(--text-sub)' }}>
             <div style={{ 
               width: '120px', 
               height: '120px', 
               borderRadius: '40px', 
               background: 'rgba(255,255,255,0.01)', 
               display: 'flex', 
               alignItems: 'center', 
               justifyContent: 'center',
               border: '1px solid var(--glass-border)'
             }}>
               <Info size={48} opacity={0.2} />
             </div>
             <div style={{ textAlign: 'center' }}>
               <h3 style={{ fontSize: '1.8rem', color: 'var(--text-main)', fontWeight: '900', letterSpacing: '-0.5px' }}>Command Center Ready</h3>
               <p style={{ maxWidth: '340px', lineHeight: '1.6', fontSize: '0.95rem' }}>Awaiting administrative engagement. Select a communication channel from the registry to begin.</p>
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
