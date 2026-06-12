'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/auth/me', {
          credentials: 'include',
        });
        if (!res.ok) {
          throw new Error('Not authenticated');
        }
        const data = await res.json();
        setUser(data);
      } catch (err) {
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, [router]);

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout request failed:', err);
    }
    router.push('/login');
    router.refresh();
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div className="loading-spinner" style={{ width: '2.5rem', height: '2.5rem' }}></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div style={{
      padding: '3rem 1.5rem',
      maxWidth: '800px',
      margin: '0 auto',
      width: '100%',
      zIndex: 1,
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      minHeight: '100vh'
    }}>
      <div className="glass-card" style={{ padding: '3rem 2rem', width: '100%' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2.5rem',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <h1 className="neon-title" style={{ fontSize: '2.5rem', marginBottom: '0.25rem' }}>AEGIS</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>Secure VPN Management System</p>
          </div>
          <button
            onClick={handleLogout}
            className="btn-primary"
            style={{
              width: 'auto',
              padding: '0.5rem 1.25rem',
              background: 'rgba(244, 63, 94, 0.15)',
              color: 'var(--accent-rose)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              boxShadow: 'none'
            }}
          >
            Logout
          </button>
        </div>

        {/* User Session Specs */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.01)',
          padding: '1.5rem',
          borderRadius: '12px',
          border: '1px solid var(--border-light)',
          marginBottom: '2.5rem'
        }}>
          <h2 style={{ fontSize: '1.15rem', marginBottom: '1.25rem', color: 'var(--accent-indigo)', fontWeight: 600 }}>
            Session Security Info
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: '0.75rem 0', fontSize: '0.95rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Authenticated User</span>
            <span style={{ fontWeight: 500 }}>{user.username}</span>

            <span style={{ color: 'var(--text-secondary)' }}>Security Role</span>
            <span style={{
              fontWeight: 600,
              color: user.role === 'admin' ? 'var(--accent-teal)' : 'var(--accent-indigo)'
            }}>
              {user.role.toUpperCase()}
            </span>

            <span style={{ color: 'var(--text-secondary)' }}>Account Status</span>
            <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>ACTIVE</span>
          </div>
        </div>

        {/* System Phase Status Blocks */}
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div className="glass-card" style={{
            flex: '1 1 280px',
            padding: '1.5rem',
            background: 'rgba(99, 102, 241, 0.03)',
            borderColor: 'rgba(99, 102, 241, 0.1)'
          }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent-indigo)' }}>
              Phase 1 Completed
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Database models configured, secure HTTP-only cookies verification operational, and Role-Based Access Control activated successfully.
            </p>
          </div>

          <div className="glass-card" style={{
            flex: '1 1 280px',
            padding: '1.5rem',
            background: 'rgba(20, 184, 166, 0.03)',
            borderColor: 'rgba(20, 184, 166, 0.1)'
          }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: 'var(--accent-teal)' }}>
              Phase 2 Ready
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Next milestones include WireGuard endpoint integration, client configuration provisioning, and real-time interface connection updates.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
