"""
ingest/create_docs.py

Generates realistic financial planning documents as text files
that will be converted to PDFs and embedded into the vector store.

Why we generate our own documents instead of downloading real ones:
- We can craft content that maps perfectly to our 5 mock businesses
- We can include specific benchmarks the agent will cite
- We control the structure so chunking works optimally
- No copyright concerns

Document library structure:
    data/pdfs/
    ├── general/
    │   ├── cash_flow_fundamentals.txt
    │   ├── runway_planning_guide.txt
    │   └── financial_health_benchmarks.txt
    ├── restaurant/
    │   ├── restaurant_financial_guide.txt
    │   └── food_cost_management.txt
    ├── retail/
    │   └── retail_cash_flow_guide.txt
    ├── saas/
    │   └── saas_metrics_guide.txt
    ├── funded_startup/
    │   └── startup_runway_guide.txt
    └── freelance/
        └── freelance_cash_flow_guide.txt

Run this script directly:
    python ingest/create_docs.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.logging_config import setup_logging

logger = logging.getLogger(__name__)


# =============================================================================
# Document content
# Each document is written to be chunked well:
# - Clear section headers
# - Self-contained paragraphs
# - Specific numbers and benchmarks the agent can cite
# =============================================================================

DOCUMENTS = {

    # -------------------------------------------------------------------------
    # GENERAL — applies to all business types
    # -------------------------------------------------------------------------

    "general/cash_flow_fundamentals.txt": """
CASH FLOW FUNDAMENTALS FOR SMALL BUSINESSES

Understanding Cash Flow vs Profit

Many small business owners confuse profit with cash flow. A business can be profitable on paper and still run out of cash. Profit is an accounting concept that includes non-cash items like depreciation and accruals. Cash flow is the actual movement of money in and out of your bank account. A business survives on cash, not profit.

The three types of cash flow every business owner must understand are operating cash flow, investing cash flow, and financing cash flow. Operating cash flow is the cash generated from normal business operations — selling products or services and paying the costs to deliver them. This is the most important number for day-to-day survival. Investing cash flow covers purchases of equipment, property, or other long-term assets. Financing cash flow includes loans taken, loans repaid, and any investment received.

What is Burn Rate?

Burn rate is the speed at which a business spends its cash reserves. It is calculated as total monthly expenses minus total monthly revenue. If a business spends $30,000 per month and earns $18,000 per month, its net burn rate is $12,000 per month. Gross burn rate refers to total monthly spending regardless of revenue, which is $30,000 in this example.

Burn rate is the single most important number for any business operating without consistent profit. It tells you how fast you are consuming your financial cushion.

What is Cash Runway?

Cash runway is the number of months a business can continue operating at its current burn rate before running out of money. It is calculated by dividing current cash reserves by monthly net burn rate.

Formula: Runway (months) = Total Cash Available / Monthly Net Burn Rate

Example: If a business has $120,000 in the bank and burns $15,000 per month net, its runway is 8 months.

Why Runway is a Critical Early Warning Metric

Most businesses that fail do not fail suddenly. They fail slowly, running out of cash after months of warning signs that were not acted upon in time. Runway gives you the time horizon within which you must either increase revenue, reduce costs, or secure additional funding. Financial advisors recommend reviewing runway monthly, not quarterly.

The 12-Month Rule

Financial planning best practice recommends that established businesses maintain a minimum of 3 to 6 months of operating expenses in readily accessible cash reserves. For early-stage businesses and startups, the recommended minimum is 12 to 18 months of runway at all times. This buffer exists to absorb unexpected revenue drops, economic downturns, or one-time large expenses.

Businesses operating with less than 3 months of runway are considered in the danger zone and should take immediate corrective action. Businesses with 1 to 2 months of runway face existential risk.

Operating Cash Flow Cycle

Every business has a cash conversion cycle — the time between spending cash on inputs and receiving cash from customers. A restaurant buys ingredients today and receives cash from customers the same day, giving it a very short cash cycle. A construction company may spend on materials and labour for months before invoicing a client, creating a very long and stressful cash cycle. Understanding your cash cycle is essential for predicting when cash gaps will occur.

