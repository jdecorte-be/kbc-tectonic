export interface Transaction {
  id: number;
  user_id: number;
  amount: string;
  currency: string;
  transaction_type: 'deposit' | 'withdrawal' | 'payment' | 'transfer';
  status: 'completed' | 'pending' | 'failed';
  description: string;
  created_at: string;
  updated_at?: string | null;
}

export interface User {
  id: number;
  name: string;
  phone_number: string;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
  is_active: boolean;

  financial_situation?: 'comfortable' | 'balanced' | 'tight' | 'critical' | null;
  is_student: boolean;
  is_unemployed: boolean;
  is_high_income: boolean;
  discretionary_spender?: 'frugal' | 'moderate' | 'impulsive' | null;
  main_transportation?: 'car' | 'public_transit' | 'bicycle' | 'walking' | 'motorcycle' | 'other' | null;
  children_count: number;
  in_couple: boolean;
  has_insurance: boolean;

  housing_status?: 'owner' | 'renter' | 'free_housing' | null;
  age_range?: '18-25' | '26-35' | '36-50' | '51-65' | '65+' | null;
  savings_goal?: 'real_estate' | 'emergency_fund' | 'travel' | 'retirement' | 'investment' | null;
  risk_tolerance?: 'low' | 'medium' | 'high' | null;

  created_at: string;
  updated_at?: string | null;
  transactions?: Transaction[];
}

export interface HealthCheckResponse {
  status: string;
  database: string;
  timestamp: string;
}
