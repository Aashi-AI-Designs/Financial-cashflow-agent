"""
database/seed_db.py

Seeds the database with realistic mock data for 5 businesses,
each with a different type, financial situation, and story.

Why realistic mock data matters:
- The agent's reasoning quality depends on the data quality
- Edge cases (seasonal revenue, lumpy income, funded vs bootstrapped)
  force the agent to reason differently for each business
- We can craft specific scenarios to test specific agent behaviours

The 5 businesses:
  1. Green Plate Café       — Restaurant, thin margins, seasonal revenue
  2. Chapter One Books      — Retail, inventory-heavy, slow burn
  3. TechSpark SaaS         — SaaS startup, fast burn, 6 months runway
  4. NovaMed Health         — Funded startup, pre-revenue, living on investment
  5. Bright Loop Studio     — Freelance studio, lumpy project-based income

Run this script directly:
    python database/seed_db.py
"""

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow running from project root or from database/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import get_connection, initialise_database, get_row_counts

logger = logging.getLogger(__name__)


# =============================================================================
# Helpers
# =============================================================================

def months_ago(n: int) -> str:
    """Return an ISO date string for n months ago from today."""
    d = date.today() - timedelta(days=n * 30)
    return d.strftime("%Y-%m-%d")


def days_ago(n: int) -> str:
    """Return an ISO date string for n days ago from today."""
    d = date.today() - timedelta(days=n)
    return d.strftime("%Y-%m-%d")


def today() -> str:
    return date.today().strftime("%Y-%m-%d")


# =============================================================================
# Business 1: Green Plate Café
# Type: Restaurant | Story: Thin margins, high food costs, seasonal revenue
# Challenge: The agent must recognise that summer revenue spikes don't reflect
#            the annual average — winter months are much leaner.
# =============================================================================