Working Capital Management

Working capital is the difference between current assets (cash, inventory, receivables) and current liabilities (payables, short-term debt). Positive working capital means you have enough short-term assets to cover short-term obligations. Negative working capital is a serious warning sign even for profitable businesses. Effective working capital management means collecting receivables quickly, paying suppliers as late as allowed, and keeping inventory lean.
""",

    "general/runway_planning_guide.txt": """
RUNWAY PLANNING GUIDE: HOW TO EXTEND YOUR BUSINESS SURVIVAL HORIZON

The Two Levers of Runway

Every business has exactly two levers to extend its runway: increase cash inflows or decrease cash outflows. While this sounds obvious, most business owners focus exclusively on growing revenue and neglect the faster and more reliable lever of cost reduction. A 10% reduction in monthly costs typically extends runway by more than a 10% increase in revenue because cost reductions are immediate and certain while revenue growth is delayed and uncertain.

Lever 1: Reducing Cash Outflows

Fixed costs are expenses that remain constant regardless of revenue. These include rent, insurance, minimum staffing, and software subscriptions. Variable costs scale with revenue or activity. Reducing fixed costs has a permanent compounding effect on runway because the savings repeat every single month.

Priority order for cost reduction in a cash crisis:
First, identify all software subscriptions and cancel or downgrade anything not directly generating revenue. Most businesses discover they are paying for 3 to 5 tools they barely use. Second, review all service contracts and renegotiate payment terms where possible. Many vendors prefer reduced payments over losing a customer entirely. Third, assess staffing levels honestly. Payroll is typically the largest cost driver and the hardest conversation, but delaying difficult staffing decisions often leads to the business failing entirely rather than surviving leaner.

Common benchmarks for cost as a percentage of revenue:
Rent should not exceed 10% of revenue for most business types. Payroll should not exceed 30% to 40% of revenue for service businesses and 20% to 25% for product businesses. Marketing should be 5% to 15% of revenue depending on the growth stage. Software and tools should not exceed 5% to 8% of revenue.

Lever 2: Increasing Cash Inflows

Revenue growth is the preferred long-term lever but it is slower and less certain than cost reduction. For businesses in a cash crisis, the fastest paths to additional cash inflows are collecting outstanding receivables immediately, asking existing customers to prepay for future services at a discount, introducing a lower-priced offering to capture budget-conscious customers, and pursuing one large contract or project that can inject meaningful cash quickly.

Scenario Planning for Runway

Every business should model three scenarios monthly: a base case using current trends, a downside case assuming revenue drops 20%, and an upside case assuming revenue grows 15%. Runway in the downside case tells you your true safety margin. If your downside runway is less than 6 months, you are more fragile than you think.

When to Seek External Funding

External funding — whether a loan, line of credit, or investment — should be pursued before you need it, not after. Lenders and investors respond poorly to desperation. The optimal time to raise funding is when you have 9 to 12 months of runway remaining and positive business momentum. Approaching funders with 2 months of runway dramatically reduces your negotiating position and approval odds.

Emergency Funding Options for Small Businesses

When runway drops below 3 months and revenue growth is insufficient to close the gap, emergency funding options include SBA emergency loans which typically take 2 to 4 weeks to process, business lines of credit which require existing banking relationships, invoice factoring which converts outstanding receivables to immediate cash at a discount of 2% to 5%, and revenue-based financing which provides upfront capital in exchange for a percentage of future monthly revenue until the advance is repaid.
""",

    "general/financial_health_benchmarks.txt": """
SMALL BUSINESS FINANCIAL HEALTH BENCHMARKS

Industry-Validated Financial Ratios

Financial health benchmarks provide context for raw numbers. A $10,000 monthly profit means something very different for a business with $50,000 in monthly revenue versus one with $500,000. Ratios allow meaningful comparison across businesses of different sizes.

Current Ratio

