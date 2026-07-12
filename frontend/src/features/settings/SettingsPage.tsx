import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Button } from '../../components/ui/Button';
import { RoleBadge } from '../../components/ui/RoleBadge';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { apiClient } from '../../api/client';
import type { ErrorEnvelope, Role } from '../../types/api';

interface AiSettingsBase {
  chatbot_enabled: boolean;
  model: string;
}

interface AiSettingsFull extends AiSettingsBase {
  temperature: number | string;
  max_tokens: number;
  system_prompt: string;
  role_tool_permissions: Record<string, string[]>;
  updated_at: string;
  openrouter_key_set?: boolean;
}

type AiSettingsResponse = AiSettingsBase | AiSettingsFull;

interface AiSettingsDraft {
  chatbot_enabled: boolean;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
}

interface UpdateAiSettingsPayload {
  chatbot_enabled?: boolean;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
}

const MODEL_SUGGESTIONS = [
  'anthropic/claude-3.5-haiku',
  'openai/gpt-4o-mini',
  'google/gemini-flash-1.5',
  'meta-llama/llama-3.1-70b-instruct',
];

function isFullSettings(s: AiSettingsResponse): s is AiSettingsFull {
  return 'system_prompt' in s;
}

function errorEnvelope(error: unknown) {
  if (axios.isAxiosError<ErrorEnvelope>(error)) {
    return error.response?.data?.error;
  }
  return undefined;
}

function errorMessage(error: unknown): string {
  return errorEnvelope(error)?.message ?? 'Something went wrong.';
}

