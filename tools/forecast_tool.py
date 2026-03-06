"""
tools/forecast_tool.py

The Forecast Tool runs forward-looking financial projections.
Unlike the SQL tool (what IS) and RAG tool (what SHOULD BE),
the forecast tool answers "where are we HEADING?"

It is a pure calculation engine — no LLM involved.
The agent provides parameters, the tool runs the maths,
and returns clear projection results.

Forecasts available:
1. runway_forecast      — how many months until cash runs out
2. burn_rate_analysis   — detailed breakdown of what's burning cash
3. scenario_forecast    — what happens if costs/revenue change by X%
4. goal_gap_analysis    — how far is a business from its financial goals
"""

import logging
from datetime import date, timedelta
from database.db import get_connection

logger = logging.getLogger(__name__)


# =============================================================================
# Data fetching helpers
# =============================================================================

def _get_business(business_name: str) -> dict | None:
    """Fetch a business record by name (case-insensitive partial match)."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM businesses
            WHERE LOWER(name) LIKE LOWER(?)
            LIMIT 1
        """, (f"%{business_name}%",)).fetchone()
    return dict(row) if row else None


def _get_total_cash(business_id: int) -> float:
    """Sum of all bank account balances for a business."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(current_balance), 0) as total
            FROM bank_accounts
            WHERE business_id = ?
        """, (business_id,)).fetchone()
    return row["total"] if row else 0.0


def _get_monthly_averages(business_id: int, months: int = 3) -> dict:
    """
    Calculate average monthly income and expenses over the last N months.
    Using a rolling average smooths out one-off spikes and seasonal effects.
    """
    cutoff_date = (date.today() - timedelta(days=months * 30)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        # Average monthly income
        income_row = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) / ? as avg_monthly
            FROM transactions
            WHERE business_id = ?
              AND transaction_type = 'income'
              AND date >= ?
        """, (months, business_id, cutoff_date)).fetchone()

        # Average monthly expenses (all outflows)
        expense_row = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) / ? as avg_monthly
            FROM transactions
            WHERE business_id = ?
              AND transaction_type IN ('expense', 'loan_repayment')
              AND date >= ?
        """, (months, business_id, cutoff_date)).fetchone()

        # Expense breakdown by category
        category_rows = conn.execute("""
            SELECT category,
                   ROUND(SUM(amount) / ?, 2) as avg_monthly,
                   ROUND(SUM(amount) / ? * 100.0 / NULLIF(
                       (SELECT SUM(amount) FROM transactions
                        WHERE business_id = ?
                          AND transaction_type IN ('expense', 'loan_repayment')
                          AND date >= ?), 0), 1) as pct_of_total
            FROM transactions
            WHERE business_id = ?
              AND transaction_type IN ('expense', 'loan_repayment')
              AND date >= ?
            GROUP BY category
            ORDER BY avg_monthly DESC
        """, (months, months, business_id, cutoff_date,
              business_id, cutoff_date)).fetchall()

    return {
        "avg_monthly_income": round(income_row["avg_monthly"], 2),
        "avg_monthly_expenses": round(expense_row["avg_monthly"], 2),
        "expense_breakdown": [dict(r) for r in category_rows],
        "months_analysed": months,
    }


# =============================================================================
# Forecast calculations
# =============================================================================

def _runway_forecast(business_id: int, business_name: str) -> str:
    """
    Calculate how many months the business can survive at current burn rate.

    Formula: Runway = Total Cash / Monthly Net Burn
    Net Burn = Monthly Expenses - Monthly Income
    """
    cash = _get_total_cash(business_id)
    averages = _get_monthly_averages(business_id, months=3)

    income = averages["avg_monthly_income"]
    expenses = averages["avg_monthly_expenses"]
    net_burn = expenses - income

    lines = [f"RUNWAY FORECAST: {business_name}"]
    lines.append("=" * 50)
    lines.append(f"Current cash balance   : ${cash:>12,.2f}")
    lines.append(f"Avg monthly income     : ${income:>12,.2f}")
    lines.append(f"Avg monthly expenses   : ${expenses:>12,.2f}")
    lines.append(f"Net burn rate          : ${net_burn:>12,.2f}/month")
    lines.append("")

    if net_burn <= 0:
        # Business is cash flow positive
        surplus = abs(net_burn)
        lines.append(f"✅ Business is cash flow POSITIVE by ${surplus:,.2f}/month")
        lines.append(f"   At this rate, cash reserves grow by ${surplus * 12:,.2f}/year")
        months_to_double = cash / surplus if surplus > 0 else float('inf')
        lines.append(f"   Cash doubles in approximately {months_to_double:.0f} months")
    else:
        runway_months = cash / net_burn

        lines.append(f"Runway                 : {runway_months:.1f} months")

        # Calculate the date cash runs out
        runout_date = date.today() + timedelta(days=runway_months * 30)
        lines.append(f"Cash runs out          : {runout_date.strftime('%B %Y')}")
        lines.append("")

        # Risk assessment
        if runway_months < 2:
            lines.append("🚨 CRITICAL: Less than 2 months runway. Immediate action required.")
        elif runway_months < 3:
            lines.append("🔴 DANGER ZONE: Less than 3 months runway.")
        elif runway_months < 6:
            lines.append("🟡 WARNING: Below recommended 6-month minimum.")
        elif runway_months < 12:
            lines.append("🟠 CAUTION: Below ideal 12-month target.")
        else:
            lines.append("🟢 HEALTHY: Runway meets or exceeds 12-month benchmark.")

    return "\n".join(lines)