The current ratio measures short-term financial health. It is calculated as current assets divided by current liabilities. A ratio above 1.5 is considered healthy for most small businesses. A ratio below 1.0 means the business cannot cover its short-term obligations with its short-term assets — a serious warning sign. Industry variation is significant: retailers often operate with current ratios as low as 1.2 due to fast inventory turnover, while service businesses should maintain ratios above 2.0.

Gross Profit Margin

Gross profit margin is calculated as revenue minus cost of goods sold, divided by revenue. Benchmarks vary significantly by industry. Restaurants typically achieve gross margins of 60% to 70% on food sales but net margins of only 3% to 9% after all expenses. Retail businesses typically achieve gross margins of 40% to 60%. Software and SaaS businesses can achieve gross margins of 70% to 85% because their cost of goods sold is primarily hosting and support. Service businesses typically achieve gross margins of 50% to 70%.

Net Profit Margin

Net profit margin is what remains after all expenses including taxes. Healthy benchmarks by sector: restaurants 3% to 9%, retail 2% to 6%, SaaS and software 10% to 25% at scale, freelance and consulting 20% to 35%, healthcare 5% to 10%.

Cash Reserve Benchmarks by Business Type

Research from the JPMorgan Chase Institute analysing 600,000 small businesses found the following median cash buffer days by industry: restaurants hold a median of 16 days of cash, retail businesses hold 19 days, service businesses hold 23 days, and professional services firms hold 32 days. The research found that 25% of small businesses hold fewer than 13 days of cash, meaning one bad month could be fatal.

Financial advisors recommend targeting significantly higher buffers than the median: 60 to 90 days for restaurants given their high sensitivity to external shocks, 45 to 60 days for retail, 90 days for service businesses, and 180 days or more for early-stage startups and funded companies.

Revenue Concentration Risk

Businesses that derive more than 25% of their revenue from a single customer or source face significant concentration risk. If that customer leaves or that revenue source dries up, the business loses more than a quarter of its income immediately. Financial advisors recommend no single customer should represent more than 15% to 20% of total revenue for a healthy business.

Debt Service Coverage Ratio

The debt service coverage ratio measures a business's ability to cover its debt obligations from operating income. It is calculated as net operating income divided by total debt service (principal plus interest payments). A ratio of 1.25 or above is generally required by lenders. A ratio below 1.0 means the business cannot service its debt from operations and is at serious risk of default.
""",

    # -------------------------------------------------------------------------
    # RESTAURANT
    # -------------------------------------------------------------------------

    "restaurant/restaurant_financial_guide.txt": """
RESTAURANT AND CAFÉ FINANCIAL MANAGEMENT GUIDE

The Economics of Food Service

The restaurant industry operates on fundamentally different economics from most other small businesses. High revenue numbers can be deeply misleading because the costs of delivering that revenue — food, labour, and rent — are extremely high and leave very thin margins for error.

The Prime Cost Rule

Prime cost is the combination of cost of goods sold (food and beverage costs) and total labour costs. It is the single most important number in restaurant finance. Industry best practice is to keep prime cost below 60% of total revenue. Restaurants with prime cost above 65% consistently struggle to survive even with strong revenue. Restaurants achieving prime cost below 55% are typically high performers.

Example: A café with $40,000 monthly revenue should target food costs of no more than $13,000 (32.5%) and labour of no more than $11,000 (27.5%) for a combined prime cost of $24,000 or 60%.

Food Cost Percentage Benchmarks

Food cost percentage is calculated as cost of food purchased divided by food revenue. Industry benchmarks by category: full-service restaurants 28% to 35%, quick service and fast casual 25% to 31%, cafés and coffee shops 25% to 35%, plant-based and specialty restaurants 30% to 38%. Food cost consistently above 40% indicates either poor purchasing practices, excessive waste, portion inconsistency, or menu pricing that is too low.

Labour Cost Benchmarks

Labour cost as a percentage of revenue: full-service restaurants 30% to 35%, quick service restaurants 25% to 30%, cafés 28% to 35%. Labour is the most controllable cost in a restaurant because scheduling can be adjusted weekly. However, cutting labour too aggressively leads to poor service quality and lost revenue.

