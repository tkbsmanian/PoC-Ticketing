import { FormEvent, useEffect, useState } from 'react'
import { adminApi } from '@/api/admin'
import type { CreateUserPayload, Department, UserRole, UserSummary } from '@/types'

const ROLES: UserRole[] = ['business_user', 'it_manager', 'it_triage', 'platform_admin', 'auditor']

export function UserManagement() {
  const [users, setUsers] = useState<UserSummary[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CreateUserPayload>({
    email: '', display_name: '', role: 'business_user', department_id: null, password: '',
  })
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    Promise.all([adminApi.listUsers(), adminApi.listDepartments()])
      .then(([u, d]) => { setUsers(u.data); setDepartments(d.data) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await adminApi.createUser(form)
      setShowForm(false)
      setForm({ email: '', display_name: '', role: 'business_user', department_id: null, password: '' })
      load()
    } catch {
      setError('Failed to create user.')
    }
  }

  const toggleActive = async (user: UserSummary) => {
    await adminApi.updateUser(user.id, { is_active: !user.is_active })
    load()
  }

  if (loading) return <p>Loading users…</p>

  return (
    <div className="user-management">
      <div className="section-header">
        <h2>Users</h2>
        <button onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : '+ Add User'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="create-form" aria-label="Create user">
          <div className="field">
            <label htmlFor="u-email">Email</label>
            <input id="u-email" type="email" required value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
          </div>
          <div className="field">
            <label htmlFor="u-name">Display Name</label>
            <input id="u-name" type="text" required value={form.display_name}
              onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))} />
          </div>
          <div className="field">
            <label htmlFor="u-role">Role</label>
            <select id="u-role" value={form.role}
              onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as UserRole }))}>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="u-dept">Department</label>
            <select id="u-dept" value={form.department_id ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, department_id: Number(e.target.value) || null }))}>
              <option value="">None</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="u-pass">Temporary Password</label>
            <input id="u-pass" type="password" required minLength={8} value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
          </div>
          {error && <p className="field-error" role="alert">{error}</p>}
          <button type="submit">Create User</button>
        </form>
      )}

      <table className="admin-table" aria-label="Users">
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Role</th><th>Department</th><th>Active</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className={u.is_active ? '' : 'row-inactive'}>
              <td>{u.display_name}</td>
              <td>{u.email}</td>
              <td>{u.role}</td>
              <td>{u.department_name ?? '—'}</td>
              <td>{u.is_active ? 'Yes' : 'No'}</td>
              <td>
                <button onClick={() => toggleActive(u)}>
                  {u.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
