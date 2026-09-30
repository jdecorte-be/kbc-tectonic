import React from 'react';
import { User, Transaction } from '../types';
import { ProfileBadges } from './ProfileBadges';
import { ArrowUpRight, ArrowDownRight, Wallet, Target } from 'lucide-react';

interface Props {
  user: User;
  transactions: Transaction[];
}

export const AccountOverview: React.FC<Props> = ({ user, transactions }) => {
  // Calculate total balance, total income, total expenses
  let totalIncome = 0;
  let totalExpense = 0;

  transactions.forEach((tx) => {
    if (tx.status === 'failed') return;
    const val = parseFloat(tx.amount);
    if (tx.transaction_type === 'deposit') {
      totalIncome += val;
    } else {
      totalExpense += val;
    }
  });

  const calculatedBalance = totalIncome - totalExpense;

  return (
    <div className="overview-card">
      <div className="balance-row">
        <div>
          <span className="balance-title">Main Checking Account Balance</span>
          <div className="balance-amount">
            €{calculatedBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Primary IBAN: BE76 1234 5678 {user.id.toString().padStart(4, '0')}
          </span>
        </div>
        <div style={{ background: 'rgba(56, 189, 248, 0.1)', padding: '0.6rem', borderRadius: '12px', color: 'var(--accent-cyan)' }}>
          <Wallet size={24} />
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-box">
          <span className="stat-label">Total Inflow (Deposits)</span>
          <span className="stat-value income">
            <ArrowUpRight size={16} style={{ display: 'inline', verticalAlign: 'sub' }} />
            +€{totalIncome.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>

        <div className="stat-box">
          <span className="stat-label">Total Outflow (Expenses)</span>
          <span className="stat-value expense">
            <ArrowDownRight size={16} style={{ display: 'inline', verticalAlign: 'sub' }} />
            -€{totalExpense.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>

        {user.savings_goal && (
          <div className="stat-box">
            <span className="stat-label">Savings Target</span>
            <span className="stat-value" style={{ color: 'var(--accent-cyan)' }}>
              <Target size={16} style={{ display: 'inline', verticalAlign: 'sub' }} />
              {user.savings_goal.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        )}
      </div>

      <ProfileBadges user={user} />
    </div>
  );
};