The 10% Net Margin Target

A well-run restaurant achieving average performance should target a net profit margin of 6% to 9%. High-performing restaurants achieve 10% to 15%. Any restaurant consistently below 3% net margin is one bad month away from a cash crisis. The industry median is approximately 3% to 5%, which is why cash reserves are critical — there is very little room for error.

Seasonal Cash Flow Management for Restaurants

Most restaurants experience significant seasonal revenue variation. Summer months typically generate 20% to 40% more revenue than winter months for casual dining establishments. Holiday periods drive spikes that can represent 150% to 200% of average monthly revenue. Restaurants must build cash reserves during peak periods to survive slow seasons. A café that does not accumulate 2 to 3 months of operating expenses during its summer peak will struggle in winter.

Managing Cash Flow Gaps

The most common cash flow crisis for restaurants occurs when a slow month coincides with a large irregular expense such as equipment repair, a health inspection fine, or a lease renewal deposit. Restaurants should maintain an emergency reserve specifically for these events, separate from operating cash. The recommended emergency reserve is 1 to 2 months of fixed costs.

Inventory Management and Waste

Food waste is a direct cash drain. Industry studies suggest that restaurants waste 4% to 10% of all food purchased. Reducing waste from 8% to 4% on a $12,000 monthly food cost saves $480 per month or $5,760 per year — the equivalent of adding a significant catering contract. Waste reduction begins with accurate inventory tracking, standardised portions, and FIFO (first in, first out) stock rotation.
""",

    "restaurant/food_cost_management.txt": """
FOOD COST CONTROL AND CASH FLOW OPTIMISATION FOR CAFÉS AND RESTAURANTS

Why Food Cost Management is Cash Flow Management

Every dollar saved on food cost is a dollar directly added to cash flow. Unlike revenue growth which requires attracting new customers, food cost reduction happens immediately and compounds monthly. A café reducing food cost from 36% to 32% of revenue on $40,000 monthly revenue saves $1,600 per month, extending cash runway by 1.6 months per year.

The Four Drivers of High Food Cost

Purchasing inefficiency occurs when businesses buy more than they need, pay above-market prices, or fail to negotiate volume discounts with suppliers. Over-ordering is the most common cause of high food cost in small cafés. Implementing a weekly par-level system — ordering only what is needed to bring stock back to a predetermined level — typically reduces food purchases by 8% to 12%.

Portion inconsistency means that the same menu item uses different amounts of ingredients depending on who is preparing it. Standardised recipes with gram-level measurements for key ingredients are the most effective tool against this. Restaurants implementing formal portion control typically see food cost drop by 2 to 4 percentage points.

Menu pricing misalignment occurs when menu prices do not reflect the actual cost of ingredients. Each menu item should be individually costed and priced to achieve the target food cost percentage. Items that cannot be priced appropriately for the market should be removed from the menu. A menu engineering review should be conducted quarterly.

Theft and spoilage are underestimated contributors to food cost. Industry estimates suggest that employee theft and spoilage together account for 3% to 7% of food cost in restaurants that do not have formal controls. Regular inventory counts, portion monitoring, and end-of-day waste logs are the primary controls.

Supplier Negotiation Strategies

Small cafés and restaurants often accept supplier pricing without negotiation. However, even small operations have negotiating leverage. Consolidating purchases with fewer suppliers typically yields 3% to 8% discounts in exchange for volume commitment. Paying invoices early (within 10 days rather than 30) often qualifies for 2% early payment discounts. Forming purchasing cooperatives with nearby non-competing restaurants to negotiate collective volume pricing has shown savings of 5% to 15% on key commodities.

Cash Flow Timing for Food Businesses

