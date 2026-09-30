import React from 'react';
import { User } from '../types';
import { User as UserIcon } from 'lucide-react';

interface Props {
  users: User[];
  selectedUserId: number | null;
  onSelectUser: (id: number) => void;
}

export const UserSelector: React.FC<Props> = ({ users, selectedUserId, onSelectUser }) => {
  return (
    <div className="user-selector-container">
      {users.map((user) => {
        const isActive = user.id === selectedUserId;
        return (
          <button
            key={user.id}
            className={`user-chip ${isActive ? 'active' : ''}`}
            onClick={() => onSelectUser(user.id)}
          >
            <UserIcon size={14} />
            {user.name}
          </button>
        );
      })}
    </div>
  );
};
