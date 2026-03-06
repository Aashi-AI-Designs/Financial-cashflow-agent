"""
tools/sql_tool.py

The SQL Tool converts a natural language question into a SQL query,
executes it against the SQLite database, and returns the results
in a format the agent can read and reason about.

Why not just let the agent write raw SQL?
- The agent doesn't know our exact schema upfront
- We need to inject schema context so the agent writes valid SQL
- We need safety guardrails (no DROP, DELETE, UPDATE etc.)
- We need to format results clearly so the agent can reason about them

How it works:
    1. Agent calls sql_tool("What is Green Plate Café's current bank balance?")
    2. Tool sends the question + schema context to the LLM
    3. LLM generates a SQL query
    4. Tool executes the query against SQLite
    5. Tool formats and returns the results as a readable string
    6. Agent reads the results and continues reasoning
"""

import logging
import re
import sqlite3

from database.db import get_connection
from config.settings import settings

logger = logging.getLogger(__name__)

# The schema context we inject into every SQL generation prompt
# This is what lets the LLM write valid queries against our database
SCHEMA_CONTEXT = """
DATABASE SCHEMA:

businesses(id, name, business_type, industry, founded_date, description,
           funding_type, monthly_fixed_costs)

bank_accounts(id, business_id, account_name, account_type, current_balance)

transactions(id, business_id, date, transaction_type, category, amount, description)
  transaction_type: 'income', 'expense', 'transfer', 'investment', 'loan_repayment'
  category examples: 'sales', 'services', 'subscription_revenue', 'salaries',
                     'rent', 'food_cost', 'marketing', 'software', 'utilities',
                     'inventory', 'loan_repayment', 'misc'

employees(id, business_id, name, role, department, monthly_salary, start_date, is_active)

loans(id, business_id, loan_name, principal, outstanding_balance,
      interest_rate, monthly_payment, start_date, end_date, is_active)

goals(id, business_id, goal_name, goal_type, target_amount, target_date, status, notes)

inventory(id, business_id, item_name, category, unit_cost, selling_price,
          quantity_in_stock, reorder_threshold, monthly_usage_avg)

funding_rounds(id, business_id, round_name, amount_raised, amount_remaining,
               investor_names, close_date, next_round_target, next_round_date)

subscriptions(id, business_id, name, subscription_type, active_subscribers,
              price_per_unit, churn_rate, monthly_cost, billing_period, is_active)
  subscription_type: 'revenue' (they sell it) or 'cost' (they pay for it)

projects(id, business_id, client_name, project_name, project_value,
         amount_invoiced, amount_paid, start_date, end_date, status)
  status: 'proposed', 'active', 'completed', 'cancelled'

BUSINESS NAMES IN DATABASE:
- Green Plate Café (restaurant)
- Chapter One Books (retail)
- TechSpark SaaS (saas)
- NovaMed Health (funded_startup)
- Bright Loop Studio (freelance)
"""

# SQL keywords that could modify or destroy data — never allowed
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "TRUNCATE", "REPLACE", "ATTACH", "DETACH"
]


def _is_safe_query(sql: str) -> bool:
    """
    Check that a generated SQL query is read-only.
    Rejects any query containing data-modification keywords.
    """
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundary to avoid false positives (e.g. "CREATED_AT" contains "CREATE")
        if re.search(rf'\b{keyword}\b', sql_upper):
            logger.warning("Unsafe SQL keyword detected: %s", keyword)
            return False
    return True


