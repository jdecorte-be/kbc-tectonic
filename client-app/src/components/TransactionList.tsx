import React, { useState } from 'react';
import { Transaction } from '../types';
import { ArrowDownLeft, CreditCard, RefreshCw } from 'lucide-react';

interface Props {
  transactions: Transaction[];
}

export const TransactionList: React.FC<Props> = ({ transactions }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [search, setSearch] = useState<string>('');

  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch = tx.description.toLowerCase().includes(search.toLowerCase());
    if (filterType === 'all') return matchesSearch;
    if (filterType === 'deposit') return matchesSearch && tx.transaction_type === 'deposit';
    if (filterType === 'payment') return matchesSearch && (tx.transaction_type === 'payment' || tx.transaction_type === 'withdrawal');
    if (filterType === 'transfer') return matchesSearch && tx.transaction_type === 'transfer';
    if (filterType === 'failed') return matchesSearch && tx.status === 'failed';
    return matchesSearch;
  });

  const getTxIcon = (tx: Transaction) => {
    if (tx.transaction_type === 'deposit') {
      return <div className="tx-icon deposit"><ArrowDownLeft size={20} /></div>;
    }
    if (tx.transaction_type === 'transfer') {
      return <div className="tx-icon transfer"><RefreshCw size={18} /></div>;
    }
    return <div className="tx-icon payment"><CreditCard size={18} /></div>;
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">Banking Transaction Feed ({filteredTransactions.length})</h2>
        <input
          type="text"
          className="search-input"
          placeholder="Search merchants..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="filter-tabs">
        <button className={`filter-chip ${filterType === 'all' ? 'active' : ''}`} onClick={() => setFilterType('all')}>
          All Transactions
        </button>
        <button className={`filter-chip ${filterType === 'deposit' ? 'active' : ''}`} onClick={() => setFilterType('deposit')}>
          Deposits & Income
        </button>
        <button className={`filter-chip ${filterType === 'payment' ? 'active' : ''}`} onClick={() => setFilterType('payment')}>
          Payments & Expenses
        </button>
        <button className={`filter-chip ${filterType === 'transfer' ? 'active' : ''}`} onClick={() => setFilterType('transfer')}>
          Savings & Transfers
        </button>
        <button className={`filter-chip ${filterType === 'failed' ? 'active' : ''}`} onClick={() => setFilterType('failed')}>
          Failed Payments
        </button>
      </div>

      {filteredTransactions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
          No transactions match your search or filter.
        </div>
      ) : (
        <div className="tx-list">
          {filteredTransactions.map((tx) => {
            const isDeposit = tx.transaction_type === 'deposit';
            const dateStr = new Date(tx.created_at).toLocaleDateString('en-GB', {
              day: 'numeric',
              month: 'short',
              year: 'numeric'
            });

            return (
              <div key={tx.id} className="tx-item">
                <div className="tx-left">
                  {getTxIcon(tx)}
                  <div className="tx-details">
                    <span className="tx-desc">{tx.description}</span>
                    <div className="tx-meta">
                      <span>{dateStr}</span>
                      <span>•</span>
                      <span style={{ textTransform: 'capitalize' }}>{tx.transaction_type}</span>
                    </div>
                  </div>
                </div>

                <div className="tx-right">
                  <span className={`tx-amount ${isDeposit ? 'deposit' : 'payment'}`}>
                    {isDeposit ? '+' : '-'}€{parseFloat(tx.amount).toFixed(2)}
                  </span>
                  {tx.status !== 'completed' && (
                    <span className={`tx-status-badge ${tx.status}`}>
                      {tx.status}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