function fieldError(error: unknown, field: string): string | undefined {
  const env = errorEnvelope(error);
  return env?.field === field ? env.message : undefined;
}

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

  const queryClient = useQueryClient();

  const {
    data: settings,
    isLoading: isSettingsLoading,
    isError: isSettingsError,
    error: settingsError,
  } = useQuery({
    queryKey: ['ai', 'settings'],
    queryFn: async () => {
      const res = await apiClient.get<AiSettingsResponse>('/ai/settings');
      return res.data;
    },
    retry: 1,
  });

  const full = settings && isFullSettings(settings) ? settings : null;

  const [draft, setDraft] = useState<AiSettingsDraft | null>(null);

  useEffect(() => {
    if (full) {
      setDraft({
        chatbot_enabled: full.chatbot_enabled,
        model: full.model,
        temperature: Number(full.temperature),
        max_tokens: full.max_tokens,
        system_prompt: full.system_prompt,
      });
    }
  }, [full]);

  const updateMutation = useMutation({
    mutationFn: async (payload: UpdateAiSettingsPayload) => {
      const res = await apiClient.put<AiSettingsResponse>('/ai/settings', payload);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['ai', 'settings'], data);
    },
  });

  const [justSaved, setJustSaved] = useState(false);
  useEffect(() => {
    if (updateMutation.data) {
      setJustSaved(true);
      const t = setTimeout(() => setJustSaved(false), 2500);
      return () => clearTimeout(t);
    }
  }, [updateMutation.data]);

  const handleSave = () => {
    if (!draft) return;
    updateMutation.mutate({
      chatbot_enabled: draft.chatbot_enabled,
      model: draft.model,
      temperature: draft.temperature,
      max_tokens: draft.max_tokens,
      system_prompt: draft.system_prompt,
    });
  };

  const aiSettingsLoadingBlock = <div className="p-6 text-sm text-ink-mute">Loading AI settings…</div>;

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
        <div className="p-4 bg-surface-2 border-b border-line flex items-center justify-between">
          <h2 className="font-semibold text-ink text-sm uppercase tracking-wider">AI Assistant Configuration</h2>
          {full && (
            <span className={`text-[11px] uppercase tracking-wide font-medium ${full.openrouter_key_set ? 'text-ok' : 'text-warn'}`}>
              {full.openrouter_key_set ? 'API key configured' : 'API key not set on server'}
            </span>
          )}
        </div>

        {isSettingsLoading ? (
          aiSettingsLoadingBlock
        ) : isSettingsError ? (
          <div className="p-6 text-sm text-danger">{errorMessage(settingsError)}</div>
        ) : !full ? (
          <div className="p-6 space-y-4">
            <p className="text-sm text-ink-mute">AI configuration is managed by Fleet Managers. Current status:</p>
            <div className="flex items-center justify-between pb-4 border-b border-line">
              <span className="text-sm font-medium text-ink">Chatbot Enabled</span>
              <span className={`text-xs font-medium ${settings?.chatbot_enabled ? 'text-ok' : 'text-ink-mute'}`}>
                {settings?.chatbot_enabled ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-ink">Model</span>
              <span className="text-sm font-data text-ink-mute">{settings?.model}</span>
            </div>
          </div>
        ) : !draft ? (
          aiSettingsLoadingBlock
        ) : (
          <div className="p-6 space-y-6">
            {updateMutation.isError && !errorEnvelope(updateMutation.error)?.field && (
              <div className="text-xs text-danger bg-danger/10 border border-danger/30 rounded px-3 py-2">
                {errorMessage(updateMutation.error)}
              </div>
            )}
            {justSaved && <div className="text-xs text-ok">Settings saved.</div>}

            <div className="flex items-start justify-between pb-6 border-b border-line">
              <div>
                <h3 className="font-medium text-ink">Chatbot Enabled</h3>
                <p className="text-sm text-ink-mute mt-1">Allow users to chat with the TransitOps AI assistant.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={draft.chatbot_enabled}
                  onChange={(e) => setDraft((d) => (d ? { ...d, chatbot_enabled: e.target.checked } : d))}
                />
                <div className="w-11 h-6 bg-surface-2 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-surface-2 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-signal"></div>
              </label>
            </div>

            <div className="flex items-start justify-between pb-6 border-b border-line gap-6">
              <div className="flex-1">
                <h3 className="font-medium text-ink">Model</h3>
                <p className="text-sm text-ink-mute mt-1">OpenRouter model id used for chat completions.</p>
              </div>
              <div className="w-72">
                <Input
                  list="ai-model-suggestions"
                  value={draft.model}
                  onChange={(e) => setDraft((d) => (d ? { ...d, model: e.target.value } : d))}
                  error={fieldError(updateMutation.error, 'model')}
                />
                <datalist id="ai-model-suggestions">
                  {MODEL_SUGGESTIONS.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
            </div>

            <div className="flex items-start justify-between pb-6 border-b border-line gap-6">
              <div className="flex-1">
                <h3 className="font-medium text-ink">Temperature</h3>
                <p className="text-sm text-ink-mute mt-1">Higher is more creative, lower is more deterministic (0–2).</p>
                {fieldError(updateMutation.error, 'temperature') && (
                  <p className="text-xs text-danger mt-1">{fieldError(updateMutation.error, 'temperature')}</p>
                )}
              </div>
              <div className="w-56 flex items-center gap-3">
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.05}
                  value={draft.temperature}
                  onChange={(e) => setDraft((d) => (d ? { ...d, temperature: Number(e.target.value) } : d))}
                  className="flex-1 accent-signal"
                />
                <span className="text-sm font-data text-ink w-10 text-right">{draft.temperature.toFixed(2)}</span>
              </div>
            </div>

            <div className="flex items-start justify-between pb-6 border-b border-line gap-6">
              <div className="flex-1">
                <h3 className="font-medium text-ink">Max Tokens</h3>
                <p className="text-sm text-ink-mute mt-1">Upper bound on the assistant's reply length (128–8192).</p>
              </div>
              <div className="w-40">
                <Input
                  type="number"
                  min={128}
                  max={8192}
                  value={draft.max_tokens}
                  onChange={(e) => setDraft((d) => (d ? { ...d, max_tokens: Number(e.target.value) } : d))}
                  error={fieldError(updateMutation.error, 'max_tokens')}
                />
              </div>
            </div>

            <Textarea
              label="System Prompt"
              hint="Admin-configurable behavior, tone, or extra instructions appended to every chat."
              rows={4}
              maxLength={4000}
              value={draft.system_prompt}
              onChange={(e) => setDraft((d) => (d ? { ...d, system_prompt: e.target.value } : d))}
              error={fieldError(updateMutation.error, 'system_prompt')}
            />

            <div className="flex justify-end">
              <Button
                onClick={handleSave}
                isLoading={updateMutation.isPending}
                className="bg-signal text-white hover:bg-signal/90 border-transparent"
              >
                Save Changes
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