def _extract_sql(text: str) -> str:
    """
    Extract just the SQL query from the LLM's response.
    The LLM might return explanation text around the query — we only want the SQL.
    """
    # Look for SQL between ```sql ... ``` code blocks
    code_block = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if code_block:
        return code_block.group(1).strip()

    # Look for SQL between ``` ... ``` (without sql tag)
    code_block = re.search(r'```\s*(SELECT.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if code_block:
        return code_block.group(1).strip()

    # Look for a SELECT statement directly
    select_match = re.search(r'(SELECT\s+.*?)(?:;|$)', text, re.DOTALL | re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()

    return text.strip()


def _generate_sql(question: str, llm_client) -> str:
    """
    Use the LLM to convert a natural language question into SQL.

    Args:
        question: The natural language question
        llm_client: An initialised LLM client (OpenAI or Ollama wrapper)

    Returns:
        A SQL query string
    """
    prompt = f"""You are a SQL expert. Convert the following question into a SQLite SQL query.

{SCHEMA_CONTEXT}

RULES:
- Only write SELECT queries — never modify data
- Use proper JOINs when data spans multiple tables
- Use strftime for date operations in SQLite
- Return ONLY the SQL query, nothing else
- If you cannot answer with SQL, return: SELECT 'Cannot answer with SQL' as message

QUESTION: {question}

SQL QUERY:"""

    response = llm_client.complete(prompt, max_tokens=500)
    sql = _extract_sql(response)
    logger.debug("Generated SQL: %s", sql)
    return sql


def _execute_query(sql: str) -> list[dict]:
    """
    Execute a SQL query and return results as a list of dicts.
    Each dict represents one row with column names as keys.
    """
    with get_connection() as conn:
        try:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            # sqlite3.Row objects — convert to plain dicts
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("SQL execution error: %s\nQuery: %s", e, sql)
            raise


def _format_results(rows: list[dict], question: str) -> str:
    """
    Format query results as a readable string for the agent.
    The agent reads this string and uses it in its reasoning.
    """
    if not rows:
        return "Query returned no results."

    if len(rows) == 1 and len(rows[0]) == 1:
        # Single value result — return it simply
        value = list(rows[0].values())[0]
        return str(value)

    # Multi-row or multi-column — format as a table
    lines = []
    columns = list(rows[0].keys())

    # Header
    lines.append(" | ".join(columns))
    lines.append("-" * (sum(len(c) for c in columns) + 3 * len(columns)))

    # Rows
    for row in rows[:50]:  # Cap at 50 rows to avoid overwhelming the agent
        values = []
        for col in columns:
            val = row[col]
            if isinstance(val, float):
                values.append(f"{val:,.2f}")
            else:
                values.append(str(val) if val is not None else "NULL")
        lines.append(" | ".join(values))

    if len(rows) > 50:
        lines.append(f"... and {len(rows) - 50} more rows")

    return "\n".join(lines)


class SQLTool:
    """
    The SQL tool the agent calls to query structured financial data.

    Usage:
        tool = SQLTool(llm_client)
        result = tool.run("What is TechSpark's monthly burn rate?")
        # Returns a formatted string the agent can read
    """

    # Tool identity — the agent reads these to decide when to use this tool
    NAME = "sql_tool"
    DESCRIPTION = """Use this tool to query structured financial data from the database.
Use it for questions about: current bank balances, transaction history, revenue figures,
expense breakdowns, employee salaries, loan details, subscription counts, project values,
burn rates, and any other numerical financial data.
Input: a clear natural language question about financial data.
Output: query results as formatted text."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def run(self, question: str) -> str:
        """
        Convert a question to SQL, execute it, and return formatted results.

        Args:
            question: Natural language question about financial data

        Returns:
            Formatted query results as a string, or an error message
        """
        logger.info("SQLTool: %s", question)

        try:
            # Step 1: Generate SQL from the question
            sql = _generate_sql(question, self.llm_client)

            # Step 2: Safety check
            if not _is_safe_query(sql):
                return "Error: Generated query contains unsafe operations and was blocked."

            # Step 3: Execute the query
            rows = _execute_query(sql)

            # Step 4: Format and return
            result = _format_results(rows, question)
            logger.info("SQLTool returned %d rows", len(rows))
            return result

        except sqlite3.Error as e:
            error_msg = f"Database error: {e}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"SQL tool error: {e}"
            logger.error(error_msg)
            return error_msg
