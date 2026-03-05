-- =============================================================================
-- financial-cashflow-agent — Database Schema
-- =============================================================================
-- Design principles:
--   1. Core tables apply to every business type
--   2. Extension tables add structure for specific business types
--   3. Everything references businesses.id as the root
--   4. Amounts are stored in the business's local currency (no currency conversion)
--   5. All dates use ISO 8601 format: YYYY-MM-DD
-- =============================================================================


-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- businesses
-- The root table. Every other table references this.
-- business_type drives which extension tables are populated.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS businesses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,

    -- Drives agent reasoning and which extension tables to query
    -- Values: 'restaurant', 'retail', 'saas', 'funded_startup',
    --         'bootstrapped_startup', 'freelance', 'construction'
    business_type       TEXT NOT NULL,

    industry            TEXT,                    -- e.g. 'Food & Beverage', 'Technology'
    founded_date        TEXT,                    -- YYYY-MM-DD
    description         TEXT,                    -- One-line description of what they do
    country             TEXT DEFAULT 'US',
    currency            TEXT DEFAULT 'USD',

    -- Funding context — critical for runway interpretation
    -- Values: 'bootstrapped', 'seed', 'series_a', 'series_b', 'grant', 'none'
    funding_type        TEXT DEFAULT 'bootstrapped',

    -- Monthly fixed costs that don't change regardless of revenue
    -- (rent, insurance, subscriptions, minimum staff)
    monthly_fixed_costs REAL DEFAULT 0,

    created_at          TEXT DEFAULT (datetime('now'))
);


-- -----------------------------------------------------------------------------
-- bank_accounts
-- A business can have multiple accounts (operating, savings, payroll etc.)
-- Current balance is the source of truth for runway calculations.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bank_accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id     INTEGER NOT NULL REFERENCES businesses(id),
    account_name    TEXT NOT NULL,              -- e.g. 'Main Operating Account'

    -- Values: 'checking', 'savings', 'payroll', 'reserve', 'investment'
    account_type    TEXT NOT NULL DEFAULT 'checking',

    current_balance REAL NOT NULL DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);


-- -----------------------------------------------------------------------------
-- transactions
-- The heartbeat of the financial model.
-- Every dollar in or out is recorded here.
-- The agent mines this table for burn rate, revenue trends, and anomalies.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id     INTEGER NOT NULL REFERENCES businesses(id),
    date            TEXT NOT NULL,              -- YYYY-MM-DD

    -- Type of money movement
    -- Values: 'income', 'expense', 'transfer', 'investment', 'loan_repayment'
    transaction_type TEXT NOT NULL,

    -- Category for grouping and analysis
    -- Income:  'sales', 'services', 'subscription_revenue', 'grant', 'investment'
    -- Expense: 'rent', 'salaries', 'food_cost', 'marketing', 'software',
    --          'utilities', 'inventory', 'loan_repayment', 'equipment', 'misc'
    category        TEXT NOT NULL,

    amount          REAL NOT NULL,              -- Always positive (type determines direction)
    description     TEXT,                       -- Human-readable note
    created_at      TEXT DEFAULT (datetime('now'))
);


-- -----------------------------------------------------------------------------
-- employees
-- Headcount is usually the biggest cost driver.
-- Used by the forecast tool to model salary burn.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id     INTEGER NOT NULL REFERENCES businesses(id),
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,
    department      TEXT,                       -- e.g. 'Engineering', 'Operations'
    monthly_salary  REAL NOT NULL,
    start_date      TEXT NOT NULL,              -- YYYY-MM-DD
    is_active       INTEGER DEFAULT 1           -- 1 = active, 0 = former
);


-- -----------------------------------------------------------------------------
-- loans
-- Debt obligations that affect runway.
-- Monthly payment is a fixed expense the forecast must account for.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS loans (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id         INTEGER NOT NULL REFERENCES businesses(id),
    loan_name           TEXT NOT NULL,          -- e.g. 'SBA Loan', 'Equipment Finance'
    principal           REAL NOT NULL,          -- Original loan amount
    outstanding_balance REAL NOT NULL,          -- What's still owed
    interest_rate       REAL NOT NULL,          -- Annual rate as decimal (0.07 = 7%)
    monthly_payment     REAL NOT NULL,
    start_date          TEXT NOT NULL,
    end_date            TEXT,                   -- NULL if open-ended
    is_active           INTEGER DEFAULT 1
);


