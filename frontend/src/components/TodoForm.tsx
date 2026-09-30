import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { TodoCreateInput } from '../types';

interface Props {
  onAddTodo: (input: TodoCreateInput) => Promise<void>;
}

export const TodoForm: React.FC<Props> = ({ onAddTodo }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      await onAddTodo({ title: title.trim(), description: description.trim() || undefined });
      setTitle('');
      setDescription('');
    } catch (err: any) {
      setError(err.message || 'Failed to add todo');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="form-group" onSubmit={handleSubmit}>
      {error && <div className="error-message">{error}</div>}
      <input
        type="text"
        className="input-field"
        placeholder="What needs to be done?"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        disabled={submitting}
        required
      />
      <input
        type="text"
        className="input-field"
        placeholder="Optional description or details..."
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        disabled={submitting}
      />
      <button type="submit" className="btn btn-primary" disabled={submitting || !title.trim()}>
        <Plus size={18} /> Add Todo Task
      </button>
    </form>
  );
};
