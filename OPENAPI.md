# REST API OpenAPI Specification

**FastAPI PostgreSQL Backend Documentation**  
- **Base URL**: `http://localhost:8000`  
- **Interactive Swagger Docs**: `http://localhost:8000/api/docs`  
- **OpenAPI JSON Schema**: `http://localhost:8000/api/openapi.json`  
- **Markdown Specification**: `http://localhost:8000/api/openapi.md`  

---

## 📌 Endpoint Summary

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Health** | `GET` | `/api/health` | Check API and PostgreSQL database health status |
| **Database** | `POST` | `/api/seed` | Seed database with sample users & lifestyle transactions |
| **Users** | `GET` | `/api/users` | List all users |
| **Users** | `GET` | `/api/users/{user_id}` | Get detailed user profile with transaction history |
| **Users** | `POST` | `/api/users` | Create a new user with profiling attributes |
| **Users** | `PUT` | `/api/users/{user_id}` | Update user profile fields (Full Update) |
| **Users** | `PATCH` | `/api/users/{user_id}` | Update user profile fields (Partial Update) |
| **Transactions**| `GET` | `/api/transactions` | List transactions (optional `?user_id=1` filter) |
| **Transactions**| `POST` | `/api/transactions` | Create a new financial transaction |
| **Docs** | `GET` | `/api/openapi.md` | Serve API documentation in Markdown format |

---

## 🚀 Detailed API Endpoints

### 1. Health & Database Services

#### `GET /api/health`
Checks backend FastAPI server and PostgreSQL database connectivity.

- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-09-30T19:00:00Z"
}
```

#### `POST /api/seed`
Triggers database seeding script. Creates 5 Belgian sample users with varied lifestyle profiles and 500 transactions (100 per user).

- **Query Parameters**:
  - `force` (boolean, optional, default: `false`): If `true`, drops existing tables and reseeds clean data.
- **Response `200 OK`**:
```json
{
  "status": "success",
  "users_created": 5,
  "transactions_created": 500,
  "transactions_per_user": 100
}
```

---

### 2. User Management API (`/api/users`)

#### `GET /api/users`
Retrieves list of registered users.

- **Query Parameters**:
  - `skip` (integer, default: `0`)
  - `limit` (integer, default: `100`)
- **Response `200 OK`**: Array of `UserResponse` objects.

#### `GET /api/users/{user_id}`
Retrieves detailed profile for a specific user along with their complete transaction history.

- **Path Parameters**:
  - `user_id` (integer, required)
- **Response `200 OK`**: `UserDetailResponse` object.
- **Response `404 Not Found`**: `{"detail": "User not found"}`

#### `POST /api/users`
Creates a new user account with contact and lifestyle profiling details.

- **Request Body** (`UserCreate`):
```json
{
  "name": "Alex Dupont",
  "phone_number": "+32 470 99 88 77",
  "email": "alex.dupont@example.com",
  "address": "Avenue Louise 250",
  "city": "Brussels",
  "country": "Belgium",
  "financial_situation": "comfortable",
  "is_student": false,
  "is_unemployed": false,
  "is_high_income": true,
  "discretionary_spender": "moderate",
  "main_transportation": "car",
  "children_count": 2,
  "in_couple": true,
  "has_insurance": true,
  "housing_status": "owner",
  "age_range": "36-50",
  "savings_goal": "real_estate",
  "risk_tolerance": "medium"
}
```
- **Response `201 Created`**: `UserResponse` object.
- **Response `400 Bad Request`**: `{"detail": "User with this email already exists"}`

#### `PUT /api/users/{user_id}` & `PATCH /api/users/{user_id}`
Updates existing user profile attributes. Allows full or partial field updates.

- **Path Parameters**:
  - `user_id` (integer, required)
- **Request Body** (`UserUpdate`):
```json
{
  "financial_situation": "tight",
  "discretionary_spender": "frugal",
  "housing_status": "renter",
  "savings_goal": "emergency_fund"
}
```
- **Response `200 OK`**: `UserResponse` object.
- **Response `404 Not Found`**: `{"detail": "User not found"}`

---

### 3. Transaction API (`/api/transactions`)

#### `GET /api/transactions`
Lists financial transactions.

- **Query Parameters**:
  - `user_id` (integer, optional): Filter transactions by user ID.
  - `skip` (integer, default: `0`)
  - `limit` (integer, default: `100`)
- **Response `200 OK`**: Array of `TransactionResponse` objects.

#### `POST /api/transactions`
Creates a new transaction linked to a user.

- **Request Body** (`TransactionCreate`):
```json
{
  "user_id": 1,
  "amount": 125.50,
  "currency": "EUR",
  "transaction_type": "payment",
  "status": "completed",
  "description": "Supermarket Purchase"
}
```
- **Response `201 Created`**: `TransactionResponse` object.
- **Response `404 Not Found`**: `{"detail": "User not found"}`

---

## 📑 Data Schemas & Field Specs

### `UserResponse` Schema
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `id` | Integer | Unique primary key |
| `name` | String | Full name |
| `phone_number` | String | Phone number |
| `email` | String | Email address (unique) |
| `address` | String | Street address |
| `city` | String | City name |
| `country` | String | Country name |
| `is_active` | Boolean | Active status flag |
| `financial_situation` | String | `'comfortable'`, `'balanced'`, `'tight'`, `'critical'` |
| `is_student` | Boolean | Is student? |
| `is_unemployed` | Boolean | Is unemployed / seeking job? |
| `is_high_income` | Boolean | High income earner? |
| `discretionary_spender` | String | `'frugal'`, `'moderate'`, `'impulsive'` |
| `main_transportation` | String | `'car'`, `'public_transit'`, `'bicycle'`, `'walking'`, `'motorcycle'`, `'other'` |
| `children_count` | Integer | Number of children (`0`, `1`, `2`, `3+`) |
| `in_couple` | Boolean | Married or in a couple? |
| `has_insurance` | Boolean | Holds insurance policy? |
| `housing_status` | String | `'owner'`, `'renter'`, `'free_housing'` |
| `age_range` | String | `'18-25'`, `'26-35'`, `'36-50'`, `'51-65'`, `'65+'` |
| `savings_goal` | String | `'real_estate'`, `'emergency_fund'`, `'travel'`, `'retirement'`, `'investment'` |
| `risk_tolerance` | String | `'low'`, `'medium'`, `'high'` |
| `created_at` | DateTime | Timestamp created |
| `updated_at` | DateTime | Timestamp last updated |

### `TransactionResponse` Schema
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `id` | Integer | Unique transaction ID |
| `user_id` | Integer | Foreign key referencing `users.id` |
| `amount` | Decimal | Transaction amount (e.g., `1250.00`) |
| `currency` | String | Currency code (default: `"EUR"`) |
| `transaction_type` | String | `'deposit'`, `'withdrawal'`, `'payment'`, `'transfer'` |
| `status` | String | `'completed'`, `'pending'`, `'failed'` |
| `description` | String | Merchant / Description text |
| `created_at` | DateTime | Timestamp |