def seed_green_plate_cafe(conn) -> int:
    """Returns the business_id."""
    cursor = conn.execute("""
        INSERT INTO businesses
            (name, business_type, industry, founded_date, description,
             funding_type, monthly_fixed_costs)
        VALUES
            ('Green Plate Café', 'restaurant', 'Food & Beverage',
             '2021-03-15', 'A plant-based café serving breakfast and lunch in downtown Austin.',
             'bootstrapped', 8500)
    """)
    bid = cursor.lastrowid
    logger.debug("Created business: Green Plate Café (id=%d)", bid)

    # Bank accounts
    conn.execute("""
        INSERT INTO bank_accounts (business_id, account_name, account_type, current_balance)
        VALUES
            (?, 'Main Operating Account', 'checking', 18500),
            (?, 'Emergency Reserve',      'savings',   5000)
    """, (bid, bid))

    # Employees
    conn.executemany("""
        INSERT INTO employees (business_id, name, role, department, monthly_salary, start_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Sara Mitchell',  'Head Chef',       'Kitchen',    3800, '2021-03-15'),
        (bid, 'James Okafor',   'Barista',         'Front of House', 2400, '2021-06-01'),
        (bid, 'Priya Nair',     'Waitstaff',       'Front of House', 2200, '2022-01-10'),
        (bid, 'Luis Hernandez', 'Kitchen Assistant','Kitchen',   2000, '2022-08-01'),
    ])

    # Loans
    conn.execute("""
        INSERT INTO loans
            (business_id, loan_name, principal, outstanding_balance,
             interest_rate, monthly_payment, start_date, end_date)
        VALUES
            (?, 'SBA Equipment Loan', 45000, 28000, 0.065, 950, '2021-04-01', '2026-04-01')
    """, (bid,))

    # Goals
    conn.executemany("""
        INSERT INTO goals (business_id, goal_name, goal_type, target_amount, target_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Build 6 months emergency reserve', 'savings', 51000,
         '2025-12-31', 'at_risk', 'Currently have ~1.4 months. Seasonal dip in winter hurting savings rate.'),
        (bid, 'Break even on catering division', 'break_even', None,
         '2025-06-30', 'active', 'Launched catering in Jan 2024. Currently losing $800/month on it.'),
    ])

    # Transactions — 12 months of history
    # Restaurant pattern: high food costs (~32% of revenue), seasonal revenue peaks in summer
    transactions = []

    monthly_data = [
        # (months_ago, revenue, food_cost, salaries, rent, utilities, marketing, loan_repay, misc)
        (12, 31000, 9920, 10400, 4200, 820, 400, 950, 600),   # Low season
        (11, 29500, 9440, 10400, 4200, 780, 300, 950, 450),
        (10, 33000, 10560, 10400, 4200, 800, 500, 950, 380),
        (9,  38000, 12160, 10400, 4200, 850, 600, 950, 420),   # Spring pickup
        (8,  44000, 14080, 10400, 4200, 900, 700, 950, 550),
        (7,  52000, 16640, 10400, 4200, 980, 800, 950, 480),   # Summer peak
        (6,  54000, 17280, 10400, 4200, 960, 800, 950, 620),
        (5,  49000, 15680, 10400, 4200, 940, 700, 950, 510),
        (4,  41000, 13120, 10400, 4200, 880, 500, 950, 390),   # Autumn slowdown
        (3,  35000, 11200, 10400, 4200, 810, 400, 950, 440),
        (2,  30000, 9600,  10400, 4200, 790, 300, 950, 380),   # Winter dip
        (1,  28000, 8960,  10400, 4200, 770, 300, 950, 420),
    ]

    for m, rev, food, sal, rent, util, mkt, loan, misc in monthly_data:
        base_date = months_ago(m)
        transactions += [
            (bid, base_date, 'income',         'sales',          rev,  'Monthly café revenue'),
            (bid, base_date, 'expense',         'food_cost',      food, 'Food & beverage purchases'),
            (bid, base_date, 'expense',         'salaries',       sal,  'Staff salaries'),
            (bid, base_date, 'expense',         'rent',           rent, 'Premises rent'),
            (bid, base_date, 'expense',         'utilities',      util, 'Gas, electricity, water'),
            (bid, base_date, 'expense',         'marketing',      mkt,  'Social media & local ads'),
            (bid, base_date, 'loan_repayment',  'loan_repayment', loan, 'SBA equipment loan'),
            (bid, base_date, 'expense',         'misc',           misc, 'Packaging, cleaning, misc'),
        ]

    # Inventory
    conn.executemany("""
        INSERT INTO inventory
            (business_id, item_name, category, unit_cost, selling_price,
             quantity_in_stock, reorder_threshold, monthly_usage_avg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Coffee Beans (1kg)',  'Beverages',   18.00, None, 45,  10, 40),
        (bid, 'Oat Milk (1L)',       'Beverages',    1.80, None, 120, 30, 110),
        (bid, 'Avocado (each)',      'Produce',      1.20, None, 80,  20, 75),
        (bid, 'Sourdough Loaf',      'Bakery',       3.50, None, 30,  10, 28),
        (bid, 'Mixed Salad Greens',  'Produce',      4.00, None, 15,   5, 14),
    ])

    return bid, transactions


# =============================================================================
# Business 2: Chapter One Books
# Type: Retail | Story: Inventory-heavy, slow burn, competing with Amazon
# Challenge: Inventory carrying cost eats into cash — the agent must recognise
#            that cash tied up in stock isn't the same as cash in the bank.
# =============================================================================

def seed_chapter_one_books(conn) -> int:
    cursor = conn.execute("""
        INSERT INTO businesses
            (name, business_type, industry, founded_date, description,
             funding_type, monthly_fixed_costs)
        VALUES
            ('Chapter One Books', 'retail', 'Retail',
             '2019-09-01', 'Independent bookstore specialising in fiction and local authors in Portland, OR.',
             'bootstrapped', 6200)
    """)
    bid = cursor.lastrowid
    logger.debug("Created business: Chapter One Books (id=%d)", bid)

    conn.execute("""
        INSERT INTO bank_accounts (business_id, account_name, account_type, current_balance)
        VALUES
            (?, 'Operating Account', 'checking', 24000),
            (?, 'Holiday Stock Fund', 'savings',   8000)
    """, (bid, bid))

    conn.executemany("""
        INSERT INTO employees (business_id, name, role, department, monthly_salary, start_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Diana Cheng',    'Store Manager', 'Operations', 3600, '2019-09-01'),
        (bid, 'Tom Bradley',    'Sales Associate','Floor',     2200, '2020-02-01'),
        (bid, 'Amara Diallo',   'Sales Associate','Floor',     2200, '2021-05-15'),
    ])

    conn.executemany("""
        INSERT INTO goals (business_id, goal_name, goal_type, target_amount, target_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Maintain 4 months cash runway at all times', 'runway', 4, None,
         'at_risk', 'Currently at 3.1 months. Holiday season critical.'),
        (bid, 'Launch online store by Q3', 'revenue', None,
         '2025-09-30', 'active', 'Hoping to offset foot traffic decline with online sales.'),
    ])

    transactions = []
    monthly_data = [
        # Revenue is very seasonal — big December spike for holiday gifts
        (12, 18000, 8000, 8000, 3200, 350, 300, 500),
        (11, 16500, 7300, 8000, 3200, 320, 200, 400),
        (10, 17000, 7500, 8000, 3200, 340, 250, 380),
        (9,  19000, 8400, 8000, 3200, 350, 300, 420),
        (8,  21000, 9300, 8000, 3200, 360, 350, 390),
        (7,  24000, 10600,8000, 3200, 370, 400, 450),
        (6,  27000, 11900,8000, 3200, 380, 450, 480),
        (5,  22000, 9700, 8000, 3200, 360, 350, 410),
        (4,  20000, 8800, 8000, 3200, 350, 300, 380),
        (3,  19500, 8600, 8000, 3200, 345, 280, 370),
        (2,  16000, 7000, 8000, 3200, 315, 200, 360),
        (1,  38000, 16800,8000, 3200, 400, 800, 600),  # December holiday spike
    ]

    for m, rev, cogs, sal, rent, util, mkt, misc in monthly_data:
        base_date = months_ago(m)
        transactions += [
            (bid, base_date, 'income',  'sales',     rev,  'Book sales'),
            (bid, base_date, 'expense', 'inventory', cogs, 'Book purchases from distributors'),
            (bid, base_date, 'expense', 'salaries',  sal,  'Staff salaries'),
            (bid, base_date, 'expense', 'rent',      rent, 'Store rent'),
            (bid, base_date, 'expense', 'utilities', util, 'Electricity & internet'),
            (bid, base_date, 'expense', 'marketing', mkt,  'Events, social media'),
            (bid, base_date, 'expense', 'misc',      misc, 'Bags, receipts, misc supplies'),
        ]

    conn.executemany("""
        INSERT INTO inventory
            (business_id, item_name, category, unit_cost, selling_price,
             quantity_in_stock, reorder_threshold, monthly_usage_avg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Fiction (avg)',        'Books', 9.00,  18.00, 820, 150, 280),
        (bid, 'Non-Fiction (avg)',    'Books', 10.50, 22.00, 460, 80,  140),
        (bid, 'Children\'s (avg)',    'Books', 7.00,  14.00, 340, 60,  120),
        (bid, 'Gift Cards',           'Other', 0,     50.00, 100, 20,  35),
        (bid, 'Bookmarks & Merch',    'Other', 2.00,  8.00,  200, 40,  60),
    ])

    return bid, transactions


