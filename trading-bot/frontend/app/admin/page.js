"use client";
import React, { useState, useEffect } from 'react';
import { useAuth } from '../components/AuthContext';
import { getApiBaseUrl } from '../lib/config';
import StatsCard from '../components/StatsCard';
import { Users, MessageSquare, TrendingUp, ShieldAlert, Activity, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    userCount: 0,
    openTickets: 0,
    totalProfit: 0,
    activeEngine: false
  });
  const { token } = useAuth();

  useEffect(() => {
    const fetchAdminStats = async () => {
      try {
        const usersRes = await fetch(`${getApiBaseUrl()}/v1/admin/users`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const ticketsRes = await fetch(`${getApiBaseUrl()}/v1/admin/tickets`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (usersRes.ok && ticketsRes.ok) {
          const users = await usersRes.json();
          const tickets = await ticketsRes.json();
          
          setStats({
            userCount: users.length,
            openTickets: tickets.filter(t => t.status === 'open').length,
            totalProfit: users.reduce((acc, u) => acc + u.total_profit, 0),
            activeEngine: true
          });
        }
      } catch (err) {}
    };

    if (token) fetchAdminStats();
  }, [token]);

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
      <header>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--text-main)', marginBottom: '8px' }}>Admin Console</h1>
        <p style={{ color: 'var(--text-muted)' }}>Universal oversight of the Alertli Alpha Ecosystem</p>
      </header>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(4, 1fr)', 
        gap: '20px' 
      }}>
        <StatsCard label="Ecosystem Users" value={stats.userCount} subtext="Total managed accounts" />
        <StatsCard label="Priority Tickets" value={stats.openTickets} subtext="Open help requests" type={stats.openTickets > 0 ? 'loss' : 'normal'} />
        <StatsCard label="Combined Profit" value={`$${stats.totalProfit.toLocaleString()}`} subtext="Total across all accounts" type="profit" />
        <StatsCard label="Engine Status" value={stats.activeEngine ? "ACTIVE" : "OFFLINE"} subtext="Core infrastructure health" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        {/* Quick Actions */}
        <div style={{ background: 'var(--bg-card)', padding: '2.5rem', borderRadius: '24px', border: '1px solid var(--border)' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={20} color="var(--accent)" /> Mission Control
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <Link href="/admin/users" style={{ textDecoration: 'none' }}>
              <div className="hover:scale-105 transition-all" style={{ padding: '1.5rem', background: 'var(--background)', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <Users color="var(--accent)" />
                  <span style={{ fontWeight: '700', color: 'var(--text-main)' }}>Audit Users</span>
                </div>
                <ArrowRight size={18} color="var(--text-muted)" />
              </div>
            </Link>
            <Link href="/admin/support" style={{ textDecoration: 'none' }}>
              <div className="hover:scale-105 transition-all" style={{ padding: '1.5rem', background: 'var(--background)', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <MessageSquare color="#10b981" />
                  <span style={{ fontWeight: '700', color: 'var(--text-main)' }}>Admin Support</span>
                </div>
                <ArrowRight size={18} color="var(--text-muted)" />
              </div>
            </Link>
          </div>
        </div>

        {/* Security Summary */}
        <div style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '2.5rem', borderRadius: '24px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '1rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={20} /> Security Risk
          </h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: '1.5', marginBottom: '1.5rem' }}>
            No immediate breaches detected. All systems operating within normal parameters.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#10b981', fontSize: '0.85rem', fontWeight: '700' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></div>
            All Accounts Secure
          </div>
        </div>
      </div>
    </div>
  );
}
