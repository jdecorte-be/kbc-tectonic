import React from 'react';
import { HealthCheckResponse } from '../types';
import { Server, Database, RefreshCw } from 'lucide-react';

interface Props {
  health: HealthCheckResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const HealthBadge: React.FC<Props> = ({ health, loading, onRefresh }) => {
  const isBackendHealthy = health?.status === 'healthy';
  const isDbConnected = health?.database === 'connected';

  return (
    <div className="health-banner">
      <div className={`health-badge ${isBackendHealthy ? 'connected' : 'disconnected'}`}>
        <Server size={14} />
        <span className="health-dot"></span>
        FastAPI Backend: {isBackendHealthy ? 'Online' : 'Offline'}
      </div>

      <div className={`health-badge ${isDbConnected ? 'connected' : 'disconnected'}`}>
        <Database size={14} />
        <span className="health-dot"></span>
        PostgreSQL DB: {isDbConnected ? 'Connected' : 'Disconnected'}
      </div>

      <button
        className="btn-icon"
        onClick={onRefresh}
        disabled={loading}
        title="Refresh Status"
        style={{ marginLeft: 'auto' }}
      >
        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
      </button>
    </div>
  );
};