Supplier payment terms significantly affect cash flow. Standard terms in the food industry are net 30, meaning payment is due 30 days after delivery. Negotiating net 45 or net 60 terms on dry goods and non-perishables while taking advantage of early payment discounts on perishables is an effective cash management strategy. A café with $10,000 monthly in food purchases operating on net 30 terms has $10,000 of cash tied up in supplier credit at any given time. Extending to net 45 effectively frees up additional operating capital.
""",

    # -------------------------------------------------------------------------
    # RETAIL
    # -------------------------------------------------------------------------

    "retail/retail_cash_flow_guide.txt": """
RETAIL BUSINESS CASH FLOW AND INVENTORY MANAGEMENT GUIDE

The Unique Cash Flow Challenge of Retail

Retail businesses face a cash flow challenge that most other business types do not: cash is tied up in inventory before it is converted back into cash through sales. This creates a structural delay between spending money and receiving it back. Managing this cycle efficiently is the difference between a retail business that grows and one that slowly strangles itself with excess stock.

Inventory as Frozen Cash

Every unit of unsold inventory represents cash that cannot be used for rent, salaries, or emergency expenses. A bookstore with $80,000 in inventory on the shelves has $80,000 of frozen cash. If that inventory takes 6 months to sell, the store effectively has a 6-month cash gap between spending and earning.

The Inventory Turnover Ratio

Inventory turnover measures how many times a business sells and replaces its inventory in a year. It is calculated as cost of goods sold divided by average inventory value. Industry benchmarks: independent bookstores 2 to 4 times per year, general retail 4 to 6 times per year, fashion retail 4 to 8 times per year, grocery 12 to 20 times per year. Low turnover means cash is tied up too long. A bookstore achieving 2 turns per year holds each book on average for 6 months before selling it.

Days Inventory Outstanding

Days inventory outstanding measures the average number of days inventory is held before being sold. It is calculated as 365 divided by inventory turnover. A bookstore with 3 turns per year holds inventory for an average of 122 days. Reducing days inventory outstanding from 120 to 90 days by managing purchasing more tightly frees up significant working capital.

Seasonal Inventory Planning

Retail businesses typically experience dramatic seasonal revenue variation. Independent bookstores achieve 25% to 35% of their annual revenue in November and December alone. Purchasing too much inventory for a seasonal peak that underperforms is one of the most common causes of retail cash crises. Best practice is to maintain conservative base inventory levels and use rapid reorder capabilities for bestsellers rather than overstocking in anticipation.

Managing the Retail Cash Gap

The most dangerous period for retail cash flow is immediately after a major inventory purchase and before the corresponding sales revenue arrives. Retail businesses should time large inventory purchases to coincide with their strongest revenue periods, not their slowest. Consignment arrangements, where inventory is only paid for after it is sold, are available from some suppliers and eliminate the cash gap entirely for those products.

Gross Margin Benchmarks for Retail

Gross margin is the difference between the selling price and the cost of the product, expressed as a percentage of selling price. Benchmarks by category: independent bookstores 40% to 45%, gift and specialty retail 50% to 60%, clothing and apparel 50% to 65%, electronics 15% to 25%. Independent retailers competing with Amazon and large chains on commoditised products like books must compensate with community, curation, and events revenue to achieve viable margins.

Strategies for Independent Retailers Competing with Online Giants

Independent retailers cannot compete on price against Amazon and large chains. The businesses that survive focus on three advantages: expertise and curation that algorithms cannot replicate, community and in-store experience that creates customer loyalty, and local uniqueness that makes the store a destination. Financially, this translates to higher gross margins on curated selections and events revenue that carries no cost of goods sold. A bookstore generating 15% of revenue from ticketed events and author appearances achieves significantly better cash flow than one relying entirely on book sales.
""",

    # -------------------------------------------------------------------------
    # SAAS
    # -------------------------------------------------------------------------

    "saas/saas_metrics_guide.txt": """
SAAS FINANCIAL METRICS AND RUNWAY MANAGEMENT GUIDE

Why SaaS Businesses Are Financially Different

Software as a Service businesses operate on fundamentally different financial dynamics from traditional businesses. Revenue is recurring and predictable, costs are front-loaded, and the path to profitability requires sustained investment in growth before the economics improve. Understanding SaaS-specific metrics is essential for anyone advising these businesses.

