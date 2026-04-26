/**
 * CommentThread — conversation thread with public/internal toggle for IT roles.
 */

import { FormEvent, useState } from 'react'
import { commentsApi } from '@/api/comments'
import { usePermissions } from '@/hooks/usePermissions'
import type { Comment, TicketStatus } from '@/types'

interface Props {
  ticketId: number
  comments: Comment[]
  ticketStatus: TicketStatus
  onCommentAdded: () => void
}

export function CommentThread({ ticketId, comments, ticketStatus, onCommentAdded }: Props) {
  const perms = usePermissions()
  const [body, setBody] = useState('')
  const [isInternal, setIsInternal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isClosed = ticketStatus === 'Closed'
  const canComment = !isClosed

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!body.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await commentsApi.create(ticketId, { body: body.trim(), is_internal: isInternal })
      setBody('')
      onCommentAdded()
    } catch {
      setError('Failed to post comment. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const visibleComments = perms.canViewInternalComments
    ? comments
    : comments.filter((c) => !c.is_internal)

  return (
    <section aria-labelledby="comments-heading">
      <h2 id="comments-heading">Comments</h2>

      {visibleComments.length === 0 ? (
        <p className="empty-state">No comments yet.</p>
      ) : (
        <ul className="comment-list" aria-label="Comments">
          {visibleComments.map((c) => (
            <li
              key={c.id}
              className={`comment ${c.is_internal ? 'comment-internal' : ''}`}
            >
              {c.is_internal && (
                <span className="internal-label" aria-label="Internal note">
                  🔒 Internal
                </span>
              )}
              <div className="comment-meta">
                <strong>{c.author_name}</strong>
                <span className="comment-role">{c.author_role}</span>
                <time dateTime={c.created_at}>
                  {new Date(c.created_at).toLocaleString()}
                </time>
              </div>
              <p className="comment-body">{c.body}</p>
            </li>
          ))}
        </ul>
      )}

      {canComment && (
        <form onSubmit={handleSubmit} aria-label="Add comment">
          <div className="field">
            <label htmlFor="comment-body">Add a comment</label>
            <textarea
              id="comment-body"
              rows={3}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write your comment…"
              required
            />
          </div>

          {perms.canAddInternalComment && (
            <label className="internal-toggle">
              <input
                type="checkbox"
                checked={isInternal}
                onChange={(e) => setIsInternal(e.target.checked)}
              />
              Internal note (hidden from requester)
            </label>
          )}

          {error && <p className="field-error" role="alert">{error}</p>}

          <button type="submit" disabled={submitting || !body.trim()}>
            {submitting ? 'Posting…' : 'Post Comment'}
          </button>
        </form>
      )}

      {isClosed && (
        <p className="info-message">This ticket is closed. Comments are disabled.</p>
      )}
    </section>
  )
}
