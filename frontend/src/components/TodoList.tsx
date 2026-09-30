import React, { useState } from 'react';
import { Todo, TodoUpdateInput } from '../types';
import { TodoItem } from './TodoItem';

interface Props {
  todos: Todo[];
  loading: boolean;
  onToggle: (id: number, completed: boolean) => void;
  onDelete: (id: number) => void;
  onUpdate: (id: number, input: TodoUpdateInput) => Promise<void>;
}

export const TodoList: React.FC<Props> = ({ todos, loading, onToggle, onDelete, onUpdate }) => {
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  const filteredTodos = todos.filter((todo) => {
    if (filter === 'active') return !todo.completed;
    if (filter === 'completed') return todo.completed;
    return true;
  });

  const activeCount = todos.filter((t) => !t.completed).length;

  if (loading && todos.length === 0) {
    return <div className="empty-state">Loading todos...</div>;
  }

  return (
    <div>
      <div className="filter-bar">
        <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {activeCount} {activeCount === 1 ? 'task' : 'tasks'} remaining
        </span>

        <div className="filter-group">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({todos.length})
          </button>
          <button
            className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
            onClick={() => setFilter('active')}
          >
            Active ({activeCount})
          </button>
          <button
            className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
            onClick={() => setFilter('completed')}
          >
            Completed ({todos.length - activeCount})
          </button>
        </div>
      </div>

      {filteredTodos.length === 0 ? (
        <div className="empty-state">
          {todos.length === 0
            ? 'No tasks yet. Create your first task above!'
            : `No ${filter} tasks found.`}
        </div>
      ) : (
        <div className="todo-list">
          {filteredTodos.map((todo) => (
            <TodoItem
              key={todo.id}
              todo={todo}
              onToggle={onToggle}
              onDelete={onDelete}
              onUpdate={onUpdate}
            />
          ))}
        </div>
      )}
    </div>
  );
};
