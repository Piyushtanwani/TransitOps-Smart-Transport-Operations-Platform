import { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { RoleBadge } from '../../components/ui/RoleBadge';
import type { Role } from '../../types/api';

const mockUsers = [
  { id: 'u1', name: 'Alex Manager', email: 'manager@transitops.in', role: 'fleet_manager' as Role, status: 'active' },
  { id: 'u2', name: 'Priya Officer', email: 'dispatch@transitops.in', role: 'dispatcher' as Role, status: 'active' },
  { id: 'u3', name: 'John Doe', email: 'safety@transitops.in', role: 'safety_officer' as Role, status: 'active' },
  { id: 'u4', name: 'Suresh Kumar', email: 'finance@transitops.in', role: 'financial_analyst' as Role, status: 'disabled' },
];

export function SettingsPage() {
  const [users, setUsers] = useState(mockUsers);

  const toggleStatus = (id: string) => {
    setUsers(users.map(u => u.id === id ? { ...u, status: u.status === 'active' ? 'disabled' : 'active' } : u));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-ink">System Settings</h1>
          <p className="text-sm text-ink-mute mt-1">Manage users, roles, and AI configurations</p>
        </div>
        <Button className="bg-signal text-white hover:bg-signal/90 border-transparent">
          + Add User
        </Button>
      </div>

      <div className="rounded-md border border-line bg-surface-1 overflow-hidden">
        <div className="p-4 bg-surface-2 border-b border-line">
          <h2 className="font-semibold text-ink text-sm uppercase tracking-wider">User Directory</h2>
        </div>
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-ink-mute text-[11px] uppercase tracking-wider font-medium">
            <tr>
              <th className="px-6 py-4">NAME</th>
              <th className="px-6 py-4">EMAIL</th>
              <th className="px-6 py-4">ROLE</th>
              <th className="px-6 py-4">STATUS</th>
              <th className="px-6 py-4">ACTIONS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line text-ink">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-surface-2/50 transition-colors">
                <td className="px-6 py-4 font-medium">{u.name}</td>
                <td className="px-6 py-4 text-ink-mute">{u.email}</td>
                <td className="px-6 py-4"><RoleBadge role={u.role} /></td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    u.status === 'active' ? 'bg-ok/20 text-ok' : 'bg-surface-3 text-ink-mute'
                  }`}>
                    {u.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 space-x-3">
                  <button className="text-ink-mute hover:text-ink font-medium text-sm transition-colors">Edit</button>
                  <button 
                    onClick={() => toggleStatus(u.id)}
                    className={`${u.status === 'active' ? 'text-danger' : 'text-ok'} hover:underline font-medium text-sm transition-colors`}
                  >
                    {u.status === 'active' ? 'Disable' : 'Enable'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-md border border-line bg-surface-1 overflow-hidden mt-8">
        <div className="p-4 bg-surface-2 border-b border-line">
          <h2 className="font-semibold text-ink text-sm uppercase tracking-wider">AI Assistant Configuration</h2>
        </div>
        <div className="p-6 space-y-6">
          <div className="flex items-start justify-between pb-6 border-b border-line">
            <div>
              <h3 className="font-medium text-ink">Trip Advisor Enabled</h3>
              <p className="text-sm text-ink-mute mt-1">Allow AI to analyze trips for weather, fatigue, and delays during dispatch.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-surface-3 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-surface-3 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-signal"></div>
            </label>
          </div>
          
          <div className="flex items-start justify-between pb-6 border-b border-line">
            <div>
              <h3 className="font-medium text-ink">Strict AI Blocking</h3>
              <p className="text-sm text-ink-mute mt-1">If AI detects a high-risk factor (e.g. severe weather), prevent dispatchers from overriding the block.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" />
              <div className="w-11 h-6 bg-surface-3 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-surface-3 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-signal"></div>
            </label>
          </div>

          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-medium text-ink">AI Model Precision</h3>
              <p className="text-sm text-ink-mute mt-1">Higher precision is slower but makes fewer hallucinations. Lower is faster.</p>
            </div>
            <select defaultValue="High Precision (GPT-4o)" className="h-9 rounded-md border border-line bg-surface-0 px-3 text-sm focus:border-signal focus:outline-none text-ink">
              <option>Fast (Llama 3 8B)</option>
              <option>Balanced (GPT-4o mini)</option>
              <option>High Precision (GPT-4o)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