Monthly Recurring Revenue (MRR)

Monthly Recurring Revenue is the normalised monthly revenue from all active subscriptions. It excludes one-time fees and non-recurring revenue. MRR is the most important top-line metric for any SaaS business. Growth in MRR directly extends runway by reducing net burn rate.

MRR is calculated as the sum of all active subscriber counts multiplied by their respective monthly plan prices. A SaaS business with 180 customers on a $29 plan, 94 customers on a $79 plan, and 12 customers on a $299 plan has MRR of: (180 × $29) + (94 × $79) + (12 × $299) = $5,220 + $7,426 + $3,588 = $16,234.

Churn Rate and Its Impact on Runway

Monthly churn rate is the percentage of subscribers who cancel in a given month. It is the most dangerous metric in SaaS because it silently erodes revenue growth. A business adding 20 new customers per month but churning 15% of existing customers may appear to be growing while actually deteriorating.

Churn rate benchmarks: below 2% monthly is excellent, 2% to 5% is acceptable for early-stage, above 5% monthly indicates serious product-market fit problems and will eventually prevent the business from growing. A 5% monthly churn rate means a customer is retained for an average of only 20 months before cancelling.

The relationship between churn and runway is critical: a SaaS company with $15,000 MRR and 5% monthly churn is losing $750 of revenue per month before adding new customers. If acquisition is flat, revenue declines every month and runway shrinks faster than the bank balance suggests.

Customer Acquisition Cost (CAC) and Payback Period

Customer Acquisition Cost is the total sales and marketing spend divided by the number of new customers acquired. If a SaaS business spends $8,000 on marketing in a month and acquires 20 new customers, CAC is $400.

CAC Payback Period is how many months of subscription revenue it takes to recover the cost of acquiring a customer. At $29 per month per customer, a $400 CAC takes 13.8 months to recover. Benchmarks: under 12 months is healthy, 12 to 18 months is acceptable for venture-backed companies with strong growth, over 18 months is concerning for bootstrapped businesses.

Default Alive vs Default Dead

A concept from Y Combinator: a startup is "default alive" if its current revenue growth trajectory means it will reach profitability before running out of money, assuming costs stay constant. It is "default dead" if it will run out of money before reaching profitability without raising additional funds.

Calculating default alive status requires projecting MRR growth forward at the current growth rate and comparing the projected break-even date to the current runway end date. A company with $14,000 MRR growing at $800 per month and $26,000 monthly burn will reach $26,000 MRR (break-even) in approximately 15 months. If the current runway is 12 months, the company is default dead by 3 months and must either grow faster, cut costs, or raise capital.

SaaS Runway Extension Strategies

For pre-revenue or early-revenue SaaS businesses, the fastest ways to extend runway without fundraising are: annual prepayment discounts where customers pay 12 months upfront at a 15% to 20% discount, which immediately injects cash equivalent to 10 to 11 months of revenue; enterprise upfront contracts where large customers pay significant implementation fees in addition to recurring subscription; and freemium to paid conversion optimisation, where improving the conversion rate from free to paid by even 1% can meaningfully increase MRR.

Cost control in SaaS is primarily about infrastructure and people. Cloud infrastructure costs should scale proportionally with revenue — a SaaS business spending more than 15% of revenue on cloud infrastructure is likely over-provisioned. People costs typically represent 60% to 80% of total SaaS expenses and should only scale ahead of revenue when there is high confidence in near-term revenue growth.

Series A Readiness Benchmarks

For SaaS startups seeking Series A funding, investors typically look for: MRR of $100,000 or greater (approximately $1.2M ARR), monthly churn below 3%, month-over-month MRR growth of 10% to 15% consistently for 6 months, gross margin above 65%, and a clear path to $10M ARR. Startups should begin Series A preparation when they have 9 to 12 months of runway remaining.
""",

    # -------------------------------------------------------------------------
    # FUNDED STARTUP
    # -------------------------------------------------------------------------

    "funded_startup/startup_runway_guide.txt": """
