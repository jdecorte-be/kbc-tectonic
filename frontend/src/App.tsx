import { useEffect, useState, useCallback } from 'react';
import { HealthBadge } from './components/HealthBadge';
import { TodoForm } from './components/TodoForm';
import { TodoList } from './components/TodoList';
import { fetchHealth, fetchTodos, createTodo, updateTodo, deleteTodo } from './api';
import { Todo, TodoCreateInput, TodoUpdateInput, HealthCheckResponse } from './types';
import { Layers } from 'lucide-react';

export function App() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [todosLoading, setTodosLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const checkHealthStatus = useCallback(async () => {
    setHealthLoading(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err: any) {
      setHealth({
        status: 'degraded',
        database: 'disconnected',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setHealthLoading(false);
    }
  }, []);

  const loadTodos = useCallback(async () => {
    setTodosLoading(true);
    setGlobalError(null);
    try {
      const data = await fetchTodos();
      setTodos(data);
    } catch (err: any) {
      setGlobalError('Could not fetch todos from backend API.');
    } finally {
      setTodosLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealthStatus();
    loadTodos();
  }, [checkHealthStatus, loadTodos]);

  const handleAddTodo = async (input: TodoCreateInput) => {
    const newTodo = await createTodo(input);
    setTodos((prev) => [newTodo, ...prev]);
    checkHealthStatus();
  };

  const handleToggleTodo = async (id: number, completed: boolean) => {
    setTodos((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed } : t))
    );
    try {
      await updateTodo(id, { completed });
    } catch (err) {
      loadTodos();
    }
  };

  const handleUpdateTodo = async (id: number, input: TodoUpdateInput) => {
    const updated = await updateTodo(id, input);
    setTodos((prev) => prev.map((t) => (t.id === id ? updated : t)));
  };

  const handleDeleteTodo = async (id: number) => {
    setTodos((prev) => prev.filter((t) => t.id !== id));
    try {
      await deleteTodo(id);
    } catch (err) {
      loadTodos();
    }
  };

  return (
    <div className="container">
      <header>
        <div className="header-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Layers size={28} color="#38bdf8" />
            <h1>Todo Architecture Stack</h1>
          </div>
        </div>

        <HealthBadge
          health={health}
          loading={healthLoading}
          onRefresh={checkHealthStatus}
        />
      </header>

      <div className="card">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>
          Add New Todo Task
        </h2>
        <TodoForm onAddTodo={handleAddTodo} />
      </div>

      <div className="card">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 600 }}>
          Tasks stored in PostgreSQL
        </h2>
        {globalError && <div className="error-message">{globalError}</div>}
        <TodoList
          todos={todos}
          loading={todosLoading}
          onToggle={handleToggleTodo}
          onDelete={handleDeleteTodo}
          onUpdate={handleUpdateTodo}
        />
      </div>
    </div>
  );
}

export default App;
