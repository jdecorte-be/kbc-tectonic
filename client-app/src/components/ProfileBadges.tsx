import React from 'react';
import { User } from '../types';
import { ShieldCheck, Car, Bus, Bike, Footprints, Home, Users, GraduationCap, Briefcase, TrendingUp } from 'lucide-react';

interface Props {
  user: User;
}

export const ProfileBadges: React.FC<Props> = ({ user }) => {
  const getTransportIcon = () => {
    switch (user.main_transportation) {
      case 'car': return <Car size={13} />;
      case 'public_transit': return <Bus size={13} />;
      case 'bicycle': return <Bike size={13} />;
      case 'walking': return <Footprints size={13} />;
      default: return <Car size={13} />;
    }
  };

  return (
    <div className="badges-container">
      {user.is_high_income && (
        <span className="badge badge-green">
          <TrendingUp size={13} /> High Income Profile
        </span>
      )}

      {user.is_student && (
        <span className="badge badge-cyan">
          <GraduationCap size={13} /> Student Status
        </span>
      )}

      {user.is_unemployed && (
        <span className="badge badge-rose">
          <Briefcase size={13} /> Job Seeking / Allowance
        </span>
      )}

      {user.financial_situation && (
        <span className={`badge ${user.financial_situation === 'comfortable' ? 'badge-green' : user.financial_situation === 'tight' ? 'badge-rose' : 'badge-cyan'}`}>
          Situation: {user.financial_situation.toUpperCase()}
        </span>
      )}

      {user.discretionary_spender && (
        <span className={`badge ${user.discretionary_spender === 'impulsive' ? 'badge-amber' : 'badge-cyan'}`}>
          Spender: {user.discretionary_spender.toUpperCase()}
        </span>
      )}

      {user.main_transportation && (
        <span className="badge badge-cyan">
          {getTransportIcon()} Transport: {user.main_transportation.replace('_', ' ').toUpperCase()}
        </span>
      )}

      {user.housing_status && (
        <span className="badge badge-cyan">
          <Home size={13} /> Housing: {user.housing_status.replace('_', ' ').toUpperCase()}
        </span>
      )}

      {user.children_count > 0 && (
        <span className="badge badge-amber">
          <Users size={13} /> {user.children_count} {user.children_count === 1 ? 'Child' : 'Children'}
        </span>
      )}

      {user.has_insurance && (
        <span className="badge badge-green">
          <ShieldCheck size={13} /> Insured
        </span>
      )}
    </div>
  );
};
