'use client';

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { QRCodeSVG } from 'qrcode.react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  Globe,
  History,
  KeyRound,
  LayoutDashboard,
  Lock,
  LogOut,
  Play,
  Plus,
  RefreshCw,
  Shield,
  ShieldCheck,
  ShieldX,
  Users,
  XCircle,
  Zap,
} from 'lucide-react';

// ─────────────────── Helpers ───────────────────

function formatDate(value: string | null) {
  if (!value) return '-';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatBytes(value: number = 0) {
  if (value < 1024) return `${value} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let size = value / 1024;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(size >= 10 ? 1 : 2)} ${units[index]}`;
}

function StatusPill({ value }: { value: any }) {
  const active = ['online', 'open', 'admin', 'active', true].includes(value);
  return (
    <span className={`pill ${active ? 'pill-good' : 'pill-muted'}`}>
      {String(value).toUpperCase()}
    </span>
  );
}

// ─────────────────── API Helper ───────────────────

async function apiFetch(path: string, options: any = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`http://localhost:8000${path}`, {
    ...options,
    headers,
    credentials: 'include',
    body: options.body && typeof options.body !== 'string' ? JSON.stringify(options.body) : options.body,
  });

  if (res.status === 204) return null;
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    let message = `Request failed with ${res.status}`;
    if (contentType.includes('application/json')) {
      const data = await res.json();
      if (data && data.detail) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail.map((d: any) => {
            if (d && typeof d === 'object') {
              const field = d.loc ? d.loc.join('.') : '';
              return field ? `${field}: ${d.msg}` : (d.msg || JSON.stringify(d));
            }
            return String(d);
          }).join(', ');
        } else if (typeof data.detail === 'object') {
          message = data.detail.message || JSON.stringify(data.detail);
        }
      }
    }
    throw new Error(message);
  }
  if (contentType.includes('application/json')) return res.json();
  return res.text();
}

