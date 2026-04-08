"use client";
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../components/AuthContext';
import { getApiBaseUrl } from '../../lib/config';
import toast from 'react-hot-toast';
import { ShieldAlert, ShieldCheck, User as UserIcon, TrendingUp, Wallet, Eye } from 'lucide-react';

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      }
    } catch (err) {
      toast.error("Failed to fetch ecosystem users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchUsers();
  }, [token]);

  const handleBreach = async (userId, email, isCurrentlyBreached) => {
    const action = isCurrentlyBreached ? 'unbreach' : 'breach';
    const confirmMsg = isCurrentlyBreached 
      ? `Are you sure you want to RESTORE access for ${email}?` 
      : `CRITICAL: Are you sure you want to BREACH and LOCK ${email}? This will suspend all trading activity immediately.`;
    
    if (!confirm(confirmMsg)) return;

    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/admin/users/${userId}/${action}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success(`Account ${action}ed successfully`);
        fetchUsers();
      } else {
        toast.error(`Fault during ${action} operation`);
      }
    } catch (err) {
      toast.error("Network fault in security bridge");
    }
  };

  if (loading) return <div className="p-8 text-center text-muted">Scanning User Ecosystem...</div>;

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2rem', color: 'var(--text-main)', fontWeight: '800' }}>User Management</h1>
          <p style={{ color: 'var(--text-muted)' }}>Managing {users.length} active alpha accounts</p>
        </div>
      </header>

      <div style={{ 
        background: 'var(--bg-card)', 
        borderRadius: '24px', 
        border: '1px solid var(--border)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-main)'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.02)' }}>
              <th style={{ padding: '1.5rem', color: 'var(--text-muted)' }}>User / Identity</th>
              <th style={{ padding: '1.5rem', color: 'var(--text-muted)' }}>Financial Data</th>
              <th style={{ padding: '1.5rem', color: 'var(--text-muted)' }}>Security Status</th>
              <th style={{ padding: '1.5rem', color: 'var(--text-muted)', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.2s' }} className="hover:bg-white/5">
                <td style={{ padding: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ 
                      width: '40px', 
                      height: '40px', 
                      borderRadius: '12px', 
                      background: 'var(--accent)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: 'white'
                    }}>
                      <UserIcon size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', color: 'var(--text-main)' }}>{u.username || 'Quantum User'}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{u.email}</div>
                    </div>
                  </div>
                </td>
                <td style={{ padding: '1.5rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: u.total_profit >= 0 ? '#10b981' : '#ef4444' }}>
                      <TrendingUp size={14} />
                      <span style={{ fontWeight: '700' }}>${u.total_profit?.toLocaleString() || '0'}</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Wallet size={12} />
                      Bal: ${u.current_balance?.toLocaleString() || '0'}
                    </div>
                  </div>
                </td>
                <td style={{ padding: '1.5rem' }}>
                  <span style={{ 
                    padding: '6px 12px', 
                    borderRadius: '8px', 
                    fontSize: '0.75rem', 
                    fontWeight: '800',
                    textTransform: 'uppercase',
                    background: u.is_breached ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                    color: u.is_breached ? '#ef4444' : '#10b981',
                    border: `1px solid ${u.is_breached ? '#ef4444' : '#10b981'}`
                  }}>
                    {u.is_breached ? 'Account Breached' : 'Secure'}
                  </span>
                </td>
                <td style={{ padding: '1.5rem', textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    <button 
                      onClick={() => handleBreach(u.id, u.email, u.is_breached)}
                      style={{
                        padding: '10px',
                        borderRadius: '12px',
                        background: u.is_breached ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: u.is_breached ? '#10b981' : '#ef4444',
                        border: 'none',
                        cursor: 'pointer'
                      }}
                      title={u.is_breached ? "Restore Access" : "Breach Account"}
                    >
                      {u.is_breached ? <ShieldCheck size={18} /> : <ShieldAlert size={18} />}
                    </button>
                    <button style={{
                      padding: '10px',
                      borderRadius: '12px',
                      background: 'rgba(255,255,255,0.05)',
                      color: 'var(--text-main)',
                      border: 'none',
                      cursor: 'pointer'
                    }}>
                      <Eye size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