# =============================================================================
# Business 3: TechSpark SaaS
# Type: SaaS Startup | Story: Fast burn, 6 months runway, needs to hit MRR target
# Challenge: The agent must reason about MRR growth vs burn — can they grow
#            revenue fast enough before the runway runs out?
# =============================================================================

def seed_techspark_saas(conn) -> int:
    cursor = conn.execute("""
        INSERT INTO businesses
            (name, business_type, industry, founded_date, description,
             funding_type, monthly_fixed_costs)
        VALUES
            ('TechSpark SaaS', 'saas', 'Technology',
             '2023-01-10', 'B2B project management tool for remote engineering teams.',
             'bootstrapped', 22000)
    """)
    bid = cursor.lastrowid
    logger.debug("Created business: TechSpark SaaS (id=%d)", bid)

    conn.execute("""
        INSERT INTO bank_accounts (business_id, account_name, account_type, current_balance)
        VALUES
            (?, 'Main Operating Account', 'checking', 138000),
            (?, 'Payroll Buffer',         'savings',   20000)
    """, (bid, bid))

    conn.executemany("""
        INSERT INTO employees (business_id, name, role, department, monthly_salary, start_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Alex Reid',      'CEO & Co-founder',     'Leadership',  6000, '2023-01-10'),
        (bid, 'Mia Tanaka',     'CTO & Co-founder',     'Engineering', 6000, '2023-01-10'),
        (bid, 'Jordan Lee',     'Senior Engineer',       'Engineering', 7500, '2023-03-01'),
        (bid, 'Fatima Al-Amin', 'Product Manager',       'Product',    5500, '2023-06-01'),
        (bid, 'Chris Dawson',   'Growth Marketer',       'Marketing',  4800, '2024-01-15'),
    ])

    conn.executemany("""
        INSERT INTO goals (business_id, goal_name, goal_type, target_amount, target_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Reach $25k MRR before runway expires', 'revenue', 25000,
         '2025-08-31', 'at_risk',
         'Currently at $14.2k MRR. Need ~$10k more to be default alive. Burn is $26k/month.'),
        (bid, 'Extend runway to 12 months via seed round', 'runway', 12,
         '2025-07-01', 'active', 'Targeting $600k seed. First meetings scheduled.'),
    ])

    # SaaS subscriptions they SELL
    conn.executemany("""
        INSERT INTO subscriptions
            (business_id, name, subscription_type, active_subscribers,
             price_per_unit, churn_rate, billing_period, start_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Starter Plan',     'revenue', 180, 29,  0.06, 'monthly', '2023-06-01', 1),
        (bid, 'Pro Plan',         'revenue', 94,  79,  0.04, 'monthly', '2023-08-01', 1),
        (bid, 'Enterprise Plan',  'revenue', 12,  299, 0.02, 'monthly', '2024-01-01', 1),
    ])

    # SaaS tools they PAY FOR
    conn.executemany("""
        INSERT INTO subscriptions
            (business_id, name, subscription_type, monthly_cost, billing_period, start_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'AWS',            'cost', 3800, 'monthly', '2023-01-10', 1),
        (bid, 'GitHub',         'cost', 84,   'monthly', '2023-01-10', 1),
        (bid, 'Slack',          'cost', 180,  'monthly', '2023-03-01', 1),
        (bid, 'Intercom',       'cost', 390,  'monthly', '2023-06-01', 1),
        (bid, 'Figma',          'cost', 75,   'monthly', '2023-03-01', 1),
        (bid, 'Datadog',        'cost', 420,  'monthly', '2024-01-15', 1),
    ])

    transactions = []
    # MRR growing from ~$7k to ~$14k over 12 months, burn rate ~$26k/month
    monthly_data = [
        # (months_ago, subscription_revenue, salaries, aws, other_software, marketing, misc)
        (12,  7200, 25800, 2800, 800, 1200, 600),
        (11,  8100, 25800, 3000, 850, 1500, 550),
        (10,  9300, 25800, 3100, 900, 1800, 490),
        (9,  10100, 29800, 3200, 900, 2000, 520),  # New hire joins
        (8,  10900, 29800, 3300, 950, 2200, 480),
        (7,  11600, 29800, 3400, 980, 2500, 510),
        (6,  12100, 29800, 3500, 1000,2800, 540),
        (5,  12800, 29800, 3600, 1050,3000, 490),
        (4,  13200, 29800, 3700, 1100,3200, 520),
        (3,  13600, 29800, 3750, 1100,3400, 480),
        (2,  14000, 29800, 3800, 1149,3600, 510),
        (1,  14200, 29800, 3800, 1149,3800, 530),
    ]

    for m, rev, sal, aws, soft, mkt, misc in monthly_data:
        base_date = months_ago(m)
        transactions += [
            (bid, base_date, 'income',  'subscription_revenue', rev,  'Monthly subscription revenue'),
            (bid, base_date, 'expense', 'salaries',             sal,  'Team salaries'),
            (bid, base_date, 'expense', 'software',             aws,  'AWS infrastructure'),
            (bid, base_date, 'expense', 'software',             soft, 'Software tools (Slack, GitHub, etc.)'),
            (bid, base_date, 'expense', 'marketing',            mkt,  'Paid acquisition, content'),
            (bid, base_date, 'expense', 'misc',                 misc, 'Legal, accounting, misc'),
        ]

    return bid, transactions