async function downloadFile(path: string, filename: string) {
  const res = await fetch(`http://localhost:8000${path}`, {
    credentials: 'include',
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || `Download failed with status ${res.status}`);
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// Smooth-scroll to a section by ID
function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─────────────────── Shared UI Components ───────────────────

function ErrorBanner({ message, onClose }: { message: string; onClose: () => void }) {
  if (!message) return null;
  return (
    <div className="alert-card alert-danger" style={{ justifyContent: 'space-between', width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <AlertTriangle size={18} />
        <span>{message}</span>
      </div>
      <button onClick={onClose} style={{ background: 'transparent', color: 'inherit', border: 'none', cursor: 'pointer' }}>
        <XCircle size={18} />
      </button>
    </div>
  );
}

// Accent colors for stat icon backgrounds
const ACCENT_COLORS: Record<string, { bg: string; fg: string }> = {
  blue:   { bg: 'rgba(59, 130, 246, 0.12)', fg: 'var(--accent-blue)' },
  green:  { bg: 'rgba(16, 185, 129, 0.12)', fg: 'var(--accent-emerald)' },
  violet: { bg: 'rgba(139, 92, 246, 0.12)', fg: 'var(--accent-purple)' },
  amber:  { bg: 'rgba(245, 158, 11, 0.12)', fg: 'var(--accent-amber)' },
  red:    { bg: 'rgba(244, 63, 94, 0.12)',  fg: 'var(--accent-rose)' },
  teal:   { bg: 'rgba(20, 184, 166, 0.12)', fg: 'var(--accent-teal)' },
  indigo: { bg: 'rgba(99, 102, 241, 0.12)', fg: 'var(--accent-indigo)' },
};

function StatCard({ icon: Icon, label, value, accent }: { icon: any; label: string; value: any; accent: string }) {
  const colors = ACCENT_COLORS[accent] || ACCENT_COLORS.indigo;
  return (
    <div className="stat-card">
      <div className="stat-icon-wrap" style={{ background: colors.bg }}>
        <Icon size={20} style={{ color: colors.fg }} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ icon: Icon, title, hint }: { icon: any; title: string; hint: string }) {
  return (
    <div className="empty-state">
      <Icon size={36} />
      <div className="empty-title">{title}</div>
      <div className="empty-hint">{hint}</div>
    </div>
  );
}

// ─────────────────── Sidebar Navigation ───────────────────

interface NavConfig {
  icon: any;
  label: string;
  target: string;
}

function SidebarNav({ items }: { items: NavConfig[] }) {
  return (
    <nav className="nav-menu">
      <div className="nav-label">Navigation</div>
      {items.map((item) => (
        <button
          key={item.target}
          className="nav-item"
          onClick={() => scrollTo(item.target)}
        >
          <item.icon size={18} />
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

const ADMIN_NAV: NavConfig[] = [
  { icon: LayoutDashboard, label: 'Overview',         target: 'section-stats' },
  { icon: Users,           label: 'User Management',  target: 'section-users' },
  { icon: Shield,          label: 'VPN Profiles',     target: 'section-vpn' },
  { icon: Activity,        label: 'Live Connections',  target: 'section-sessions' },
  { icon: AlertTriangle,   label: 'Security Alerts',  target: 'section-alerts' },
];

const USER_NAV: NavConfig[] = [
  { icon: Globe,   label: 'My VPN Config',     target: 'section-profile' },
  { icon: Lock,    label: '2FA Security',       target: 'section-mfa' },
  { icon: History, label: 'Connection History', target: 'section-history' },
];

const AUDITOR_NAV: NavConfig[] = [
  { icon: FileText,      label: 'Audit Logs',      target: 'section-logs' },
  { icon: Zap,           label: 'Security Events',  target: 'section-events' },
  { icon: AlertTriangle, label: 'Threat Alerts',    target: 'section-threats' },
];

// ─────────────────── ADMIN DASHBOARD ───────────────────

function AdminDashboard() {
  const [stats, setStats] = useState<any>({});
  const [users, setUsers] = useState<any[]>([]);
  const [profiles, setProfiles] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // Forms
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('AdminSecurePass123!');
  const [newUserRole, setNewUserRole] = useState('user');

  const [mockUserId, setMockUserId] = useState('');
  const [mockIP, setMockIP] = useState('203.0.113.10');
  const [mockDevice, setMockDevice] = useState('demo-laptop');
  const [mockUpload, setMockUpload] = useState(12000000);
  const [mockDownload, setMockDownload] = useState(45000000);
  const [mockStatus, setMockStatus] = useState('online');

  const loadData = useCallback(async () => {
    setError('');
    try {
      const [dash, userRows, profileRows, sessionRows, alertRows] = await Promise.all([
        apiFetch('/api/admin/dashboard'),
        apiFetch('/api/users'),
        apiFetch('/api/vpn/profiles'),
        apiFetch('/api/sessions'),
        apiFetch('/api/threats/alerts'),
      ]);
      setStats(dash.stats || {});
      setUsers(userRows || []);
      setProfiles(profileRows || []);
      setSessions(sessionRows || []);
      setAlerts(alertRows || []);
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await apiFetch('/api/users', {
        method: 'POST',
        body: {
          email: newUserEmail,
          username: newUsername,
          password: newUserPassword,
          role: newUserRole,
        },
      });
      setNewUserEmail('');
      setNewUsername('');
      setNewUserPassword('AdminSecurePass123!');
      loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const toggleUserStatus = async (user: any) => {
    try {
      const endpoint = user.is_active ? 'disable' : 'enable';
      await apiFetch(`/api/users/${user.id}/${endpoint}`, { method: 'POST' });
      loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateProfile = async (userId: string) => {
    try {
      await apiFetch(`/api/vpn/users/${userId}/profile`, { method: 'POST', body: {} });
      loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleRevokeProfile = async (profileId: string) => {
    try {
      await apiFetch(`/api/vpn/profiles/${profileId}/revoke`, { method: 'POST' });
      loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateMockSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await apiFetch('/api/sessions/mock', {
        method: 'POST',
        body: {
          user_id: mockUserId,
          source_ip: mockIP,
          device: mockDevice,
          upload_bytes: Number(mockUpload),
          download_bytes: Number(mockDownload),
          status: mockStatus,
        },
      });
      loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await apiFetch(`/api/threats/alerts/${alertId}/resolve`, { method: 'PATCH' });
      loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const activeProfilesCount = useMemo(() => profiles.filter((p) => p.is_active).length, [profiles]);

  return (
    <>
      <header className="page-header">
        <div>
          <p>System Administrator</p>
          <h2>Operations Dashboard</h2>
        </div>
        <button className="ghost-btn" onClick={loadData}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <ErrorBanner message={error} onClose={() => setError('')} />

      {/* Welcome Banner */}
      <div className="welcome-banner">
        <div className="welcome-text">
          <h3>Welcome back, Administrator</h3>
          <p>Manage users, VPN profiles, monitor connections, and review security alerts from this dashboard. Use the sidebar to jump to any section.</p>
        </div>
        <div className="welcome-actions">
          <button className="btn-primary" style={{ width: 'auto' }} onClick={() => scrollTo('section-users')}>
            <Plus size={16} />
            Create User
          </button>
          <button className="ghost-btn" onClick={loadData}>
            <RefreshCw size={16} />
            Refresh All
          </button>
        </div>
      </div>

      {/* Stats Section */}
      <section id="section-stats" className="stat-grid">
        <StatCard icon={Users} label="Total Users" value={stats.total_users ?? '-'} accent="blue" />
        <StatCard icon={ShieldCheck} label="Active VPN Users" value={stats.active_vpn_users ?? '-'} accent="green" />
        <StatCard icon={Activity} label="Active Sessions" value={stats.active_sessions ?? '-'} accent="violet" />
        <StatCard icon={AlertTriangle} label="Failed Logins Today" value={stats.failed_logins_today ?? '-'} accent="amber" />
        <StatCard icon={ShieldX} label="Open Alerts" value={stats.alerts ?? '-'} accent="red" />
      </section>

      {/* Content Blocks */}
      <div className="content-grid">
        {/* User Management */}
        <section id="section-users" className="glass-card panel">
          <div className="panel-head">
            <h3>User Management</h3>
          </div>
          <form className="grid-form" onSubmit={handleCreateUser}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                placeholder="email@example.com"
                type="email"
                value={newUserEmail}
                onChange={(e) => setNewUserEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Username</label>
              <input
                placeholder="username"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                placeholder="password"
                type="password"
                value={newUserPassword}
                onChange={(e) => setNewUserPassword(e.target.value)}
                required
                minLength={12}
              />
            </div>
            <div className="form-group">
              <label>Role</label>
              <select value={newUserRole} onChange={(e) => setNewUserRole(e.target.value)}>
                <option value="user">User</option>
                <option value="admin">Admin</option>
                <option value="auditor">Auditor</option>
              </select>
            </div>
            <div className="form-group">
              <button className="btn-primary" type="submit" disabled={busy}>
                <Plus size={16} />
                Add User
              </button>
            </div>
          </form>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState
                        icon={Users}
                        title="No users registered"
                        hint="Use the form above to create the first user account."
                      />
                    </td>
                  </tr>
                ) : (
                  users.map((row) => (
                    <tr key={row.id}>
                      <td>{row.username}</td>
                      <td>
                        <StatusPill value={row.role} />
                      </td>
                      <td>
                        <StatusPill value={row.is_active ? 'active' : 'disabled'} />
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            className={`icon-text-btn ${row.is_active ? 'danger' : ''}`}
                            onClick={() => toggleUserStatus(row)}
                          >
                            {row.is_active ? <ShieldX size={14} /> : <CheckCircle2 size={14} />}
                            {row.is_active ? 'Disable' : 'Enable'}
                          </button>
                          <button
                            className="icon-text-btn"
                            onClick={() => handleCreateProfile(row.id)}
                            disabled={!row.is_active || row.is_vpn_enabled}
                          >
                            <KeyRound size={14} />
                            Provision
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* VPN Profiles */}
        <section id="section-vpn" className="glass-card panel">
          <div className="panel-head">
            <h3>VPN Access Profiles</h3>
            <span>{activeProfilesCount} active tunnels</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Assigned IP</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {profiles.length === 0 ? (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState
                        icon={Shield}
                        title="No VPN profiles provisioned"
                        hint="Go to User Management and click 'Provision' on a user to create their VPN profile."
                      />
                    </td>
                  </tr>
                ) : (
                  profiles.map((row) => (
                    <tr key={row.id}>
                      <td>{row.username}</td>
                      <td>{row.assigned_ip}</td>
                      <td>
                        <StatusPill value={row.is_active ? 'active' : 'revoked'} />
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            className="icon-text-btn"
                            onClick={() => downloadFile(`/api/vpn/profiles/${row.id}/config`, `profile-${row.username}.conf`)}
                            disabled={!row.is_active}
                          >
                            <Download size={14} />
                            Config
                          </button>
                          {row.is_active && (
                            <button className="icon-text-btn danger" onClick={() => handleRevokeProfile(row.id)}>
                              <ShieldX size={14} />
                              Revoke
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div className="content-grid">
        {/* Mock Session and Connection Tracking */}
        <section id="section-sessions" className="glass-card panel">
          <div className="panel-head">
            <h3>Live VPN Connections</h3>
          </div>
          <form className="grid-form" onSubmit={handleCreateMockSession}>
            <div className="form-group">
              <label>VPN User</label>
              <select value={mockUserId} onChange={(e) => setMockUserId(e.target.value)} required>
                <option value="">Select User</option>
                {users.filter(u => u.is_vpn_enabled && u.is_active).map((user) => (
                  <option key={user.id} value={user.id}>{user.username}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Source IP</label>
              <input value={mockIP} onChange={(e) => setMockIP(e.target.value)} placeholder="Source IP" required />
            </div>
            <div className="form-group">
              <label>Device Name</label>
              <input value={mockDevice} onChange={(e) => setMockDevice(e.target.value)} placeholder="Device" required />
            </div>
            <div className="form-group">
              <label>Upload (Bytes)</label>
              <input type="number" value={mockUpload} onChange={(e) => setMockUpload(Number(e.target.value))} placeholder="Upload bytes" required />
            </div>
            <div className="form-group">
              <label>Download (Bytes)</label>
              <input type="number" value={mockDownload} onChange={(e) => setMockDownload(Number(e.target.value))} placeholder="Download bytes" required />
            </div>
            <div className="form-group">
              <label>Status</label>
              <select value={mockStatus} onChange={(e) => setMockStatus(e.target.value)}>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
              </select>
            </div>
            <div className="form-group">
              <button className="btn-primary" type="submit" disabled={busy}>
                <Play size={16} />
                Mock Connect
              </button>
            </div>
          </form>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>IP</th>
                  <th>Device</th>
                  <th>Usage (U/D)</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length === 0 ? (
                  <tr>
                    <td colSpan={5}>
                      <EmptyState
                        icon={Activity}
                        title="No connection history"
                        hint="Connections will appear here once users connect through the VPN tunnel."
                      />
                    </td>
                  </tr>
                ) : (
                  sessions.map((row, index) => (
                    <tr key={row.id || index}>
                      <td>{row.username}</td>
                      <td>{row.source_ip}</td>
                      <td>{row.device}</td>
                      <td>{formatBytes(row.upload_bytes)} / {formatBytes(row.download_bytes)}</td>
                      <td>
                        <StatusPill value={row.status} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Security Alerts */}
        <section id="section-alerts" className="glass-card panel">
          <div className="panel-head">
            <h3>Active Security Alerts</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts.length === 0 ? (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState
                        icon={ShieldCheck}
                        title="No active threats"
                        hint="The system is secure. Threats will be listed here when detected."
                      />
                    </td>
                  </tr>
                ) : (
                  alerts.map((row) => (
                    <tr key={row.id}>
                      <td style={{ fontSize: '0.85rem' }}>{row.title}</td>
                      <td>
                        <StatusPill value={row.severity} />
                      </td>
                      <td>
                        <StatusPill value={row.status} />
                      </td>
                      <td>
                        {row.status === 'open' && (
                          <button className="icon-text-btn" onClick={() => handleResolveAlert(row.id)}>
                            <CheckCircle2 size={14} />
                            Resolve
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </>
  );
}

// ─────────────────── USER DASHBOARD ───────────────────

function UserDashboard({ user, onUserUpdate }: { user: any; onUserUpdate: () => void }) {
  const [profile, setProfile] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [mfaSecret, setMfaSecret] = useState<string | null>(null);
  const [mfaUri, setMfaUri] = useState<string | null>(null);
  const [mfaVerifyCode, setMfaVerifyCode] = useState('');
  const [localSuccess, setLocalSuccess] = useState('');

  const loadData = useCallback(async () => {
    setError('');
    try {
      const sessionRows = await apiFetch('/api/sessions/me');
      setSessions(sessionRows || []);
      try {
        const prof = await apiFetch('/api/vpn/my-profile');
        setProfile(prof);
      } catch {
        setProfile(null);
      }
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  const handleMfaEnroll = async () => {
    setError('');
    setLocalSuccess('');
    try {
      const data = await apiFetch('/api/auth/mfa/enroll', { method: 'POST' });
      setMfaSecret(data.secret);
      setMfaUri(data.provisioning_uri);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleMfaVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLocalSuccess('');
    try {
      await apiFetch('/api/auth/mfa/verify', {
        method: 'POST',
        body: { code: mfaVerifyCode }
      });
      setMfaSecret(null);
      setMfaUri(null);
      setMfaVerifyCode('');
      setLocalSuccess('Multi-Factor Authentication enabled successfully!');
      if (onUserUpdate) onUserUpdate();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleMfaDisable = async () => {
    if (!confirm('Are you sure you want to disable 2FA? This will decrease your account security.')) {
      return;
    }
    setError('');
    setLocalSuccess('');
    try {
      await apiFetch('/api/auth/mfa/disable', { method: 'POST' });
      setLocalSuccess('2FA has been disabled.');
      if (onUserUpdate) onUserUpdate();
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <>
      <header className="page-header">
        <div>
          <p>User Portal</p>
          <h2>VPN Configuration Access</h2>
        </div>
        <button className="ghost-btn" onClick={loadData}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>

      <ErrorBanner message={error} onClose={() => setError('')} />

      {/* Quick Actions Guide */}
      <div className="quick-actions-grid">
        <div className="quick-action-card" onClick={() => scrollTo('section-profile')}>
          <div className="qa-icon" style={{ background: 'rgba(59, 130, 246, 0.12)' }}>
            <Download size={20} style={{ color: 'var(--accent-blue)' }} />
          </div>
          <h4>Download VPN Config</h4>
          <p>Get your WireGuard configuration file to connect securely.</p>
        </div>
        <div className="quick-action-card" onClick={() => scrollTo('section-mfa')}>
          <div className="qa-icon" style={{ background: 'rgba(139, 92, 246, 0.12)' }}>
            <Lock size={20} style={{ color: 'var(--accent-purple)' }} />
          </div>
          <h4>Enable 2FA Security</h4>
          <p>Add an extra layer of protection with authenticator app verification.</p>
        </div>
        <div className="quick-action-card" onClick={() => scrollTo('section-history')}>
          <div className="qa-icon" style={{ background: 'rgba(16, 185, 129, 0.12)' }}>
            <History size={20} style={{ color: 'var(--accent-emerald)' }} />
          </div>
          <h4>Connection History</h4>
          <p>Review your past VPN sessions, devices, and traffic usage.</p>
        </div>
      </div>

      {/* VPN Profile Strip */}
      <section id="section-profile" className="profile-strip">
        <div>
          <span>VPN Address IP</span>
          <strong>{profile ? profile.assigned_ip : 'Not Provisioned'}</strong>
        </div>
        <div>
          <span>Endpoint Gateway</span>
          <strong>{profile ? profile.endpoint : '-'}</strong>
        </div>
        <button
          className="btn-primary"
          disabled={!profile || !profile.is_active}
          onClick={() => downloadFile('/api/vpn/my-profile/config', 'wireguard-client.conf')}
          style={{ width: 'auto' }}
        >
          <Download size={18} />
          Download Config (.conf)
        </button>
      </section>

      {/* 2FA Enrollment Panel */}
      <section id="section-mfa" className="glass-card panel">
        <div className="panel-head">
          <h3>Multi-Factor Authentication (2FA)</h3>
          <span className={`pill ${user.is_mfa_enabled ? 'pill-good' : 'pill-muted'}`}>
            {user.is_mfa_enabled ? 'ACTIVE' : 'INACTIVE'}
          </span>
        </div>

        {localSuccess && (
          <div className="alert-card alert-success" style={{ marginBottom: '1.5rem', width: '100%' }}>
            <CheckCircle2 size={18} />
            <span>{localSuccess}</span>
          </div>
        )}

        {!user.is_mfa_enabled ? (
          !mfaSecret ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1rem 0' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                Protect your account by adding an extra layer of security. When enabled, you will be prompted for a 6-digit verification code from your authenticator app upon logging in.
              </p>
              <button className="btn-primary" onClick={handleMfaEnroll} style={{ width: 'auto', alignSelf: 'flex-start' }}>
                <Lock size={16} />
                Enable 2FA
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', padding: '1rem 0', alignItems: 'center' }}>
              <div style={{ background: '#fff', padding: '1rem', borderRadius: '0.75rem', display: 'inline-block' }}>
                <QRCodeSVG value={mfaUri || ''} size={160} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, minWidth: '280px' }}>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                  1. Scan this QR code with Google Authenticator, Duo, or any TOTP app.
                </p>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Or enter key manually: <code style={{ color: 'var(--accent-indigo)', background: 'rgba(99, 102, 241, 0.1)', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', marginLeft: '0.5rem', wordBreak: 'break-all' }}>{mfaSecret}</code>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                  2. Enter the 6-digit code shown in your app to verify and activate 2FA:
                </p>
                <form onSubmit={handleMfaVerify} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    placeholder="e.g. 123456"
                    value={mfaVerifyCode}
                    onChange={(e) => setMfaVerifyCode(e.target.value)}
                    required
                    maxLength={6}
                    style={{
                      padding: '0.6rem 1rem',
                      borderRadius: '0.5rem',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      color: 'var(--text-primary)',
                      width: '140px',
                      textAlign: 'center',
                      fontSize: '1.1rem',
                      letterSpacing: '0.15em',
                      fontFamily: 'inherit',
                    }}
                  />
                  <button className="btn-primary" type="submit" style={{ width: 'auto' }}>
                    Activate
                  </button>
                  <button type="button" className="ghost-btn" onClick={() => { setMfaSecret(null); setMfaUri(null); setMfaVerifyCode(''); }} style={{ width: 'auto' }}>
                    Cancel
                  </button>
                </form>
              </div>
            </div>
          )
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1rem 0' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
              Multi-Factor Authentication is currently active on your account. To deactivate 2FA and remove the 2nd factor verification code prompt during sign-in, click the button below.
            </p>
            <button className="ghost-btn danger" onClick={handleMfaDisable} style={{ width: 'auto', alignSelf: 'flex-start' }}>
              <ShieldX size={16} />
              Disable 2FA
            </button>
          </div>
        )}
      </section>

      {/* Connection History */}
      <section id="section-history" className="glass-card panel">
        <div className="panel-head">
          <h3>My Connections History</h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source IP Address</th>
                <th>Access Device</th>
                <th>Connected Time</th>
                <th>Traffic (Upload/Download)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <EmptyState
                      icon={History}
                      title="No connection history"
                      hint="Your VPN connection sessions will be recorded here automatically."
                    />
                  </td>
                </tr>
              ) : (
                sessions.map((row, index) => (
                  <tr key={row.id || index}>
                    <td>{row.source_ip}</td>
                    <td>{row.device}</td>
                    <td>{formatDate(row.started_at)}</td>
                    <td>{formatBytes(row.upload_bytes)} / {formatBytes(row.download_bytes)}</td>
                    <td>
                      <StatusPill value={row.status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

// ─────────────────── AUDITOR DASHBOARD ───────────────────

function AuditorDashboard() {
  const [logs, setLogs] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setError('');
    try {
      const [logRows, eventRows, alertRows] = await Promise.all([
        apiFetch('/api/audit'),
        apiFetch('/api/threats/events'),
        apiFetch('/api/threats/alerts'),
      ]);
      setLogs(logRows || []);
      setEvents(eventRows || []);
      setAlerts(alertRows || []);
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <>
      <header className="page-header">
        <div>
          <p>Security Auditor</p>
          <h2>System Security Auditing</h2>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="ghost-btn" onClick={() => downloadFile('/api/audit/export?format=csv', 'audit-report.csv')}>
            <Download size={16} />
            Export CSV
          </button>
          <button className="ghost-btn" onClick={loadData}>
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </header>

      <ErrorBanner message={error} onClose={() => setError('')} />

      {/* Welcome Banner */}
      <div className="welcome-banner">
        <div className="welcome-text">
          <h3>Security Overview</h3>
          <p>Monitor system activity, review audit trails, and investigate security incidents. Export audit logs for compliance reporting.</p>
        </div>
        <div className="welcome-actions">
          <button className="ghost-btn" onClick={() => downloadFile('/api/audit/export?format=csv', 'audit-report.csv')}>
            <Download size={16} />
            Export Report
          </button>
        </div>
      </div>

      {/* Audit Logs */}
      <section id="section-logs" className="glass-card panel">
        <div className="panel-head">
          <h3>System Audit Logs</h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>Outcome</th>
                <th>Source IP</th>
                <th>Date Time</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <EmptyState
                      icon={FileText}
                      title="No audit logs found"
                      hint="System events will be logged here as users interact with the portal."
                    />
                  </td>
                </tr>
              ) : (
                logs.map((row) => (
                  <tr key={row.id}>
                    <td>{row.action}</td>
                    <td>
                      <StatusPill value={row.outcome} />
                    </td>
                    <td>{row.ip_address || '-'}</td>
                    <td>{formatDate(row.created_at)}</td>
                    <td style={{ fontSize: '0.8rem', opacity: 0.85 }}>
                      {JSON.stringify(row.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="content-grid">
        {/* Security Events */}
        <section id="section-events" className="glass-card panel">
          <div className="panel-head">
            <h3>Security Incidents</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>IP Address</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {events.length === 0 ? (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState
                        icon={Zap}
                        title="No security events"
                        hint="Security incidents will be captured and listed here when detected."
                      />
                    </td>
                  </tr>
                ) : (
                  events.map((row) => (
                    <tr key={row.id}>
                      <td>{row.event_type}</td>
                      <td>
                        <StatusPill value={row.severity} />
                      </td>
                      <td>{row.source_ip || '-'}</td>
                      <td>{formatDate(row.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Security Alerts */}
        <section id="section-threats" className="glass-card panel">
          <div className="panel-head">
            <h3>Identified Threats (Alerts)</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {alerts.length === 0 ? (
                  <tr>
                    <td colSpan={3}>
                      <EmptyState
                        icon={ShieldCheck}
                        title="No system alerts"
                        hint="Identified threats and security alerts will appear here."
                      />
                    </td>
                  </tr>
                ) : (
                  alerts.map((row) => (
                    <tr key={row.id}>
                      <td style={{ fontSize: '0.85rem' }}>{row.title}</td>
                      <td>
                        <StatusPill value={row.status} />
                      </td>
                      <td>
                        <StatusPill value={row.severity} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </>
  );
}

// ─────────────────── MAIN APP SHELL ───────────────────

export default function App() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const data = await apiFetch('/api/auth/me');
      setUser(data);
    } catch {
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, [router]);

  const handleLogout = async () => {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' });
    } catch (err) {
      console.error('Logout error:', err);
    }
    router.push('/login');
    router.refresh();
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" style={{ width: '2.5rem', height: '2.5rem' }}></div>
      </div>
    );
  }

  if (!user) return null;

  // Determine nav items based on role
  const navItems = user.role === 'admin' ? ADMIN_NAV
    : user.role === 'auditor' ? AUDITOR_NAV
    : USER_NAV;

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand-mark">
          <ShieldCheck size={26} />
          <span>AEGIS Portal</span>
        </div>

        <SidebarNav items={navItems} />

        <div className="identity">
          <strong>{user.username}</strong>
          <StatusPill value={user.role} />
        </div>
        <button className="btn-logout" onClick={handleLogout}>
          <LogOut size={16} />
          Sign Out
        </button>
      </aside>

      {/* Core Dashboard */}
      <main className="workspace">
        {user.role === 'admin' && <AdminDashboard />}
        {user.role === 'user' && <UserDashboard user={user} onUserUpdate={checkAuth} />}
        {user.role === 'auditor' && <AuditorDashboard />}
      </main>
    </div>
  );
}
