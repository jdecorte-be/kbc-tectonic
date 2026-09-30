// Synthetic demo data only — no real client data. Swap for a real API later.

export type ProfileId
  = | 'student'
    | 'young-investor'
    | 'investor'
    | 'holiday'
    | 'family'
    | 'homebuyer'
    | 'commuter'
    | 'freelancer'
    | 'saver'
    | 'financial-stress'
    | 'retiree'

export interface ProfileDef {
  label: string
  core: boolean
  offer: string
}

export const PROFILES: Record<ProfileId, ProfileDef> = {
  'student': { label: 'Student', core: true, offer: 'Youth account + student card' },
  'young-investor': { label: 'Young investor', core: true, offer: 'ETF savings plan' },
  'investor': { label: 'Investor', core: true, offer: 'Portfolio review with advisor' },
  'holiday': { label: 'Holiday soon', core: true, offer: 'Travel insurance + FX card' },
  'family': { label: 'New parent / family', core: false, offer: 'Child savings account' },
  'homebuyer': { label: 'Homebuyer / mover', core: false, offer: 'Mortgage simulation' },
  'commuter': { label: 'Car owner / commuter', core: false, offer: 'Car insurance check-up' },
  'freelancer': { label: 'Freelancer', core: false, offer: 'Business account + VAT pot' },
  'saver': { label: 'Saver', core: false, offer: 'Higher-yield savings plan' },
  'financial-stress': { label: 'Financial stress', core: false, offer: 'Budget coaching call' },
  'retiree': { label: 'Retiree', core: false, offer: 'Pension planning session' }
}

export const PROFILE_IDS = Object.keys(PROFILES) as ProfileId[]

export const HABITS = ['Travel', 'Investing', 'Groceries', 'Mobility', 'Eating out'] as const
export type Habit = typeof HABITS[number]

export interface Signal {
  text: string
  weight: number // 0..1 contribution to the profile confidence
}

export interface Transaction {
  date: string
  merchant: string
  category: string
  amount: number // negative = spend
}

export interface HabitChange {
  habit: string
  text: string
  delta: number // % vs the client's own baseline
  severity: 'info' | 'watch' | 'alert'
}

export interface Client {
  id: string
  name: string
  age: number
  profiles: { id: ProfileId, confidence: number }[]
  monthlySpend: number[] // last 6 months
  savingsRate: number // %
  recurringCount: number
  cashShare: number // % of spend in cash
  payday: number
  topHabit: string
  signals: Signal[]
  change?: HabitChange
  transactions: Transaction[]
}

// Deterministic PRNG so the demo looks identical on every reload (and SSR/client match).
function rng(seed: number) {
  let s = seed
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296
    return s / 4294967296
  }
}

interface Seed {
  name: string
  age: number
  main: ProfileId
  second?: ProfileId
  base: number
  savings: number
  recurring: number
  cash: number
  payday: number
  topHabit: string
  signals: [string, number][]
  change?: HabitChange
  tx: [string, string, number][]
}