def _burn_rate_analysis(business_id: int, business_name: str) -> str:
    """
    Break down what's driving expenses and identify the biggest cost categories.
    """
    averages = _get_monthly_averages(business_id, months=3)
    income = averages["avg_monthly_income"]
    expenses = averages["avg_monthly_expenses"]
    breakdown = averages["expense_breakdown"]

    lines = [f"BURN RATE ANALYSIS: {business_name}"]
    lines.append("=" * 50)
    lines.append(f"Avg monthly revenue  : ${income:>10,.2f}")
    lines.append(f"Avg monthly expenses : ${expenses:>10,.2f}")
    lines.append(f"Net burn / surplus   : ${income - expenses:>+10,.2f}")
    lines.append("")
    lines.append("EXPENSE BREAKDOWN (last 3 months avg):")
    lines.append(f"{'Category':<20} {'Monthly Avg':>12} {'% of Total':>12}")
    lines.append("-" * 46)

    for row in breakdown:
        lines.append(
            f"{row['category']:<20} ${row['avg_monthly']:>10,.2f} {row['pct_of_total']:>10.1f}%"
        )

    # Flag the top cost driver
    if breakdown:
        top = breakdown[0]
        lines.append("")
        lines.append(
            f"⚠️  Largest cost driver: {top['category']} "
            f"(${top['avg_monthly']:,.2f}/month, {top['pct_of_total']}% of expenses)"
        )

    return "\n".join(lines)


def _scenario_forecast(
    business_id: int,
    business_name: str,
    cost_change_pct: float = 0,
    revenue_change_pct: float = 0,
) -> str:
    """
    Model what happens to runway if costs or revenue change by a percentage.

    Example: cost_change_pct=-20 means "what if we cut costs by 20%?"
             revenue_change_pct=15 means "what if revenue grows by 15%?"
    """
    cash = _get_total_cash(business_id)
    averages = _get_monthly_averages(business_id, months=3)

    base_income = averages["avg_monthly_income"]
    base_expenses = averages["avg_monthly_expenses"]
    base_burn = base_expenses - base_income
    base_runway = cash / base_burn if base_burn > 0 else float('inf')

    # Apply scenario changes
    new_income = base_income * (1 + revenue_change_pct / 100)
    new_expenses = base_expenses * (1 + cost_change_pct / 100)
    new_burn = new_expenses - new_income
    new_runway = cash / new_burn if new_burn > 0 else float('inf')

    runway_change = new_runway - base_runway

    lines = [f"SCENARIO FORECAST: {business_name}"]
    lines.append("=" * 50)

    if cost_change_pct != 0:
        direction = "reduction" if cost_change_pct < 0 else "increase"
        lines.append(f"Scenario: {abs(cost_change_pct):.0f}% cost {direction}")
    if revenue_change_pct != 0:
        direction = "growth" if revenue_change_pct > 0 else "decline"
        lines.append(f"Scenario: {abs(revenue_change_pct):.0f}% revenue {direction}")

    lines.append("")
    lines.append(f"{'':25} {'CURRENT':>12} {'SCENARIO':>12} {'CHANGE':>10}")
    lines.append("-" * 62)
    lines.append(
        f"{'Monthly income':<25} ${base_income:>10,.2f} ${new_income:>10,.2f} "
        f"${new_income - base_income:>+8,.2f}"
    )
    lines.append(
        f"{'Monthly expenses':<25} ${base_expenses:>10,.2f} ${new_expenses:>10,.2f} "
        f"${new_expenses - base_expenses:>+8,.2f}"
    )
    lines.append(
        f"{'Net burn rate':<25} ${base_burn:>10,.2f} ${new_burn:>10,.2f} "
        f"${new_burn - base_burn:>+8,.2f}"
    )

    if base_runway == float('inf'):
        lines.append(f"{'Runway (months)':<25} {'∞':>12}", )
    else:
        lines.append(f"{'Runway (months)':<25} {base_runway:>11.1f}m", )

    if new_runway == float('inf'):
        lines.append(f"{'New runway':<25} {'∞ (cash flow positive)':>22}")
    else:
        lines.append(
            f"{'New runway':<25} {new_runway:>11.1f}m {runway_change:>+9.1f}m"
        )

    lines.append("")
    if new_runway == float('inf'):
        lines.append("✅ This scenario makes the business cash flow positive.")
    elif new_runway > base_runway:
        lines.append(
            f"✅ This scenario extends runway by {runway_change:.1f} months "
            f"({runway_change / base_runway * 100:.0f}% improvement)."
        )
    else:
        lines.append(
            f"🔴 This scenario reduces runway by {abs(runway_change):.1f} months."
        )

    return "\n".join(lines)