FUNDED STARTUP RUNWAY MANAGEMENT AND INVESTOR RELATIONS GUIDE

The Unique Financial Reality of Funded Startups

Funded startups operate in a fundamentally different financial reality from bootstrapped businesses. They have deliberately raised capital to invest ahead of revenue, accepting losses today in exchange for faster growth. This makes runway management both more important and more complex than for revenue-generating businesses. Running out of money before the next funding round is an existential event that standard business recovery options cannot prevent.

Understanding Your Burn Rate as a Funded Startup

Gross burn rate for funded startups is typically dominated by two categories: people and infrastructure. People costs — salaries, benefits, recruiting fees — typically represent 70% to 85% of total monthly expenses. Infrastructure costs, primarily cloud computing, represent most of the remainder. This concentration means that meaningful burn rate reduction almost always requires difficult headcount decisions.

Net burn rate accounts for any revenue the startup is generating. Pre-revenue startups have net burn equal to gross burn. Startups beginning to generate revenue should track both numbers carefully as net burn is what actually depletes the bank account.

The 18-Month Rule for Funded Startups

The gold standard in venture-backed startup finance is to maintain 18 months of runway at all times. This provides sufficient time to: achieve the milestones required for the next funding round (typically 12 months of work), run a fundraising process (typically 3 to 6 months), and maintain a buffer for the fundraising process taking longer than expected.

Startups with less than 12 months of runway should consider fundraising immediately. Startups with less than 6 months of runway are in crisis and face severely reduced negotiating leverage with investors.

Milestone-Based Runway Planning

Investors fund milestones, not time. The purpose of a funding round is to achieve the specific milestones that justify the next funding round at a higher valuation. Runway planning must therefore be tied to milestone achievement, not just calendar time.

For pre-seed to seed transitions, typical milestones include: building a working prototype, demonstrating initial user traction, and identifying a clear go-to-market strategy. For seed to Series A, milestones typically include: product-market fit evidence, consistent MRR growth, strong retention metrics, and a clear unit economics story.

If current burn rate will exhaust funds before milestones are achieved, there are three options: reduce burn rate to extend runway to the milestone, accelerate milestone achievement with current resources, or raise a bridge round to extend runway. Bridge rounds carry dilution costs and signal potential problems to new investors, so reducing burn is typically the preferred first option.

Investor Reporting and Transparency

Funded startups are obligated to keep investors informed about financial health, particularly runway. Monthly updates to investors should include current cash balance, monthly burn rate, current runway in months, key metrics progress against milestones, and any significant changes to financial projections.

Proactive communication about runway concerns demonstrates management maturity and gives investors the opportunity to help — through bridge financing, introductions to other investors, or operational advice. Surprising investors with a runway crisis is one of the most damaging things a founder can do to the relationship.

Down Round Risk and Runway Management

A down round is a funding round where the company is valued lower than in the previous round. Down rounds occur when a startup has not achieved sufficient progress to justify a higher valuation, often because it ran low on runway and was forced to raise on unfavourable terms. Down rounds are deeply dilutive to founders and early employees and signal problems to the market.

The best protection against a down round is aggressive runway management: maintaining 18 months of runway, achieving milestones on schedule, and beginning fundraising early with strong metrics. Startups that run tight on runway typically raise at flat or down valuations even if their underlying business progress is good, simply because of the negotiating disadvantage of needing cash urgently.
""",

    # -------------------------------------------------------------------------
    # FREELANCE
    # -------------------------------------------------------------------------

    "freelance/freelance_cash_flow_guide.txt": """
FREELANCE AND INDEPENDENT STUDIO CASH FLOW MANAGEMENT GUIDE

The Feast and Famine Problem

Freelancers and independent studios face a structural cash flow problem that traditional employment insulates people from: income is lumpy, irregular, and unpredictable while expenses are smooth, monthly, and relentless. A freelance designer might earn $25,000 in one month and $0 the following month while rent, software, and contractor costs continue unchanged.

