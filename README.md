financial-cashflow-agent

A flexible SQL + RAG hybrid AI agent that forecasts cash runway and financial health for any type of small business.


What It Does
Most small businesses don't fail because of bad ideas — they fail because they run out of cash before they figure things out. The warning signs are always in the data, but that data sits scattered across transactions, bank statements, and financial documents that nobody has time to read and cross-reference together.
financial-cashflow-agent is an intelligent financial assistant that:

Calculates how long a business can survive at its current burn rate
Identifies what's eating into runway and why
Retrieves relevant financial planning best practices from a curated document library
Runs forward-looking forecasts under different scenarios (cut costs by 20%, grow revenue by 10%, etc.)
Works across any business type — café, bookstore, SaaS startup, freelance studio, funded startup, retail shop, and more

The agent understands that a restaurant and a software startup breathe completely differently financially. It adjusts its reasoning, benchmarks, and recommendations accordingly.

Architecture
This project is built on three layers that work together:
User Question
      │
      ▼
┌─────────────────────────────────────┐
│           ReAct Agent Loop          │  ← Reasons about which tool(s) to use
└──────────┬──────────────────────────┘
           │
     ┌─────┴──────┐──────────────┐
     ▼            ▼              ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ SQL     │  │  RAG    │  │   Forecast   │
│ Tool    │  │  Tool   │  │   Tool       │
└────┬────┘  └────┬────┘  └──────┬───────┘
     │            │              │
     ▼            ▼              ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ SQLite  │  │  FAISS  │  │  Projection  │
│   DB    │  │ Vector  │  │  Calculator  │
│(numbers)│  │ Store   │  │  (forecasts) │
└─────────┘  │ (docs)  │  └──────────────┘
             └─────────┘
SQL Tool — knows the numbers. Every transaction, balance, and trend. Answers "what is happening."
RAG Tool — knows the frameworks. Financial planning benchmarks, cost-cutting playbooks, industry guides. Answers "what should be happening and what to do about it."
Forecast Tool — knows the future. Projects current numbers forward under different assumptions. Answers "where are we heading."
The agent decides which tool(s) to use for each question — and when to combine all three.

Supported Business Types
The system is designed to be flexible. Each business type has its own schema extensions, RAG document segments, and forecasting logic:
Business TypeRevenue PatternKey MetricsRestaurant / CaféDaily cash, seasonalFood cost %, table turnover, wasteRetail / BookstoreFoot traffic, seasonalInventory turnover, marginSaaS / SoftwareMonthly subscriptionsMRR, churn rate, CACFunded StartupInvestor capitalBurn rate, runway to next roundBootstrapped StartupRevenue from day oneNet margin, reinvestment rateFreelance / ConsultingProject-based, lumpyInvoice gap, utilisation rateConstruction / TradesProject-based, delayed paymentsCash gap, WIP

Project Structure
financial-cashflow-agent/
│
├── config/
│   ├── settings.py              # Centralised config — reads from .env
│   └── logging_config.py        # One logging setup used everywhere
│
├── data/
│   ├── db/                      # SQLite database
│   ├── pdfs/                    # Source financial planning documents
│   └── vector_store/            # FAISS index files
│
├── ingest/
│   ├── create_docs.py           # Generate financial planning PDFs
│   ├── chunker.py               # Text chunking strategies
│   ├── embedder.py              # OpenAI embedding wrapper
│   └── vector_store.py          # FAISS build & query
│
├── database/
│   ├── schema.sql               # Core + extension table definitions
│   ├── seed_db.py               # Realistic mock business data
│   └── db.py                    # Connection manager
│
├── tools/
│   ├── sql_tool.py              # Natural language → SQL → results
│   ├── rag_tool.py              # Semantic search over planning documents
│   └── forecast_tool.py         # Burn rate, runway, scenario projections
│
├── agent/
│   ├── agent.py                 # ReAct loop (no LangChain magic)
│   ├── prompt_templates.py      # System prompts and tool descriptions
│   └── memory.py                # Conversation context management
│
├── reports/
│   └── report_generator.py      # Formats agent output into advisor reports
│
├── eval/
│   ├── retrieval_eval.py        # RAG retrieval quality metrics
│   ├── agent_eval.py            # Tool selection accuracy
│   └── forecast_eval.py         # Numerical accuracy validation
│
├── tests/
│   ├── test_sql_tool.py
│   ├── test_rag_tool.py
│   └── test_forecast_tool.py
│
├── main.py                      # Entry point — CLI chat interface
├── requirements.txt             # Pinned dependencies
├── pyproject.toml               # Project metadata and tooling config
├── .env.example                 # Environment variable template
└── README.md

Setup
Prerequisites

Python 3.10+
An OpenAI API key
Git

Installation
bash# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/financial-cashflow-agent.git
cd financial-cashflow-agent

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux

# 5. Add your OpenAI API key to .env

# 6. Seed the database with mock business data
python ingest/seed_db.py

# 7. Build the vector store from financial planning documents
python ingest/create_docs.py
python ingest/ingest_pdfs.py

# 8. Run the agent
python main.py

Environment Variables
Copy .env.example to .env and fill in your values:
bashOPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
DB_PATH=data/db/runway.db
VECTOR_STORE_PATH=data/vector_store/
LOG_LEVEL=INFO
Never commit your .env file. It is listed in .gitignore by default.

Example Queries
> How much runway does Maya's café have at her current burn rate?
> What's eating into Nova Studio's runway the most?
> What would happen to TechSpark's runway if they cut software costs by 30%?
> Which of my clients are at risk of running out of cash in the next 6 months?
> What does financial best practice say about runway for an early-stage startup?
> Compare the burn rates of all businesses in the database and rank by urgency.

Build Roadmap
This project is being built module by module with a focus on understanding the architecture deeply, not just making it work.
ModuleTopicStatus1Project Foundation & Professional Structure In Progress2Data Layer — SQL Schema & Seeding Upcoming3RAG From Scratch — Chunking, Embedding, FAISS Upcoming4Tools Layer — SQL, RAG, Forecast Tools Upcoming5The Agent — ReAct Loop From Scratch Upcoming6Output & Reporting Upcoming7Evaluation & Testing Upcoming

Tech Stack
ComponentTechnologyLanguagePython 3.10+LLMOpenAI GPT-4o-miniEmbeddingsOpenAI text-embedding-3-smallVector StoreFAISS (local, no server needed)DatabaseSQLitePDF ParsingPyMuPDFConfig Managementpython-dotenvCode FormattingBlackLintingFlake8

Design Principles
Flexible by design — the schema, RAG library, and forecasting logic are built to accommodate any business type, not just tech startups.
No magic abstractions — the agent loop, retrieval system, and tool layer are all built from scratch. No LangChain or LlamaIndex. Every line of code is understandable and intentional.
Trustworthy outputs — every forecast is traceable back to the data and documents that produced it. The agent cites its sources.
Built to be evaluated — the system includes a dedicated evaluation layer to measure whether the retrieval is accurate, the agent picks the right tools, and the numbers are correct.

Contributing
This is a learning project built in public. Questions, suggestions, and feedback are welcome via GitHub Issues.

License
MIT