# =============================================================================
# Business 4: NovaMed Health
# Type: Funded Startup | Story: Pre-revenue, living on seed funding
# Challenge: No revenue yet — runway is purely about how fast they burn
#            through investor capital. Agent must flag when next round is needed.
# =============================================================================

def seed_novamed_health(conn) -> int:
    cursor = conn.execute("""
        INSERT INTO businesses
            (name, business_type, industry, founded_date, description,
             funding_type, monthly_fixed_costs)
        VALUES
            ('NovaMed Health', 'funded_startup', 'Healthcare Technology',
             '2024-02-01', 'AI-powered diagnostic assistant for rural health clinics.',
             'seed', 18000)
    """)
    bid = cursor.lastrowid
    logger.debug("Created business: NovaMed Health (id=%d)", bid)

    conn.execute("""
        INSERT INTO bank_accounts (business_id, account_name, account_type, current_balance)
        VALUES
            (?, 'Operating Account',  'checking', 285000),
            (?, 'Seed Capital Hold',  'savings',  120000)
    """, (bid, bid))

    conn.executemany("""
        INSERT INTO employees (business_id, name, role, department, monthly_salary, start_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Dr. Priya Sharma', 'CEO & Co-founder',  'Leadership',  7000, '2024-02-01'),
        (bid, 'Ben Okoro',        'CTO & Co-founder',  'Engineering', 7000, '2024-02-01'),
        (bid, 'Lena Fischer',     'ML Engineer',        'Engineering', 8500, '2024-04-01'),
        (bid, 'Marcus Webb',      'Clinical Advisor',   'Medical',    4500, '2024-05-01'),
    ])

    # Funding rounds
    conn.execute("""
        INSERT INTO funding_rounds
            (business_id, round_name, amount_raised, amount_remaining,
             investor_names, close_date, next_round_target, next_round_date)
        VALUES
            (?, 'Pre-seed', 150000, 0,
             'Angel Syndicate Austin', '2024-01-15', NULL, NULL)
    """, (bid,))

    conn.execute("""
        INSERT INTO funding_rounds
            (business_id, round_name, amount_raised, amount_remaining,
             investor_names, close_date, next_round_target, next_round_date)
        VALUES
            (?, 'Seed', 800000, 405000,
             'HealthTech Ventures, MedSeed Fund', '2024-06-01', 3000000, '2026-01-01')
    """, (bid,))

    conn.executemany("""
        INSERT INTO goals (business_id, goal_name, goal_type, target_amount, target_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Complete FDA pilot study', 'revenue', None,
         '2025-09-30', 'active', 'Required before commercial launch. 3 clinics enrolled.'),
        (bid, 'Close Series A before seed expires', 'runway', 18,
         '2026-01-01', 'active',
         'Need 18 months runway from Series A. Current burn: $27k/month. ~15 months left.'),
        (bid, 'First paying customer', 'revenue', 1,
         '2025-12-31', 'active', 'Targeting pilot clinic as first paid contract.'),
    ])

    # SaaS tools
    conn.executemany("""
        INSERT INTO subscriptions
            (business_id, name, subscription_type, monthly_cost, billing_period, start_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'AWS (HIPAA)',      'cost', 4200, 'monthly', '2024-02-01', 1),
        (bid, 'GitHub Enterprise','cost', 210,  'monthly', '2024-02-01', 1),
        (bid, 'Notion',          'cost', 48,   'monthly', '2024-02-01', 1),
        (bid, 'Slack',           'cost', 120,  'monthly', '2024-04-01', 1),
    ])

    transactions = []
    # Pre-revenue — only expenses, funded by seed investment
    monthly_data = [
        # (months_ago, salaries, aws, other_soft, research, legal, misc)
        (9,  18000, 3800, 400, 2200, 1800, 800),
        (8,  18000, 3900, 420, 2400, 600,  750),
        (7,  27000, 4000, 430, 2600, 500,  680),   # ML engineer joins
        (6,  27000, 4100, 430, 2800, 400,  720),
        (5,  27000, 4100, 440, 3000, 300,  690),
        (4,  27000, 4150, 450, 3200, 800,  710),   # Clinical advisor joins
        (3,  27000, 4200, 450, 3400, 500,  680),
        (2,  27000, 4200, 458, 3600, 400,  660),
        (1,  27000, 4200, 458, 3800, 300,  640),
    ]

    for m, sal, aws, soft, research, legal, misc in monthly_data:
        base_date = months_ago(m)
        transactions += [
            (bid, base_date, 'expense', 'salaries',  sal,      'Team salaries'),
            (bid, base_date, 'expense', 'software',  aws,      'AWS HIPAA-compliant infrastructure'),
            (bid, base_date, 'expense', 'software',  soft,     'Software subscriptions'),
            (bid, base_date, 'expense', 'misc',      research, 'Research & clinical study costs'),
            (bid, base_date, 'expense', 'misc',      legal,    'Legal & compliance'),
            (bid, base_date, 'expense', 'misc',      misc,     'Office & operational expenses'),
        ]

    # Record the seed funding as investment income
    transactions.append(
        (bid, months_ago(9), 'investment', 'investment', 800000, 'Seed round — HealthTech Ventures & MedSeed Fund')
    )

    return bid, transactions


# =============================================================================
# Business 5: Bright Loop Studio
# Type: Freelance | Story: Lumpy project income, feast or famine pattern
# Challenge: Average monthly income looks fine but cash gaps between projects
#            create real stress. Agent must recognise timing risk, not just averages.
# =============================================================================

def seed_bright_loop_studio(conn) -> int:
    cursor = conn.execute("""
        INSERT INTO businesses
            (name, business_type, industry, founded_date, description,
             funding_type, monthly_fixed_costs)
        VALUES
            ('Bright Loop Studio', 'freelance', 'Creative Services',
             '2022-07-01', 'Brand identity and UX design studio serving tech startups.',
             'bootstrapped', 3800)
    """)
    bid = cursor.lastrowid
    logger.debug("Created business: Bright Loop Studio (id=%d)", bid)

    conn.execute("""
        INSERT INTO bank_accounts (business_id, account_name, account_type, current_balance)
        VALUES
            (?, 'Business Current',  'checking', 19500),
            (?, 'Tax Reserve',       'savings',   8000)
    """, (bid, bid))

    conn.executemany("""
        INSERT INTO employees (business_id, name, role, department, monthly_salary, start_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Sofia Reyes',    'Creative Director (Owner)', 'Design', 5000, '2022-07-01'),
        (bid, 'Noah Park',      'UX Designer',               'Design', 4200, '2023-03-01'),
    ])

    conn.executemany("""
        INSERT INTO goals (business_id, goal_name, goal_type, target_amount, target_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Build 3 months cash buffer to survive slow periods', 'savings', 27000,
         '2025-09-30', 'active',
         'Currently have ~2.3 months. One bad month away from stress.'),
        (bid, 'Add one retainer client to stabilise income', 'revenue', 4000,
         '2025-06-30', 'active', 'Retainers would smooth out the feast-famine cycle.'),
    ])

    # Active and recent projects
    conn.executemany("""
        INSERT INTO projects
            (business_id, client_name, project_name, project_value,
             amount_invoiced, amount_paid, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        (bid, 'Meridian Health App', 'Brand Identity & Design System',
         18000, 18000, 18000, months_ago(8), months_ago(5), 'completed'),
        (bid, 'Vero Finance',        'UX Audit & Redesign',
         12000, 12000, 9000, months_ago(5), months_ago(2), 'completed'),
        (bid, 'Rootsy Foods',        'Website & Brand Refresh',
         9500, 9500, 9500, months_ago(3), months_ago(1), 'completed'),
        (bid, 'Pulsar Analytics',    'Product UI Design',
         22000, 11000, 5500, months_ago(2), None, 'active'),
        (bid, 'Unnamed Client',      'Brand Identity (Proposed)',
         8000, 0, 0, None, None, 'proposed'),
    ])

    transactions = []
    # Lumpy income — some months have big payments, some have nothing incoming
    monthly_data = [
        # (months_ago, income, salaries, software, rent_cowork, marketing, misc)
        (12,  0,     9200, 280, 600, 200, 300),   # Dry month between projects
        (11, 9000,   9200, 280, 600, 150, 280),   # 50% deposit on Meridian
        (10,  0,     9200, 280, 600, 100, 260),
        (9,  9000,   9200, 280, 600, 200, 290),   # Final on Meridian
        (8,  6000,   9200, 280, 600, 180, 270),   # 50% deposit on Vero
        (7,   0,     9200, 280, 600, 120, 250),
        (6,  9500,   9200, 280, 600, 150, 280),   # Rootsy full payment + Vero partial
        (5,  3000,   9200, 280, 600, 200, 260),   # Vero final partial
        (4,  9500,   9200, 280, 600, 180, 270),   # Rootsy final payment
        (3,  5500,   9200, 280, 600, 150, 250),   # Pulsar 25% deposit
        (2,   0,     9200, 280, 600, 100, 240),   # Waiting on Pulsar milestone
        (1,  5500,   9200, 280, 600, 200, 260),   # Pulsar milestone payment
    ]

    for m, inc, sal, soft, cowork, mkt, misc in monthly_data:
        base_date = months_ago(m)
        if inc > 0:
            transactions.append(
                (bid, base_date, 'income', 'services', inc, 'Client project payment')
            )
        transactions += [
            (bid, base_date, 'expense', 'salaries',  sal,    'Owner draw + contractor'),
            (bid, base_date, 'expense', 'software',  soft,   'Figma, Adobe, project tools'),
            (bid, base_date, 'expense', 'rent',      cowork, 'Co-working space'),
            (bid, base_date, 'expense', 'marketing', mkt,    'Portfolio site, Dribbble, outreach'),
            (bid, base_date, 'expense', 'misc',      misc,   'Accounting, misc'),
        ]

    return bid, transactions