Understanding the feast and famine cycle is the starting point for solving it. The cycle typically works as follows: a freelancer completes several projects simultaneously and receives multiple payments at once (feast), then finishes those projects, spends time pursuing new work, and has a period with no income (famine). Without cash reserves, the famine period creates genuine financial stress even for freelancers with strong average annual income.

The Project Cash Flow Timeline

Most project-based businesses do not receive payment at the time they do the work. The typical cash flow timeline for a freelance project is: proposal and negotiation (0 income, 0 work), 25% to 50% deposit on contract signing (income, no significant work done yet), work delivery phase (significant work, limited income), milestone payment on approval (income, work done), final payment on completion (income, work complete), and sometimes a 30 to 60 day wait after invoicing before payment arrives.

The gap between starting work and receiving final payment can easily be 2 to 4 months for a medium-sized project. During this time, the freelancer is funding the work themselves. Managing multiple projects at different stages of this cycle smooths cash flow significantly.

The 30% Tax Reserve Rule

Self-employed income is subject to income tax and self-employment tax. Unlike employed individuals whose tax is withheld automatically, freelancers must manage their own tax liability. The standard recommendation is to immediately transfer 25% to 30% of every payment received into a dedicated tax reserve account that is never touched for operating expenses. Failing to maintain this reserve leads to a painful cash crisis at tax time.

Building a Cash Buffer: The Target Number

Freelancers should target a cash buffer equal to 3 months of total personal and business expenses combined. This covers the income gap during slow periods and provides stability during project transitions. For a freelancer with $12,000 in monthly combined expenses, the target buffer is $36,000. Until this buffer is established, financial stress during slow periods is structurally inevitable rather than a sign of business failure.

Retainer Contracts as a Structural Solution

The most effective long-term solution to freelance cash flow volatility is establishing retainer relationships with clients. A retainer is a monthly fixed fee paid in advance in exchange for a guaranteed amount of the freelancer's time or output. Even one retainer client representing $3,000 to $5,000 per month provides an income floor that dramatically reduces cash flow stress.

Freelancers seeking retainer clients should look for: businesses with ongoing needs in their specialty rather than one-off projects, clients they have already delivered value to who trust their work, and businesses large enough that a retainer fee is a small line item rather than a major budget decision.

Invoice Terms and Collection Practices

Standard invoice terms for freelancers and creative studios are net 14 to net 30. Offering a 2% to 3% discount for payment within 5 to 7 days can accelerate collections significantly from clients who care about discounts. Charging late payment fees of 1.5% to 2% per month on overdue invoices discourages slow payment from clients who do not respond to standard reminders.

For new clients, requiring a 50% upfront deposit is standard practice and should be presented as policy rather than a negotiating point. For established clients with a good payment history, 25% deposits are more common. Never begin significant work without a deposit — it creates cash flow risk and reduces the client's urgency to prioritise the project.

Expense Management for Lean Operations

Freelance studios with lean cost structures survive slow periods that would destroy higher-cost businesses. Target monthly overhead of no more than 30% to 40% of average monthly revenue. Key areas where freelancers overspend relative to their revenue include: co-working spaces that could be replaced with a home office, software subscriptions that are used occasionally but billed monthly, and contractor costs for work that could be declined or deferred during slow periods.
"""
}


# =============================================================================
# File creation
# =============================================================================

def create_documents() -> None:
    """Write all documents to the data/pdfs directory."""
    setup_logging(log_level=settings.LOG_LEVEL)

    pdf_dir = settings.PDF_DIR
    pdf_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for relative_path, content in DOCUMENTS.items():
        full_path = pdf_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.strip(), encoding="utf-8")
        logger.debug("Created: %s", full_path)
        created += 1

    print(f"\n=== Documents Created ===")
    print(f"  {created} documents written to {pdf_dir}")
    for path in sorted(pdf_dir.rglob("*.txt")):
        size = path.stat().st_size
        print(f"  {path.relative_to(pdf_dir):<55} {size:>6} bytes")
    print("=" * 30)
    print("\n✅ Documents ready for embedding.\n")


if __name__ == "__main__":
    create_documents()
