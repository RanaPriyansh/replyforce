"""
ReplyForce v0.1 — FastAPI Application
AI-powered Google Review responder for multi-location businesses.
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import init_db, get_pending_reviews, get_all_reviews, update_status, get_review_stats
from reviewer import seed_mock_reviews, generate_response, update_response

# Load .env if present
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and seed mock data on startup."""
    init_db()
    # Seed mock reviews if DB is empty and we're in mock mode
    stats = get_review_stats()
    if stats["total"] == 0 and not os.getenv("GOOGLE_API_KEY"):
        print("[replyforce] No GOOGLE_API_KEY found — seeding 10 mock reviews")
        count = seed_mock_reviews("Downtown Coffee & Bistro", "loc-downtown-001")
        print(f"[replyforce] Seeded {count} mock reviews with AI-generated responses")
    yield
    print("[replyforce] Shutting down")


app = FastAPI(
    title="ReplyForce",
    description="AI-powered Google Review responder for multi-location businesses",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Web Dashboard Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing pending reviews."""
    pending = get_pending_reviews()
    stats = get_review_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "reviews": pending,
        "stats": stats,
        "tab": "pending"
    })


@app.get("/all", response_class=HTMLResponse)
async def all_reviews(request: Request):
    """Show all reviews regardless of status."""
    reviews = get_all_reviews()
    stats = get_review_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "reviews": reviews,
        "stats": stats,
        "tab": "all"
    })


@app.post("/approve/{review_id}")
async def approve_review(review_id: int):
    """Approve a review response."""
    update_status(review_id, "approved")
    return RedirectResponse(url="/", status_code=303)


@app.post("/reject/{review_id}")
async def reject_review(review_id: int):
    """Reject a review response — sets back to pending with no response."""
    update_status(review_id, "rejected")
    return RedirectResponse(url="/", status_code=303)


@app.post("/send/{review_id}")
async def send_review(review_id: int):
    """Mark an approved review as sent."""
    update_status(review_id, "sent")
    return RedirectResponse(url="/", status_code=303)


@app.post("/regenerate/{review_id}")
async def regenerate_response(review_id: int):
    """Regenerate AI response for a review."""
    from models import get_db
    conn = get_db()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    if row:
        new_response = generate_response(row["review_text"], row["rating"], row["business_name"])
        update_response(review_id, new_response)
        update_status(review_id, "pending")
    return RedirectResponse(url="/", status_code=303)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/reviews")
async def api_get_reviews(status: str = None):
    """Get reviews as JSON."""
    if status == "pending":
        return get_pending_reviews()
    return get_all_reviews()


@app.get("/api/stats")
async def api_get_stats():
    """Get review statistics."""
    return get_review_stats()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ReplyForce", "version": "0.1.0"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
