// Named aliases over the types generated from the backend OpenAPI spec (`pnpm gen:api`).
import type { components } from './api.gen'

type Schemas = components['schemas']

export type Client = Schemas['Client']
export type ClientTransaction = Schemas['ClientTransaction']
export type Dashboard = Schemas['Dashboard']
export type Habit = Schemas['Habit']
export type HabitChange = Schemas['HabitChange']
export type JevResult = Schemas['JevResult']
export type JevTrackers = Schemas['JevTrackers']
export type ProfileDef = Schemas['ProfileDef']
export type ProfileId = Schemas['ProfileId']
export type ProfileScore = Schemas['ProfileScore']
export type Relation = Schemas['Relation']
export type Signal = Schemas['Signal']
export type WeekPoint = Schemas['WeekPoint']

export { habitValues as HABITS, profileIdValues as PROFILE_IDS } from './api.gen'
