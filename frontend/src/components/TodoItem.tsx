import React, { useState } from 'react';
import { Trash2, Edit2, Check, X } from 'lucide-react';
import { Todo, TodoUpdateInput } from '../types';

interface Props {
  todo: Todo;
  onToggle: (id: number, completed: boolean) => void;
  onDelete: (id: number) => void;
  onUpdate: (id: number, input: TodoUpdateInput) => Promise<void>;
}

export const TodoItem: React.FC<Props> = ({ todo, onToggle, onDelete, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.title);
  const [editDesc, setEditDesc] = useState(todo.description || '');

  const handleSave = async () => {
    if (!editTitle.trim()) return;
    await onUpdate(todo.id, {
      title: editTitle.trim(),
      description: editDesc.trim() || undefined
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditTitle(todo.title);
    setEditDesc(todo.description || '');
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="todo-item">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, marginRight: '1rem' }}>
          <input
            type="text"
            className="input-field"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
          />
          <input
            type="text"
            className="input-field"
            value={editDesc}
            placeholder="Description..."
            onChange={(e) => setEditDesc(e.target.value)}
          />
        </div>
        <div className="todo-actions">
          <button className="btn-icon" onClick={handleSave} title="Save">
            <Check size={18} color="#22c55e" />
          </button>
          <button className="btn-icon" onClick={handleCancel} title="Cancel">
            <X size={18} color="#ef4444" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`todo-item ${todo.completed ? 'completed' : ''}`}>
      <div className="todo-content">
        <input
          type="checkbox"
          className="checkbox"
          checked={todo.completed}
          onChange={(e) => onToggle(todo.id, e.target.checked)}
        />
        <div className="todo-text">
          <span className="todo-title">{todo.title}</span>
          {todo.description && <span className="todo-desc">{todo.description}</span>}
        </div>
      </div>
      <div className="todo-actions">
        <button className="btn-icon" onClick={() => setIsEditing(true)} title="Edit Todo">
          <Edit2 size={16} />
        </button>
        <button className="btn-icon" onClick={() => onDelete(todo.id)} title="Delete Todo">
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
};
