import React from 'react';
import { Transaction } from '../types';

interface Props {
  transactions: Transaction[];
}

export const SpendingAnalytics: React.FC<Props> = ({ transactions }) => {
  // Aggregate expenses by keyword category
  const categories: { [key: string]: number } = {
    'Housing & Rent': 0,
    'Supermarket Groceries': 0,
    'Transportation & Fuel': 0,
    'Dining & Leisure': 0,
    'Utilities & Tech': 0,
    'Savings & Transfers': 0,
    'Other Expenses': 0
  };

  let totalExpenses = 0;

  transactions.forEach((tx) => {
    if (tx.transaction_type === 'deposit' || tx.status === 'failed') return;
    const val = parseFloat(tx.amount);
    totalExpenses += val;

    const desc = tx.description.toLowerCase();
    if (desc.includes('rent') || desc.includes('mortgage')) {
      categories['Housing & Rent'] += val;
    } else if (desc.includes('groceries') || desc.includes('supermarket') || desc.includes('discount')) {
      categories['Supermarket Groceries'] += val;
    } else if (desc.includes('fuel') || desc.includes('transit') || desc.includes('parking') || desc.includes('repair') || desc.includes('train')) {
      categories['Transportation & Fuel'] += val;
    } else if (desc.includes('restaurant') || desc.includes('bar') || desc.includes('fashion') || desc.includes('pub') || desc.includes('gourmet') || desc.includes('zalando')) {
      categories['Dining & Leisure'] += val;
    } else if (desc.includes('engie') || desc.includes('proximus') || desc.includes('spotify') || desc.includes('netflix') || desc.includes('apple')) {
      categories['Utilities & Tech'] += val;
    } else if (tx.transaction_type === 'transfer' || desc.includes('savings') || desc.includes('portfolio') || desc.includes('republic')) {
      categories['Savings & Transfers'] += val;
    } else {
      categories['Other Expenses'] += val;
    }
  });

  const sortedCategories = Object.entries(categories)
    .filter(([_, amount]) => amount > 0)
    .sort((a, b) => b[1] - a[1]);

  if (totalExpenses === 0) return null;

  return (
    <div>
      <h2 className="section-title" style={{ marginBottom: '1rem' }}>Lifestyle Expense Breakdown</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {sortedCategories.map(([catName, amount]) => {
          const percent = ((amount / totalExpenses) * 100).toFixed(1);
          return (
            <div key={catName}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                <span style={{ fontWeight: 600 }}>{catName}</span>
                <span style={{ color: 'var(--text-muted)' }}>
                  €{amount.toFixed(2)} ({percent}%)
                </span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'var(--bg-primary)', borderRadius: '9999px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${percent}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #38bdf8, #2563eb)',
                    borderRadius: '9999px'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