const seeds: Seed[] = [
  {
    name: 'Emma Peeters', age: 21, main: 'student', second: 'young-investor', base: 920, savings: 4, recurring: 4, cash: 9, payday: 1, topHabit: 'Eating out',
    signals: [['Monthly allowance of €650 from parents', 0.35], ['Tuition payment KU Leuven', 0.3], ['De Lijn student pass', 0.2], ['Spotify / Netflix student plans', 0.15]],
    change: { habit: 'Investing', text: 'First transfer to a brokerage account (€50)', delta: 100, severity: 'info' },
    tx: [['Alma Student Restaurant', 'Eating out', -4.2], ['De Lijn', 'Mobility', -19], ['Delhaize', 'Groceries', -23.4], ['Spotify', 'Subscriptions', -5.99]]
  },
  {
    name: 'Noah Janssens', age: 19, main: 'student', base: 780, savings: 2, recurring: 3, cash: 14, payday: 5, topHabit: 'Groceries',
    signals: [['Low recurring income (€500/month)', 0.4], ['Rent to student housing', 0.3], ['Cheap food / takeaway dominant', 0.3]],
    tx: [['Student housing', 'Housing', -420], ['Aldi', 'Groceries', -31.2], ['Night shop', 'Eating out', -9.5], ['NMBS Youth', 'Mobility', -6.2]]
  },
  {
    name: 'Lucas Claes', age: 26, main: 'young-investor', second: 'saver', base: 1850, savings: 22, recurring: 8, cash: 4, payday: 25, topHabit: 'Investing',
    signals: [['First salary 2 years ago, stable payday', 0.25], ['Monthly €300 to broker account', 0.4], ['ETF and crypto purchases', 0.25], ['Low cash usage', 0.1]],
    change: { habit: 'Investing', text: 'Monthly investing up from €300 to €500', delta: 67, severity: 'info' },
    tx: [['Bolero', 'Investing', -300], ['Coinbase', 'Investing', -80], ['Colruyt', 'Groceries', -64.3], ['Gym Basic-Fit', 'Subscriptions', -24.99]]
  },
  {
    name: 'Sofie Maes', age: 29, main: 'young-investor', base: 2100, savings: 18, recurring: 9, cash: 6, payday: 28, topHabit: 'Investing',
    signals: [['Recurring ETF purchases (3 months in a row)', 0.45], ['Savings rate above 15%', 0.3], ['Digital-first, card payments only', 0.25]],
    tx: [['Bolero ETF plan', 'Investing', -250], ['Zara', 'Shopping', -59.9], ['Delhaize', 'Groceries', -41.8]]
  },
  {
    name: 'Hugo Willems', age: 52, main: 'investor', second: 'saver', base: 4600, savings: 31, recurring: 14, cash: 3, payday: 27, topHabit: 'Investing',
    signals: [['Large monthly flows to investment accounts (€1,500+)', 0.4], ['Brokerage and custody fees', 0.25], ['Diversified: funds, bonds, shares', 0.25], ['High balance at month end', 0.1]],
    tx: [['KBC Securities', 'Investing', -1500], ['Custody fee', 'Fees', -42], ['Restaurant Hof van Cleve', 'Eating out', -210]]
  },
  {
    name: 'Marie Dubois', age: 47, main: 'investor', base: 5200, savings: 27, recurring: 12, cash: 2, payday: 26, topHabit: 'Investing',
    signals: [['Quarterly dividend income', 0.35], ['Regular bond / fund purchases', 0.4], ['Stable high-value spending', 0.25]],
    tx: [['Dividend Proximus', 'Income', 420], ['KBC Securities', 'Investing', -900], ['Colruyt', 'Groceries', -132]]
  },
  {
    name: 'Thomas Goossens', age: 34, main: 'holiday', second: 'commuter', base: 2400, savings: 9, recurring: 7, cash: 7, payday: 25, topHabit: 'Travel',
    signals: [['Flight booking Brussels → Lisbon (€412)', 0.35], ['Hotel + Airbnb deposits', 0.25], ['Luggage and outdoor shop purchases', 0.2], ['First FX withdrawal planned / currency exchange', 0.2]],
    change: { habit: 'Travel', text: 'Travel spend +340% vs. 3-month baseline', delta: 340, severity: 'alert' },
    tx: [['Brussels Airlines', 'Travel', -412], ['Airbnb', 'Travel', -380], ['Decathlon', 'Shopping', -119], ['Travelex', 'Travel', -200]]
  },
  {
    name: 'Julie Vermeulen', age: 31, main: 'holiday', base: 2250, savings: 11, recurring: 6, cash: 8, payday: 28, topHabit: 'Travel',
    signals: [['Train tickets + hotel booking in Italy', 0.4], ['Travel pharmacy purchase', 0.2], ['Holiday budget transfer to savings', 0.4]],
    change: { habit: 'Travel', text: 'Booking.com payment, trip in 3 weeks', delta: 180, severity: 'watch' },
    tx: [['Booking.com', 'Travel', -640], ['Trainline', 'Travel', -96], ['Pharmacy', 'Health', -23]]
  },
  {
    name: 'Lotte Hermans', age: 33, main: 'family', second: 'homebuyer', base: 3100, savings: 8, recurring: 11, cash: 3, payday: 27, topHabit: 'Groceries',
    signals: [['Baby shop purchases (Baby-Dump, Prénatal)', 0.4], ['Childcare (crèche) monthly payment', 0.3], ['Groceries +45% in 4 months', 0.2], ['Pharmacy frequency up', 0.1]],
    change: { habit: 'Groceries', text: 'Groceries +45% and new childcare payment', delta: 45, severity: 'info' },
    tx: [['Baby-Dump', 'Shopping', -188], ['Crèche Zonnestraal', 'Childcare', -330], ['Delhaize', 'Groceries', -112]]
  },
  {
    name: 'Arne De Smet', age: 36, main: 'homebuyer', base: 3300, savings: 14, recurring: 10, cash: 3, payday: 26, topHabit: 'Groceries',
    signals: [['Notary fee advance (€2,400)', 0.4], ['Furniture and DIY shops (IKEA, Brico)', 0.3], ['Rent payment stopped last month', 0.3]],
    change: { habit: 'Housing', text: 'Rent stopped, DIY spend +210%', delta: 210, severity: 'watch' },
    tx: [['Notary Van den Bossche', 'Housing', -2400], ['IKEA', 'Shopping', -640], ['Brico', 'Shopping', -210]]
  },
  {
    name: 'Bram Pauwels', age: 41, main: 'commuter', base: 2900, savings: 10, recurring: 9, cash: 5, payday: 25, topHabit: 'Mobility',
    signals: [['Fuel purchases 2× per week', 0.4], ['Car insurance + leasing', 0.3], ['Tolls and parking', 0.3]],
    tx: [['Q8', 'Mobility', -78], ['Parking Q-Park', 'Mobility', -14], ['Car insurance', 'Insurance', -92]]
  },
  {
    name: 'Nina Vandenberghe', age: 38, main: 'freelancer', base: 2600, savings: 12, recurring: 8, cash: 4, payday: 15, topHabit: 'Eating out',
    signals: [['Irregular incoming payments from 5+ payers', 0.45], ['Quarterly VAT payment', 0.3], ['Coworking + software subscriptions', 0.25]],
    tx: [['Invoice Studio Nord', 'Income', 1800], ['VAT payment', 'Tax', -950], ['Coworking Mindspace', 'Subscriptions', -290], ['Adobe', 'Subscriptions', -62]]
  },
  {
    name: 'Anke Wouters', age: 45, main: 'saver', base: 1700, savings: 35, recurring: 6, cash: 10, payday: 27, topHabit: 'Groceries',
    signals: [['35% of income moved to savings', 0.5], ['Low discretionary spend', 0.3], ['Same merchants every month', 0.2]],
    tx: [['Savings transfer', 'Saving', -600], ['Aldi', 'Groceries', -48], ['Electricity', 'Bills', -96]]
  },
  {
    name: 'Kevin Mertens', age: 39, main: 'financial-stress', base: 2100, savings: -6, recurring: 13, cash: 18, payday: 25, topHabit: 'Groceries',
    signals: [['Overdraft 12 days in the last 30', 0.4], ['2 rejected direct debits', 0.3], ['Rising fixed costs (+18%)', 0.2], ['Cash withdrawals up', 0.1]],
    change: { habit: 'Overdraft', text: 'Overdraft days 2 → 12 this month', delta: 500, severity: 'alert' },
    tx: [['Rejected direct debit Engie', 'Bills', -132], ['ATM', 'Cash', -150], ['Delhaize', 'Groceries', -38]]
  },
  {
    name: 'Jozef Lambrecht', age: 66, main: 'retiree', second: 'saver', base: 1900, savings: 12, recurring: 7, cash: 28, payday: 3, topHabit: 'Groceries',
    signals: [['Pension payment on the 3rd', 0.5], ['Pharmacy and healthcare regular', 0.25], ['High cash usage', 0.25]],
    tx: [['Pension FPS', 'Income', 1720], ['Pharmacy', 'Health', -47], ['ATM', 'Cash', -100]]
  }
]

