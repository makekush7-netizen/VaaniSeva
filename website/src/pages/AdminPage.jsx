/**
 * AdminPage — RAG Knowledge Base Admin Portal
 *
 * Protected by admin JWT (stored in localStorage as "vaaniseva_admin_token").
 * Features: View / Add / Edit / Delete entries, Verify, AI Review (Bedrock fact-check).
 */
import React, { useState, useEffect, useCallback } from 'react'
import {
  Plus, Search, Filter, Loader2, CheckCircle, XCircle, AlertCircle,
  Edit2, Trash2, ChevronDown, X, RefreshCw, ShieldCheck, LogOut,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const TOKEN_KEY = 'vaaniseva_admin_token'

const CATEGORIES = [
  'emergency', 'healthcare', 'health', 'agriculture', 'legal', 'finance', 'education', 'housing', 'women', 'general',
]

// ── API helpers ──────────────────────────────────────────────
function adminFetch(path, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY)
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  })
}

// ── Status badges ────────────────────────────────────────────
function VerifiedBadge({ verified }) {
  if (verified) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-xs font-medium">
        <CheckCircle size={11} /> Verified
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs">
      Unverified
    </span>
  )
}

function AIReviewBadge({ status }) {
  if (!status) return <span className="text-gray-300 text-xs">—</span>
  const map = {
    PASS: { bg: 'bg-green-50', text: 'text-green-700', icon: <CheckCircle size={11} />, label: 'PASS' },
    FLAG: { bg: 'bg-yellow-50', text: 'text-yellow-700', icon: <AlertCircle size={11} />, label: 'FLAG' },
    FAIL: { bg: 'bg-red-50', text: 'text-red-700', icon: <XCircle size={11} />, label: 'FAIL' },
  }
  const s = map[status] || map.FLAG
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 ${s.bg} ${s.text} rounded-full text-xs font-medium`}>
      {s.icon} {s.label}
    </span>
  )
}

// ── Entry form component ─────────────────────────────────────
function EntryForm({ initial, onSave, onCancel, saving }) {
  const [form, setForm] = useState(
    initial || {
      title: '', category: 'general',
      text_hi: '', text_mr: '', text_ta: '', text_en: '',
      helpline_numbers: [], source_url: '', documents_required: [],
    }
  )
  const [helplinesInput, setHelplinesInput] = useState(
    (initial?.helpline_numbers || []).join(', ')
  )
  const [docsInput, setDocsInput] = useState(
    (initial?.documents_required || []).join(', ')
  )

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      helpline_numbers: helplinesInput.split(',').map((s) => s.trim()).filter(Boolean),
      documents_required: docsInput.split(',').map((s) => s.trim()).filter(Boolean),
    }
    onSave(payload)
  }

  const langFields = [
    { key: 'text_hi', label: 'Hindi (हिंदी)', placeholder: 'हिंदी में जानकारी लिखें…' },
    { key: 'text_mr', label: 'Marathi (मराठी)', placeholder: 'मराठीत माहिती लिहा…' },
    { key: 'text_ta', label: 'Tamil (தமிழ்)', placeholder: 'தமிழில் தகவல் எழுதுங்கள்…' },
    { key: 'text_en', label: 'English', placeholder: 'Write content in English…' },
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Title + Category */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Title *</label>
          <input
            required
            value={form.title}
            onChange={(e) => set('title', e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
            placeholder="PM-Kisan Samman Nidhi"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Category</label>
          <select
            value={form.category}
            onChange={(e) => set('category', e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 outline-none bg-white"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Language text fields — side by side in 2-col grid */}
      <div className="grid grid-cols-2 gap-4">
        {langFields.map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className="block text-xs font-semibold text-gray-500 mb-1">{label}</label>
            <textarea
              value={form[key] || ''}
              onChange={(e) => set(key, e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none resize-none"
              placeholder={placeholder}
            />
          </div>
        ))}
      </div>

      {/* Helplines + Source */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">
            Helpline Numbers <span className="font-normal text-gray-400">(comma-separated)</span>
          </label>
          <input
            value={helplinesInput}
            onChange={(e) => setHelplinesInput(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none font-mono"
            placeholder="155261, 1800-180-1551"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Source URL</label>
          <input
            value={form.source_url || ''}
            onChange={(e) => set('source_url', e.target.value)}
            type="url"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
            placeholder="https://pmkisan.gov.in"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-500 mb-1">
          Documents Required <span className="font-normal text-gray-400">(comma-separated)</span>
        </label>
        <input
          value={docsInput}
          onChange={(e) => setDocsInput(e.target.value)}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
          placeholder="Aadhaar, Land record, Bank passbook"
        />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg">
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-5 py-2 text-sm bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50 flex items-center gap-2"
        >
          {saving && <Loader2 size={14} className="animate-spin" />}
          {initial ? 'Save Changes' : 'Create Entry'}
        </button>
      </div>
    </form>
  )
}

// ── Modal wrapper ─────────────────────────────────────────────
function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-content-primary">{title}</h2>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg transition-colors">
            <X size={18} />
          </button>
        </div>
        <div className="overflow-y-auto px-6 py-5 flex-1">{children}</div>
      </div>
    </div>
  )
}

// ── Login form ───────────────────────────────────────────────
function LoginForm({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Login failed')
      localStorage.setItem(TOKEN_KEY, data.token)
      onLogin(data.token, data.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="text-3xl mb-2">🔐</div>
          <h1 className="text-xl font-bold text-content-primary">Admin Login</h1>
          <p className="text-sm text-gray-500 mt-1">VaaniSeva RAG Admin Portal</p>
        </div>
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
              placeholder="admin@example.com"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent-600 text-white rounded-lg text-sm font-medium hover:bg-accent-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading && <Loader2 size={14} className="animate-spin" />}
            Sign In
          </button>
        </form>
        <p className="text-center text-xs text-gray-400 mt-4">
          Requires <code>is_admin: true</code> on your DynamoDB user record
        </p>
      </div>
    </div>
  )
}

// ── Main Admin Component ─────────────────────────────────────
export default function AdminPage() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(null)

  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [verifiedFilter, setVerifiedFilter] = useState('')

  const [modal, setModal] = useState(null) // null | { type: 'create' | 'edit', entry? }
  const [saving, setSaving] = useState(false)
  const [reviewingId, setReviewingId] = useState(null) // entry id being reviewed
  const [verifyingId, setVerifyingId] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null) // entry id

  const handleLogin = (tok, usr) => {
    setToken(tok)
    setUser(usr)
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setEntries([])
  }

  // ── Fetch entries ────────────────────────────────────────
  const fetchEntries = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      if (categoryFilter) params.set('category', categoryFilter)
      if (verifiedFilter) params.set('verified', verifiedFilter)
      if (searchQuery) params.set('q', searchQuery)

      const res = await adminFetch(`/admin/rag?${params}`)
      const data = await res.json()
      if (res.status === 401 || res.status === 403) {
        setError(data.error || 'Access denied')
        if (res.status === 401) logout()
        return
      }
      if (!res.ok) throw new Error(data.error || 'Failed to load entries')
      setEntries(data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [categoryFilter, verifiedFilter, searchQuery])

  useEffect(() => {
    if (token) fetchEntries()
  }, [token, fetchEntries])

  // ── Create / Update ────────────────────────────────────
  const handleSave = async (payload) => {
    setSaving(true)
    try {
      const isEdit = modal?.type === 'edit' && modal.entry?.id
      const res = await adminFetch(
        isEdit ? `/admin/rag/${encodeURIComponent(modal.entry.id)}` : '/admin/rag',
        { method: isEdit ? 'PUT' : 'POST', body: JSON.stringify(payload) }
      )
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Save failed')
      setModal(null)
      fetchEntries()
    } catch (err) {
      alert(`Save failed: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  // ── Delete ─────────────────────────────────────────────
  const handleDelete = async (id) => {
    try {
      const res = await adminFetch(`/admin/rag/${encodeURIComponent(id)}`, { method: 'DELETE' })
      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.error || 'Delete failed')
      }
      setDeleteConfirm(null)
      fetchEntries()
    } catch (err) {
      alert(`Delete failed: ${err.message}`)
    }
  }

  // ── Verify ─────────────────────────────────────────────
  const handleVerify = async (id) => {
    setVerifyingId(id)
    try {
      const res = await adminFetch(`/admin/rag/${encodeURIComponent(id)}/verify`, { method: 'POST', body: '{}' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Verify failed')
      setEntries((prev) =>
        prev.map((e) => (e.id === id ? { ...e, verified: true, verified_by: data.verified_by } : e))
      )
    } catch (err) {
      alert(`Verify failed: ${err.message}`)
    } finally {
      setVerifyingId(null)
    }
  }

  // ── AI Review ──────────────────────────────────────────
  const handleAIReview = async (id) => {
    setReviewingId(id)
    try {
      const res = await adminFetch(`/admin/rag/${encodeURIComponent(id)}/ai-review`, { method: 'POST', body: '{}' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'AI review failed')
      setEntries((prev) =>
        prev.map((e) =>
          e.id === id
            ? { ...e, ai_review_status: data.ai_review_status, ai_review_notes: data.ai_review_notes }
            : e
        )
      )
    } catch (err) {
      alert(`AI Review failed: ${err.message}`)
    } finally {
      setReviewingId(null)
    }
  }

  if (!token) return <LoginForm onLogin={handleLogin} />

  const filteredEntries = entries.filter((e) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      if (
        !(e.title || '').toLowerCase().includes(q) &&
        !(e.text_en || '').toLowerCase().includes(q) &&
        !(e.text_hi || '').toLowerCase().includes(q) &&
        !(e.category || '').toLowerCase().includes(q)
      )
        return false
    }
    if (categoryFilter && e.category !== categoryFilter) return false
    if (verifiedFilter === 'true' && !e.verified) return false
    if (verifiedFilter === 'false' && e.verified) return false
    return true
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-2">
          <span className="text-xl">📚</span>
          <div>
            <h1 className="text-base font-bold text-content-primary">RAG Knowledge Admin</h1>
            <p className="text-xs text-gray-400">{entries.length} entries in vaaniseva-knowledge</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchEntries}
            disabled={loading}
            title="Refresh"
            className="p-2 text-gray-400 hover:text-gray-700 rounded-lg border border-gray-200 transition-colors"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={() => setModal({ type: 'create' })}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent-600 text-white rounded-lg text-sm font-medium hover:bg-accent-700 transition-colors"
          >
            <Plus size={15} /> Add Entry
          </button>
          <button
            onClick={logout}
            title="Logout"
            className="p-2 text-gray-400 hover:text-red-500 rounded-lg border border-gray-200 transition-colors"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-3 bg-white border-b border-gray-100 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, text, category…"
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 outline-none bg-white"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          value={verifiedFilter}
          onChange={(e) => setVerifiedFilter(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-accent-500 outline-none bg-white"
        >
          <option value="">All Status</option>
          <option value="true">Verified</option>
          <option value="false">Unverified</option>
        </select>
        {(searchQuery || categoryFilter || verifiedFilter) && (
          <button
            onClick={() => { setSearchQuery(''); setCategoryFilter(''); setVerifiedFilter('') }}
            className="text-xs text-gray-500 hover:text-gray-800 flex items-center gap-1"
          >
            <X size={12} /> Clear filters
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
          ⚠ {error}
        </div>
      )}

      {/* Table */}
      <div className="px-6 py-4">
        {loading && entries.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Loader2 size={28} className="animate-spin mx-auto mb-3 text-accent-400" />
            Loading knowledge entries…
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-sm">{entries.length === 0 ? 'No entries yet. Click "Add Entry" to create one.' : 'No entries match your filters.'}</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 w-[35%]">Title / Category</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 w-[25%]">Content Preview</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">Verified</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">AI Review</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredEntries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-content-primary truncate max-w-[240px]">{entry.title}</p>
                      <span className="mt-0.5 inline-block px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">
                        {entry.category}
                      </span>
                      {entry.helpline_numbers?.length > 0 && (
                        <p className="text-xs text-blue-600 font-mono mt-0.5">📞 {entry.helpline_numbers.join(', ')}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-gray-500 text-xs line-clamp-2 max-w-[200px]">
                        {entry.text_en || entry.text_hi || '—'}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <VerifiedBadge verified={entry.verified} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <AIReviewBadge status={entry.ai_review_status} />
                      {entry.ai_review_notes && (
                        <p className="text-xs text-gray-400 mt-0.5 max-w-[120px] truncate" title={entry.ai_review_notes}>
                          {entry.ai_review_notes}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {/* AI Review */}
                        <button
                          onClick={() => handleAIReview(entry.id)}
                          disabled={reviewingId === entry.id}
                          title="Run AI fact-check"
                          className="px-2.5 py-1.5 text-xs bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg flex items-center gap-1 disabled:opacity-50 transition-colors"
                        >
                          {reviewingId === entry.id ? (
                            <Loader2 size={11} className="animate-spin" />
                          ) : (
                            '🤖'
                          )}
                          Review
                        </button>
                        {/* Verify */}
                        {!entry.verified && (
                          <button
                            onClick={() => handleVerify(entry.id)}
                            disabled={verifyingId === entry.id}
                            title="Mark as verified"
                            className="px-2.5 py-1.5 text-xs bg-green-50 text-green-700 hover:bg-green-100 rounded-lg flex items-center gap-1 disabled:opacity-50 transition-colors"
                          >
                            {verifyingId === entry.id ? (
                              <Loader2 size={11} className="animate-spin" />
                            ) : (
                              <ShieldCheck size={11} />
                            )}
                            Verify
                          </button>
                        )}
                        {/* Edit */}
                        <button
                          onClick={() => setModal({ type: 'edit', entry })}
                          title="Edit entry"
                          className="p-1.5 text-gray-400 hover:text-accent-600 rounded-lg transition-colors"
                        >
                          <Edit2 size={14} />
                        </button>
                        {/* Delete */}
                        <button
                          onClick={() => setDeleteConfirm(entry.id)}
                          title="Delete entry"
                          className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create / Edit modal */}
      {modal && (
        <Modal
          title={modal.type === 'create' ? 'Add New Knowledge Entry' : `Edit: ${modal.entry?.title}`}
          onClose={() => setModal(null)}
        >
          <EntryForm
            initial={modal.entry}
            onSave={handleSave}
            onCancel={() => setModal(null)}
            saving={saving}
          />
        </Modal>
      )}

      {/* Delete confirm modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm text-center">
            <div className="text-3xl mb-3">🗑️</div>
            <h3 className="text-base font-bold text-content-primary mb-2">Delete this entry?</h3>
            <p className="text-sm text-gray-500 mb-5">
              This will permanently remove the entry from both knowledge and vectors tables. This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 py-2 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="flex-1 py-2 bg-red-500 text-white rounded-xl text-sm font-medium hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