# =============================================================================
# Main seeding function
# =============================================================================

def seed_all() -> None:
    """
    Seed all 5 businesses into the database.
    Wipes existing data first to ensure a clean state.
    """
    from config.logging_config import setup_logging
    from config.settings import settings
    setup_logging(log_level=settings.LOG_LEVEL)

    logger.info("Initialising database schema...")
    initialise_database()

    logger.info("Seeding mock business data...")

    all_transactions = []

    with get_connection() as conn:
        # Clear existing data (order matters for foreign keys)
        tables = [
            'projects', 'subscriptions', 'funding_rounds', 'inventory',
            'goals', 'loans', 'employees', 'transactions',
            'bank_accounts', 'businesses'
        ]
        for table in tables:
            conn.execute(f"DELETE FROM {table}")
        logger.debug("Cleared existing data")

        # Seed each business
        bid1, t1 = seed_green_plate_cafe(conn)
        bid2, t2 = seed_chapter_one_books(conn)
        bid3, t3 = seed_techspark_saas(conn)
        bid4, t4 = seed_novamed_health(conn)
        bid5, t5 = seed_bright_loop_studio(conn)

        all_transactions = t1 + t2 + t3 + t4 + t5

        # Bulk insert all transactions
        conn.executemany("""
            INSERT INTO transactions
                (business_id, date, transaction_type, category, amount, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, all_transactions)

        logger.info("Inserted %d transactions across 5 businesses", len(all_transactions))

    # Confirm row counts
    counts = get_row_counts()
    print("\n=== Database Seeded Successfully ===")
    for table, count in counts.items():
        if count > 0:
            print(f"  {table:<20} {count:>4} rows")
    print("=" * 36)
    print("\n✅ Module 2 complete — database is ready.\n")


if __name__ == "__main__":
    seed_all()