// Build a plausible 6-month spend series and keep the last point aligned with `change`.
function buildClient(seed: Seed, index: number): Client {
  const rand = rng(1000 + index * 97)
  const spend = Array.from({ length: 6 }, (_, i) =>
    Math.round(seed.base * (0.92 + rand() * 0.16 + (i === 5 && seed.change ? seed.change.delta / 1000 : 0))))
  const total = seed.signals.reduce((a, s) => a + s[1], 0)
  const mainConf = Math.round(Math.min(96, 68 + total * 18 + rand() * 6))
  const profiles = [{ id: seed.main, confidence: mainConf }]
  if (seed.second) profiles.push({ id: seed.second, confidence: Math.round(mainConf * (0.45 + rand() * 0.2)) })
  return {
    id: `c${index + 1}`,
    name: seed.name,
    age: seed.age,
    profiles,
    monthlySpend: spend,
    savingsRate: seed.savings,
    recurringCount: seed.recurring,
    cashShare: seed.cash,
    payday: seed.payday,
    topHabit: seed.topHabit,
    signals: seed.signals.map(([text, weight]) => ({ text, weight })),
    change: seed.change,
    transactions: seed.tx.map(([merchant, category, amount], i) => ({
      date: new Date(Date.UTC(2026, 8, 29 - i * 3)).toISOString().slice(0, 10),
      merchant,
      category,
      amount
    }))
  }
}