-- -----------------------------------------------------------------------------
-- goals
-- What the business is working toward financially.
-- The agent measures progress and forecasts whether goals are achievable.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id     INTEGER NOT NULL REFERENCES businesses(id),
    goal_name       TEXT NOT NULL,              -- e.g. 'Reach 12 months runway'
    goal_type       TEXT NOT NULL,              -- 'runway', 'revenue', 'savings', 'debt_free', 'break_even'
    target_amount   REAL,                       -- Target value (months of runway, revenue amount, etc.)
    target_date     TEXT,                       -- YYYY-MM-DD deadline
    status          TEXT DEFAULT 'active',      -- 'active', 'achieved', 'at_risk', 'failed'
    notes           TEXT
);


-- =============================================================================
-- EXTENSION TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- inventory
-- For: restaurant, retail, bookstore
-- Tracks stock levels and cost of goods — critical for margin analysis.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id         INTEGER NOT NULL REFERENCES businesses(id),
    item_name           TEXT NOT NULL,
    category            TEXT,                   -- e.g. 'Raw Ingredients', 'Books', 'Electronics'
    unit_cost           REAL NOT NULL,          -- What it costs the business per unit
    selling_price       REAL NOT NULL,          -- What they charge customers
    quantity_in_stock   REAL NOT NULL DEFAULT 0,
    reorder_threshold   REAL DEFAULT 0,         -- Alert when stock drops below this
    monthly_usage_avg   REAL DEFAULT 0,         -- Average units consumed/sold per month
    last_updated        TEXT DEFAULT (datetime('now'))
);


-- -----------------------------------------------------------------------------
-- funding_rounds
-- For: funded_startup, bootstrapped_startup (if they raise later)
-- Tracks investment history and remaining capital from each round.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS funding_rounds (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id         INTEGER NOT NULL REFERENCES businesses(id),
    round_name          TEXT NOT NULL,          -- e.g. 'Pre-seed', 'Seed', 'Series A'
    amount_raised       REAL NOT NULL,
    amount_remaining    REAL NOT NULL,          -- How much from this round is still in the bank
    investor_names      TEXT,                   -- Comma-separated list
    close_date          TEXT NOT NULL,          -- YYYY-MM-DD when the round closed
    next_round_target   REAL,                   -- How much they plan to raise next
    next_round_date     TEXT                    -- When they need to close the next round
);


-- -----------------------------------------------------------------------------
-- subscriptions
-- For: SaaS (revenue side) and any business with recurring revenue or costs
-- Tracks both subscriptions they SELL (revenue) and subscriptions they PAY (cost)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscriptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id         INTEGER NOT NULL REFERENCES businesses(id),
    name                TEXT NOT NULL,          -- e.g. 'Pro Plan', 'AWS', 'Salesforce'

    -- 'revenue' = customer paying them, 'cost' = they are paying this
    subscription_type   TEXT NOT NULL,

    -- For revenue subscriptions
    active_subscribers  INTEGER DEFAULT 0,      -- Current paying customers
    price_per_unit      REAL DEFAULT 0,         -- Price per subscriber per billing period
    churn_rate          REAL DEFAULT 0,         -- Monthly % of subscribers who cancel

    -- For cost subscriptions
    monthly_cost        REAL DEFAULT 0,         -- Fixed monthly cost they pay

    billing_period      TEXT DEFAULT 'monthly', -- 'monthly', 'annual'
    start_date          TEXT,
    is_active           INTEGER DEFAULT 1
);


-- -----------------------------------------------------------------------------
-- projects
-- For: freelance, construction, consulting
-- Tracks individual client projects — the primary income unit for these businesses.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id         INTEGER NOT NULL REFERENCES businesses(id),
    client_name         TEXT NOT NULL,
    project_name        TEXT NOT NULL,
    project_value       REAL NOT NULL,          -- Total contract value
    amount_invoiced     REAL DEFAULT 0,         -- How much has been invoiced so far
    amount_paid         REAL DEFAULT 0,         -- How much has actually been received
    start_date          TEXT,
    end_date            TEXT,                   -- NULL if ongoing

    -- Values: 'proposed', 'active', 'completed', 'cancelled'
    status              TEXT DEFAULT 'proposed',
    notes               TEXT
);


-- =============================================================================
-- INDEXES
-- Performance optimisation for the most common agent queries
-- =============================================================================

-- Transactions are queried by business + date range constantly
CREATE INDEX IF NOT EXISTS idx_transactions_business_date
    ON transactions(business_id, date);

-- Category filtering for expense breakdown analysis
CREATE INDEX IF NOT EXISTS idx_transactions_category
    ON transactions(business_id, category);

-- Bank account lookups
CREATE INDEX IF NOT EXISTS idx_bank_accounts_business
    ON bank_accounts(business_id);

-- Active employee queries for salary burn calculations
CREATE INDEX IF NOT EXISTS idx_employees_business_active
    ON employees(business_id, is_active);

-- Goal status lookups
CREATE INDEX IF NOT EXISTS idx_goals_business_status
    ON goals(business_id, status);
