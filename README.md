# Automated Outreach Pipeline

One seed domain in, four stages fire on their own, personalized cold emails go out. No human touches the data between stages — the only manual steps are the seed domain at the start and a single confirmation before any email is sent.

```
domain → Ocean.io → Prospeo → Eazyreach → Brevo → emails sent
         lookalike   decision-  verified    send
         companies   makers     emails
```

## Pipeline Stages

| Stage | Tool | In → Out |
|-------|------|----------|
| 1 | Ocean.io | seed domain → similar company domains |
| 2 | Prospeo | company domain → decision-makers + LinkedIn URLs |
| 3 | Eazyreach | LinkedIn URL → verified work email |
| 4 | Brevo | verified contact → personalized email sent |

## Features

- **End-to-end automation**: One domain in, all four stages fire
- **Resilient to messy data**: Missing contacts, rate limits, partial failures don't crash the run
- **Safety checkpoint**: Summary shown before emails fire, requires explicit confirmation
- **Mock mode**: Test the entire pipeline without API calls
- **Dry-run mode**: Real API lookups but no emails sent
- **Rate limit handling**: Automatic retry with exponential backoff on 429s and 5xx errors
- **De-duplication**: Removes duplicate contacts before sending

## Project Layout

```
outreach-pipeline/
├── pyproject.toml              # packaging, deps, console entry point
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── outreach_pipeline/
│       ├── __init__.py
│       ├── __main__.py         # `python -m outreach_pipeline`
│       ├── cli.py              # argument parsing + entry point
│       ├── config.py           # API keys from .env, default limits
│       ├── models.py           # Company, Contact (the data contract)
│       ├── http_client.py      # shared request helper: retries, 429 backoff
│       ├── checkpoint.py       # summary + confirm before sending
│       ├── pipeline.py         # orchestration + de-duplication
│       ├── stages/
│       │   ├── ocean.py        # Stage 1: lookalike companies
│       │   ├── prospeo.py      # Stage 2: decision-makers
│       │   ├── eazyreach.py    # Stage 3: verified emails
│       │   └── brevo.py        # Stage 4: send outreach
│       └── templates/
│           └── outreach.txt    # your email copy
└── tests/
    ├── test_models.py
    ├── test_checkpoint.py
    └── test_pipeline.py
```

## Setup

### Prerequisites

1. **Get a domain first** — Ocean.io needs a company email to sign up
   - Free via GitHub Student Developer Pack, or buy cheapest on Namecheap
2. **Create a company email** on that domain (`you@yourdomain`)
3. **Sign up for Ocean.io** using that company email
4. **Create accounts** for Prospeo, Eazyreach, and Brevo

### Installation

```bash
cd outreach-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # installs the package + test deps
```

This gives you an `outreach` command on your PATH.

### Configuration

```bash
cp .env.example .env
# Edit .env and paste in your real API keys + sender identity
```

**Important**: In Brevo, make sure `SENDER_EMAIL` is a **verified sender**, or sends will fail.

## Usage

### Mock Mode (Safe Testing)

Start in mock mode to watch the whole pipeline with zero real API calls:

```bash
outreach example.com --mock --dry-run
# or without installing:
PYTHONPATH=src python -m outreach_pipeline example.com --mock --dry-run
```

### Real Runs

```bash
outreach stripe.com --dry-run     # real lookups, stops before sending
outreach stripe.com               # real run; shows summary, asks to confirm
outreach stripe.com --yes         # real run; skip confirmation (non-interactive)
```

### CLI Flags

| Flag | What it does |
|------|--------------|
| `--mock` | Use sample data instead of real API calls |
| `--dry-run` | Run every stage except the actual send |
| `--yes` | Skip the confirmation prompt (non-interactive) |
| `--max-companies N` | Override the lookalike-company limit |
| `--max-contacts N` | Override contacts-per-company limit |
| `--verbose` | Debug logging |

## Testing

```bash
pytest                  # run all tests
pytest -v               # verbose output
pytest --cov            # with coverage report
```

## API Integration Details

### Stage 1: Ocean.io
- **Endpoint**: `POST https://api.ocean.io/v1/companies/similar`
- **Auth**: Bearer token in Authorization header
- **Purpose**: Find lookalike companies from a seed domain

### Stage 2: Prospeo
- **Endpoint**: `POST https://api.prospeo.io/domain-search`
- **Auth**: API key in X-KEY header
- **Purpose**: Find C-suite/VP decision-makers with LinkedIn URLs

### Stage 3: Eazyreach
- **Endpoint**: `POST https://api.eazyreach.app/v1/resolve`
- **Auth**: Bearer token in Authorization header
- **Purpose**: Resolve LinkedIn URLs to verified work emails

### Stage 4: Brevo
- **Endpoint**: `POST https://api.brevo.com/v3/smtp/email`
- **Auth**: API key in api-key header
- **Purpose**: Send personalized transactional emails

## Customizing Email Copy

Edit `src/outreach_pipeline/templates/outreach.txt` to customize your outreach message.

Available placeholders:
- `{first_name}` — Contact's first name
- `{full_name}` — Contact's full name
- `{title}` — Contact's job title
- `{company}` — Company name

## Error Handling

The pipeline is designed to be resilient:
- **Per-item try/except**: A bad company or unresolvable contact is skipped, not fatal
- **Rate limit handling**: Automatic retry with exponential backoff on HTTP 429
- **Server errors**: Automatic retry on 5xx responses
- **Graceful degradation**: Missing LinkedIn URLs are skipped, unverified emails aren't sent

## License

MIT