export const clients: Client[] = seeds.map(buildClient)

export const primaryProfile = (c: Client) => c.profiles[0]!

// Segment distribution: primary profile counts (scaled to look like a real book of clients).
export const SCALE = 820
export const segmentCounts = PROFILE_IDS
  .map(id => ({
    id,
    label: PROFILES[id].label,
    count: clients.filter(c => primaryProfile(c).id === id).length * SCALE
  }))
  .filter(s => s.count > 0)
  .sort((a, b) => b.count - a.count)

// Weekly spend per habit (12 weeks), with each habit's baseline. Travel and investing drift up.
const weekRand = rng(42)
export interface WeekPoint { date: Date, spend: number, baseline: number }

export const habitTrends: Record<Habit, WeekPoint[]> = Object.fromEntries(
  HABITS.map((habit) => {
    const base = { 'Travel': 18, 'Investing': 42, 'Groceries': 65, 'Mobility': 24, 'Eating out': 30 }[habit]
    const drift = { 'Travel': 1.9, 'Investing': 0.35, 'Groceries': 0.1, 'Mobility': 0.05, 'Eating out': -0.1 }[habit]
    const points: WeekPoint[] = Array.from({ length: 12 }, (_, w) => {
      const ramp = w > 7 ? 1 + drift * ((w - 7) / 4) : 1
      return {
        date: new Date(Date.UTC(2026, 6, 13 + w * 7)),
        spend: Math.round(base * 1000 * (0.94 + weekRand() * 0.12) * ramp) / 1000,
        baseline: base
      }
    })
    return [habit, points]
  })
) as Record<Habit, WeekPoint[]>

// Average spend per weekday (index 0 = Monday) across all clients, in €.
export const weekdayRhythm = [
  { day: 'Mon', spend: 38 }, { day: 'Tue', spend: 41 }, { day: 'Wed', spend: 44 },
  { day: 'Thu', spend: 52 }, { day: 'Fri', spend: 83 }, { day: 'Sat', spend: 97 }, { day: 'Sun', spend: 51 }
]

export const kpis = {
  clientsTracked: clients.length * SCALE,
  profilesDetected: segmentCounts.length,
  habitChanges: clients.filter(c => c.change).length * 37,
  openOpportunities: clients.filter(c => c.change && c.change.severity !== 'info').length * 63
}

export const getClient = (id: string) => clients.find((c) => c.id === id)
