# AI-Assisted Support Ticket Triage System

An end-to-end pipeline that automatically **classifies**, **prioritizes**, and **drafts grounded responses** for customer support tickets — combining a local LLM with retrieval-augmented generation (RAG) over a real knowledge base, and automatic escalation flagging for high-risk tickets (legal threats, churn risk, angry enterprise customers).

Runs **completely free, offline, and locally** via [Ollama](https://ollama.com) — no API key, no account, no subscription, no usage costs. Anyone can clone this repo and run it end-to-end without paying anything or sending data anywhere.

Built to demonstrate practical AI application in a customer support / technical support analyst context: not a toy chatbot, but a tool modeled on a real support workflow — triage, knowledge lookup, response drafting, and escalation routing.

## Why this project

Support and technical analyst roles increasingly involve evaluating, configuring, and trusting AI-assisted tooling rather than just answering tickets manually. This project shows I can:

- Design a **support ticket triage workflow** end-to-end, not just call an API
- Build **retrieval-augmented generation (RAG)** that grounds AI responses in actual company knowledge instead of letting the model hallucinate policy
- Encode **escalation logic** (legal threats, churn risk, enterprise + high urgency) as explicit, auditable rules rather than a black box
- Write **tested, documented Python** with CI — not just a notebook
- Think about **support operations metrics**: ticket volume by category, urgency distribution, escalation rate
- Make sensible **build choices around cost and data privacy** — a local model means zero ongoing cost and no customer data ever leaves the machine, which matters in a real support tooling context

## How it works

```
data/sample_tickets.json
        │
        ▼
┌───────────────────┐      ┌──────────────────────┐
│  1. Classification │ ──▶ │ category / urgency /  │
│   (local LLM via   │     │ sentiment / escalate?  │
│      Ollama)        │     │                        │
└───────────────────┘      └──────────────────────┘
        │
        ▼
┌───────────────────┐      ┌──────────────────────┐
│ 2. KB Retrieval     │ ──▶ │ relevant policy/FAQ   │
│    (TF-IDF search)  │     │ chunks for grounding   │
└───────────────────┘      └──────────────────────┘
        │
        ▼
┌───────────────────┐
│ 3. Response Draft   │ ──▶ data/processed_tickets.json
│  (local LLM via     │ ──▶ data/report.html (dashboard)
│      Ollama)         │
└───────────────────┘
```

1. **Classification** — each ticket is sent to a local LLM (Llama 3.2, via Ollama) with a structured prompt that returns category, urgency, sentiment, and an escalation flag with a stated reason.
2. **Knowledge base retrieval** — a lightweight TF-IDF + cosine-similarity search (`src/knowledge_base.py`) pulls the most relevant markdown KB articles for the ticket, split into chunks by heading.
3. **Grounded response drafting** — the model drafts a reply using *only* the retrieved KB context, explicitly instructed not to invent policy that isn't in the knowledge base.
4. **Reporting** — a self-contained HTML report summarizes ticket volume, urgency breakdown, category breakdown, and every escalated ticket with its reason.

## Example output

For a ticket like:

> *"This is the third time the export feature has failed silently. I'm an enterprise customer and I have a board meeting in 2 hours... I will need to escalate to my account manager and consider canceling."*

The pipeline produces:

```json
{
  "category": "technical_bug",
  "urgency": "critical",
  "sentiment": "frustrated",
  "escalate": true,
  "escalation_reason": "Enterprise customer with critical urgency and explicit cancellation threat",
  "kb_sources_used": ["technical_issues"],
  "suggested_response": "I completely understand the urgency here, especially with your board meeting coming up. I've flagged this to our team immediately. In the meantime, exports over 50,000 rows use our async export endpoint, which can sometimes resolve silent failures..."
}
```

## Project structure

```
support-ai-triage/
├── data/
│   └── sample_tickets.json      # 10 realistic sample tickets
├── knowledge_base/               # Markdown "company policy" articles used for RAG
│   ├── login_issues.md
│   ├── billing_issues.md
│   ├── technical_issues.md
│   └── account_settings.md
├── src/
│   ├── ai_client.py               # Local LLM client via Ollama (classification + drafting)
│   ├── knowledge_base.py         # TF-IDF retrieval over the KB
│   └── pipeline.py               # Orchestrates the full run + report generation
├── tests/
│   ├── test_knowledge_base.py    # Runs with no API key needed
│   └── test_ai_client.py         # Mocked API calls, runs with no API key needed
├── .github/workflows/ci.yml      # Tests run automatically on every push
├── requirements.txt
└── README.md
```

## Running it yourself

This runs entirely on your own machine, for free, with no account or API key.

**1. Install Ollama** (one-time, free): [ollama.com/download](https://ollama.com/download)

**2. Pull the model** (one-time, ~2GB download, runs on CPU):
```bash
ollama pull llama3.2
```

**3. Clone and run the project:**
```bash
git clone https://github.com/<your-username>/support-ai-triage.git
cd support-ai-triage
pip install -r requirements.txt
python src/pipeline.py
```

Ollama typically starts automatically in the background after install. If the pipeline can't connect, start it manually with `ollama serve` in a separate terminal.

This will process all 10 sample tickets and write:
- `data/processed_tickets.json` — full structured output per ticket
- `data/report.html` — open in a browser for the summary dashboard

### Running tests (fully mocked, no Ollama required)

```bash
pytest tests/ -v
```

All retrieval logic and classification-parsing logic is unit tested independently of any live model calls, using mocked responses — so the test suite runs in CI on every push with zero dependencies beyond Python itself.

## Design decisions worth noting

- **Local model instead of a paid API**: using Ollama means anyone reviewing this repo can run it end-to-end for free, with no signup and no usage limits, and no customer ticket data ever leaves the machine. The `ai_client.py` module is written so the same interface (`classify_ticket`, `draft_response`) could point at a hosted API instead by swapping only the internal `_call_llm()` method — the rest of the pipeline wouldn't need to change.
- **TF-IDF instead of a vector database**: for a KB this size, a full vector DB would be overkill and would add an external dependency that makes the project harder to run for anyone reviewing it. TF-IDF + cosine similarity is transparent, fast, and dependency-light, while still demonstrating real retrieval mechanics rather than just dumping the whole KB into the prompt.
- **Escalation rules are explicit, not just "ask the LLM and trust it"**: the system prompt encodes concrete, auditable escalation criteria (legal language, enterprise + high urgency, explicit churn threats, angry sentiment) so the logic can be reviewed, adjusted, and explained to a team — important for any tool that affects how real customer issues get routed.
- **Responses are grounded, not freeform**: the drafting prompt explicitly forbids inventing policy not present in the retrieved context, and instructs the model to defer to a human specialist when the KB doesn't cover the issue — a deliberate choice to avoid AI-generated promises the company can't keep.
- **Defensive JSON parsing**: smaller local models occasionally wrap structured output in extra commentary. The classifier extracts the first valid `{...}` block rather than assuming the response is clean JSON, and this behavior is explicitly unit tested.

## Possible extensions

- Swap the sample JSON for a live ticket queue (Zendesk/Intercom API)
- Swap the local model for a hosted API (Claude, GPT, etc.) by editing only `_call_llm()` in `ai_client.py` — useful if higher classification accuracy is needed at production scale
- Add a feedback loop where agent edits to drafts are logged and used to refine prompts
- Track escalation precision/recall against human-labeled ground truth over time

## Tech stack

`Python` · `Ollama (local LLM)` · `Llama 3.2` · `scikit-learn (TF-IDF / RAG retrieval)` · `pytest` · `GitHub Actions CI`