def _goal_gap_analysis(business_id: int, business_name: str) -> str:
    """
    Analyse how far the business is from its financial goals
    and whether they are achievable at the current trajectory.
    """
    with get_connection() as conn:
        goals = conn.execute("""
            SELECT * FROM goals
            WHERE business_id = ? AND status = 'active'
            ORDER BY target_date
        """, (business_id,)).fetchall()

    if not goals:
        return f"No active goals found for {business_name}."

    cash = _get_total_cash(business_id)
    averages = _get_monthly_averages(business_id, months=3)
    monthly_surplus = averages["avg_monthly_income"] - averages["avg_monthly_expenses"]

    lines = [f"GOAL GAP ANALYSIS: {business_name}"]
    lines.append("=" * 50)

    for goal in goals:
        goal = dict(goal)
        lines.append(f"\nGoal: {goal['goal_name']}")
        lines.append(f"Type: {goal['goal_type']} | Status: {goal['status']}")

        if goal["target_date"]:
            target = date.fromisoformat(goal["target_date"])
            months_remaining = max(0, (target - date.today()).days / 30)
            lines.append(f"Deadline: {target.strftime('%B %Y')} ({months_remaining:.0f} months away)")

        if goal["target_amount"] and goal["goal_type"] == "savings":
            gap = goal["target_amount"] - cash
            if gap <= 0:
                lines.append(f"✅ ACHIEVED: Current cash ${cash:,.2f} exceeds target ${goal['target_amount']:,.2f}")
            else:
                lines.append(f"Gap to target: ${gap:,.2f}")
                if monthly_surplus > 0:
                    months_to_goal = gap / monthly_surplus
                    lines.append(f"At current surplus of ${monthly_surplus:,.2f}/month → achievable in {months_to_goal:.0f} months")
                    if goal["target_date"]:
                        if months_to_goal <= months_remaining:
                            lines.append("✅ On track to meet deadline")
                        else:
                            lines.append(f"🔴 Will miss deadline by ~{months_to_goal - months_remaining:.0f} months")
                else:
                    lines.append("🔴 Currently burning cash — goal not achievable without cost cuts or revenue growth")

        if goal["notes"]:
            lines.append(f"Notes: {goal['notes']}")

    return "\n".join(lines)


# =============================================================================
# Main tool class
# =============================================================================

class ForecastTool:
    """
    The Forecast Tool the agent calls to run financial projections.

    Usage:
        tool = ForecastTool()
        result = tool.run("runway", business_name="TechSpark SaaS")
        result = tool.run("scenario", business_name="Green Plate Café",
                         cost_change_pct=-20)
    """

    NAME = "forecast_tool"
    DESCRIPTION = """Use this tool to run forward-looking financial projections and scenarios.
Use it for questions about: how long a business can survive, what happens if costs change,
whether financial goals are achievable, and any question requiring future projections.
Forecast types available:
- 'runway': how many months until cash runs out
- 'burn_rate': detailed expense breakdown
- 'scenario': what-if analysis with cost/revenue changes
- 'goals': gap analysis against financial goals
Input: forecast_type and business_name, plus optional parameters for scenarios.
Output: detailed financial projection with risk assessment."""

    def run(
        self,
        forecast_type: str,
        business_name: str,
        cost_change_pct: float = 0,
        revenue_change_pct: float = 0,
    ) -> str:
        """
        Run a financial forecast for a business.

        Args:
            forecast_type: 'runway', 'burn_rate', 'scenario', or 'goals'
            business_name: Name of the business (partial match supported)
            cost_change_pct: For scenario forecasts — % change in costs
            revenue_change_pct: For scenario forecasts — % change in revenue

        Returns:
            Formatted projection results as a string
        """
        logger.info(
            "ForecastTool: type=%s, business=%s", forecast_type, business_name
        )

        # Look up the business
        business = _get_business(business_name)
        if not business:
            return f"Business '{business_name}' not found in the database."

        bid = business["id"]
        bname = business["name"]

        try:
            if forecast_type == "runway":
                return _runway_forecast(bid, bname)
            elif forecast_type == "burn_rate":
                return _burn_rate_analysis(bid, bname)
            elif forecast_type == "scenario":
                return _scenario_forecast(bid, bname, cost_change_pct, revenue_change_pct)
            elif forecast_type == "goals":
                return _goal_gap_analysis(bid, bname)
            else:
                return (
                    f"Unknown forecast type: '{forecast_type}'. "
                    "Choose from: runway, burn_rate, scenario, goals"
                )

        except Exception as e:
            error_msg = f"Forecast tool error: {e}"
            logger.error(error_msg)
            return error_msg
