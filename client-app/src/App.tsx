import { useEffect, useState, useCallback } from 'react';
import { UserSelector } from './components/UserSelector';
import { AccountOverview } from './components/AccountOverview';
import { TransactionList } from './components/TransactionList';
import { SpendingAnalytics } from './components/SpendingAnalytics';
import { fetchUsers, fetchUserDetail } from './api';
import { User } from './types';
import { Landmark, RefreshCw, Building2 } from 'lucide-react';

export function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'feed' | 'analytics'>('feed');

  const loadInitialUsers = useCallback(async () => {
    setLoading(true);
    try {
      const userList = await fetchUsers();
      setUsers(userList);
      if (userList.length > 0) {
        setSelectedUserId(userList[0].id);
      }
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUserDetail = useCallback(async (id: number) => {
    try {
      const userDetail = await fetchUserDetail(id);
      setSelectedUser(userDetail);
    } catch (err) {
      console.error('Failed to load user detail:', err);
    }
  }, []);

  useEffect(() => {
    loadInitialUsers();
  }, [loadInitialUsers]);

  useEffect(() => {
    if (selectedUserId !== null) {
      loadUserDetail(selectedUserId);
    }
  }, [selectedUserId, loadUserDetail]);

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">
            <Landmark size={22} />
          </div>
          <div className="brand-title">
            <h1>KBC Banking Client</h1>
            <p>Personal Finance & Lifestyle Mobile View</p>
          </div>
        </div>

        <button
          className="btn-secondary"
          onClick={() => selectedUserId && loadUserDetail(selectedUserId)}
          title="Refresh Account Data"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </header>

      {users.length > 0 && (
        <UserSelector
          users={users}
          selectedUserId={selectedUserId}
          onSelectUser={(id) => setSelectedUserId(id)}
        />
      )}

      {selectedUser && (
        <>
          <AccountOverview
            user={selectedUser}
            transactions={selectedUser.transactions || []}
          />

          <div className="card">
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <button
                className={`btn-secondary ${activeTab === 'feed' ? 'active' : ''}`}
                style={activeTab === 'feed' ? { background: 'var(--accent-blue)', color: 'white', borderColor: 'transparent' } : {}}
                onClick={() => setActiveTab('feed')}
              >
                <Building2 size={16} /> Transaction History ({selectedUser.transactions?.length || 0})
              </button>
              <button
                className={`btn-secondary ${activeTab === 'analytics' ? 'active' : ''}`}
                style={activeTab === 'analytics' ? { background: 'var(--accent-blue)', color: 'white', borderColor: 'transparent' } : {}}
                onClick={() => setActiveTab('analytics')}
              >
                Analytics & Categories
              </button>
            </div>

            {activeTab === 'feed' ? (
              <TransactionList transactions={selectedUser.transactions || []} />
            ) : (
              <SpendingAnalytics transactions={selectedUser.transactions || []} />
            )}
          </div>
        </>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading banking accounts...
        </div>
      )}
    </div>
  );
}

export default App;
