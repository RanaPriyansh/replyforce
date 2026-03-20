ReplyForce v0.1
================

AI-powered Google Review responder for multi-location businesses.

Quick Start
-----------

    pip install -r requirements.txt
    python main.py

Open http://localhost:8000 in your browser.

Configuration
-------------

Set these environment variables (or create a .env file):

    # Optional: OpenAI-compatible API key for LLM-generated responses
    OPENAI_API_KEY=sk-...

    # Optional: Custom API base URL (default: https://api.openai.com/v1)
    OPENAI_BASE_URL=https://api.openai.com/v1

    # Optional: Model to use (default: gpt-4o-mini)
    OPENAI_MODEL=gpt-4o-mini

    # Optional: Google Business Profile API key (not yet implemented)
    GOOGLE_API_KEY=...

    # Optional: SQLite database path (default: replyforce.db)
    REPLYFORCE_DB=replyforce.db

Mock Mode
---------

If GOOGLE_API_KEY is not set, ReplyForce starts in mock mode and seeds
10 realistic sample reviews with AI-generated (or template) responses.

How It Works
------------

1. Reviews are fetched from Google Business Profile API (or mock data)
2. Each review is analyzed by an LLM considering rating and tone
3. A professional, tone-matched response is drafted automatically
4. The dashboard presents reviews + responses for owner approval
5. Approved responses can be marked as "sent"

Dashboard Features
------------------

- Pending reviews with drafted AI responses
- Approve / Reject / Regenerate buttons
- Stats bar showing totals, pending, approved, sent, avg rating
- All-reviews view with status filtering
- Color-coded cards (green for positive, red for negative)

API Endpoints
-------------

    GET  /              Dashboard (pending reviews)
    GET  /all           Dashboard (all reviews)
    POST /approve/{id}  Approve a review response
    POST /reject/{id}   Reject a review response
    POST /send/{id}     Mark review as sent
    POST /regenerate/{id} Regenerate AI response
    GET  /api/reviews   JSON list of reviews
    GET  /api/stats     JSON statistics
    GET  /health        Health check

Architecture
------------

    main.py           FastAPI app, routes, startup
    models.py         SQLite models and queries
    reviewer.py       Review fetching and AI response generation
    templates/        Jinja2 HTML templates
    static/           CSS styles

Roadmap
-------

- v0.2: Real Google Business Profile API integration
- v0.2: Response editing in the dashboard
- v0.3: Multi-business support with auth
- v0.3: Email/Slack notifications for new reviews
- v0.4: Analytics and response quality tracking
- v1.0: Stripe billing ($29-49/mo per location)
