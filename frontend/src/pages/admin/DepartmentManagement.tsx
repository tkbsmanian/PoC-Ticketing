import { FormEvent, useEffect, useState } from 'react'
import { adminApi } from '@/api/admin'
import type { Department } from '@/types'

export function DepartmentManagement() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [newName, setNewName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = () => adminApi.listDepartments().then(({ data }) => setDepartments(data))
  useEffect(() => { load() }, [])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setError(null)
    try {
      await adminApi.createDepartment(newName.trim())
      setNewName('')
      load()
    } catch {
      setError('Failed to create department.')
    }
  }

  const toggleActive = async (dept: Department) => {
    await adminApi.updateDepartment(dept.id, { is_active: !dept.is_active })
    load()
  }

  return (
    <div className="department-management">
      <h2>Departments</h2>
      <form onSubmit={handleCreate} className="inline-form" aria-label="Add department">
        <input
          type="text"
          placeholder="Department name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          required
          maxLength={120}
        />
        <button type="submit">Add</button>
        {error && <span className="field-error">{error}</span>}
      </form>

      <table className="admin-table" aria-label="Departments">
        <thead>
          <tr><th>Name</th><th>Active</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {departments.map((d) => (
            <tr key={d.id} className={d.is_active ? '' : 'row-inactive'}>
              <td>{d.name}</td>
              <td>{d.is_active ? 'Yes' : 'No'}</td>
              <td>
                <button onClick={() => toggleActive(d)}>
                  {d.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
