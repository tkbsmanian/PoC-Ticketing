/**
 * Business portal — ticket submission form.
 * Fields: title, description, department, urgency, cost (optional), manager, attachments.
 */

import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ticketsApi } from '@/api/tickets'
import { attachmentsApi } from '@/api/attachments'
import { adminApi } from '@/api/admin'
import type { Department, UrgencyLevel, UserSummary } from '@/types'

const URGENCY_OPTIONS: UrgencyLevel[] = ['Low', 'Medium', 'High', 'Critical']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

export function SubmitTicketPage() {
  const navigate = useNavigate()

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [departmentId, setDepartmentId] = useState<number | ''>('')
  const [urgency, setUrgency] = useState<UrgencyLevel>('Medium')
  const [cost, setCost] = useState<string>('')
  const [managerId, setManagerId] = useState<number | ''>('')
  const [files, setFiles] = useState<File[]>([])

  const [departments, setDepartments] = useState<Department[]>([])
  const [managers, setManagers] = useState<UserSummary[]>([])
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    adminApi.listDepartments().then(({ data }) => setDepartments(data.filter((d) => d.is_active)))
    adminApi.listManagers().then(({ data }) => setManagers(data))
  }, [])

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    if (!title.trim()) e.title = 'Title is required.'
    if (title.trim().length > 255) e.title = 'Title must be 255 characters or fewer.'
    if (!description.trim()) e.description = 'Description is required.'
    if (!departmentId) e.departmentId = 'Department is required.'
    if (!managerId) e.managerId = 'Approving manager is required.'
    if (cost && (isNaN(Number(cost)) || Number(cost) < 0))
      e.cost = 'Cost must be a positive number.'
    for (const f of files) {
      if (f.size > MAX_FILE_SIZE) {
        e.files = `"${f.name}" exceeds the 10 MB limit.`
        break
      }
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    try {
      const { data: ticket } = await ticketsApi.create({
        title: title.trim(),
        description: description.trim(),
        department_id: Number(departmentId),
        urgency,
        cost: cost ? Number(cost) : undefined,
        manager_id: Number(managerId),
      })
      // Upload attachments after ticket creation
      for (const file of files) {
        await attachmentsApi.upload(ticket.id, file)
      }
      navigate(`/portal/tickets/${ticket.id}`, {
        state: { successMessage: `Request ${ticket.ticket_id} submitted successfully.` },
      })
    } catch {
      setErrors({ submit: 'Submission failed. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(Array.from(e.target.files ?? []))
  }

  return (
    <div className="submit-ticket-page">
      <h1>Submit a Request</h1>
      <form onSubmit={handleSubmit} noValidate aria-label="Submit request form">
        <div className="field">
          <label htmlFor="title">Title <span aria-hidden="true">*</span></label>
          <input
            id="title"
            type="text"
            maxLength={255}
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            aria-describedby={errors.title ? 'title-error' : undefined}
            aria-invalid={!!errors.title}
          />
          {errors.title && <span id="title-error" className="field-error">{errors.title}</span>}
        </div>

        <div className="field">
          <label htmlFor="description">Description <span aria-hidden="true">*</span></label>
          <textarea
            id="description"
            rows={5}
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            aria-describedby={errors.description ? 'desc-error' : undefined}
            aria-invalid={!!errors.description}
          />
          {errors.description && <span id="desc-error" className="field-error">{errors.description}</span>}
        </div>

        <div className="field">
          <label htmlFor="department">Department <span aria-hidden="true">*</span></label>
          <select
            id="department"
            required
            value={departmentId}
            onChange={(e) => setDepartmentId(Number(e.target.value))}
            aria-invalid={!!errors.departmentId}
          >
            <option value="">Select department…</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          {errors.departmentId && <span className="field-error">{errors.departmentId}</span>}
        </div>

        <div className="field">
          <label htmlFor="urgency">Urgency <span aria-hidden="true">*</span></label>
          <select
            id="urgency"
            value={urgency}
            onChange={(e) => setUrgency(e.target.value as UrgencyLevel)}
          >
            {URGENCY_OPTIONS.map((u) => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
          <small>High or Critical urgency requires Director approval.</small>
        </div>

        <div className="field">
          <label htmlFor="cost">Estimated Cost (optional)</label>
          <input
            id="cost"
            type="number"
            min="0"
            step="0.01"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            aria-describedby="cost-hint"
            aria-invalid={!!errors.cost}
          />
          <small id="cost-hint">Any cost entered requires Director approval.</small>
          {errors.cost && <span className="field-error">{errors.cost}</span>}
        </div>

        <div className="field">
          <label htmlFor="manager">Approving Manager <span aria-hidden="true">*</span></label>
          <select
            id="manager"
            required
            value={managerId}
            onChange={(e) => setManagerId(Number(e.target.value))}
            aria-invalid={!!errors.managerId}
          >
            <option value="">Select manager…</option>
            {managers.map((m) => (
              <option key={m.id} value={m.id}>{m.display_name}</option>
            ))}
          </select>
          {errors.managerId && <span className="field-error">{errors.managerId}</span>}
        </div>

        <div className="field">
          <label htmlFor="attachments">Attachments (optional, max 10 MB each)</label>
          <input
            id="attachments"
            type="file"
            multiple
            onChange={handleFileChange}
            aria-describedby={errors.files ? 'files-error' : undefined}
          />
          {errors.files && <span id="files-error" className="field-error">{errors.files}</span>}
        </div>

        {errors.submit && (
          <p className="field-error" role="alert">{errors.submit}</p>
        )}

        <div className="form-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit Request'}
          </button>
          <button type="button" onClick={() => navigate(-1)}>Cancel</button>
        </div>
      </form>
    </div>
  )
}
