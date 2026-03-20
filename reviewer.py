"""
ReplyForce v0.1 — Core Review Logic
Fetches reviews (or generates mocks) and drafts AI responses.
"""

import os
import random
from datetime import datetime, timedelta
from openai import OpenAI
from models import insert_review, update_response

# ---------------------------------------------------------------------------
# Mock review data
# ---------------------------------------------------------------------------

MOCK_REVIEWS = [
    {
        "reviewer": "Sarah M.",
        "rating": 5,
        "text": "Absolutely love this place! The staff was incredibly friendly and knowledgeable. My haircut was exactly what I asked for. Will definitely be coming back!"
    },
    {
        "reviewer": "James K.",
        "rating": 5,
        "text": "Best coffee in town! The atmosphere is cozy and perfect for getting work done. Their pastries are fresh every morning. A hidden gem!"
    },
    {
        "reviewer": "Linda R.",
        "rating": 4,
        "text": "Great food and service. The only reason I'm not giving 5 stars is because we had to wait 20 minutes for a table even with a reservation. But the meal itself was fantastic."
    },
    {
        "reviewer": "Mike T.",
        "rating": 1,
        "text": "Terrible experience. Waited over an hour for our food, and when it finally arrived, my order was wrong. Manager didn't seem to care. Won't be returning."
    },
    {
        "reviewer": "Emily W.",
        "rating": 5,
        "text": "Outstanding customer service! They went above and beyond to help me find exactly what I needed. The product quality is top-notch. Highly recommend!"
    },
    {
        "reviewer": "David L.",
        "rating": 3,
        "text": "Decent place but nothing special. Food was okay, prices are a bit high for what you get. Service was fine but nothing memorable."
    },
    {
        "reviewer": "Rachel B.",
        "rating": 2,
        "text": "Disappointing visit. The place was dirty and the staff seemed overwhelmed. Food was mediocre at best. Expected much more based on other reviews."
    },
    {
        "reviewer": "Tom H.",
        "rating": 5,
        "text": "This is our go-to family restaurant! Kids love the menu options, and we love the quality and freshness. The owner always makes us feel welcome. 10/10!"
    },
    {
        "reviewer": "Patricia N.",
        "rating": 4,
        "text": "Really enjoyed my experience here. The team was professional and the results exceeded my expectations. Only minor issue was parking being a bit tight."
    },
    {
        "reviewer": "Carlos G.",
        "rating": 1,
        "text": "Booked an appointment weeks in advance, showed up on time, and they had no record of it. Staff was rude about it. Completely unprofessional."
    },
]


def seed_mock_reviews(business_name: str, location_id: str) -> int:
    """
    Seed the database with mock reviews and auto-generate responses.
    Returns number of reviews created.
    """
    count = 0
    for review in MOCK_REVIEWS:
        review_id = insert_review(
            business_name=business_name,
            location_id=location_id,
            reviewer_name=review["reviewer"],
            rating=review["rating"],
            review_text=review["text"]
        )
        # Generate a response for each
        response = generate_response(review["text"], review["rating"], business_name)
        update_response(review_id, response)
        count += 1
    return count


# ---------------------------------------------------------------------------
# LLM-powered response generation
# ---------------------------------------------------------------------------

def _get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_response(review_text: str, rating: int, business_name: str = "our business") -> str:
    """
    Generate a professional response to a review using an LLM.
    Falls back to template responses if no API key is set.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return _template_response(review_text, rating, business_name)

    # Build tone-specific system prompt
    if rating >= 5:
        tone = "Warm, grateful, and enthusiastic. Celebrate their experience. Invite them back."
    elif rating >= 4:
        tone = "Appreciative and positive. Acknowledge any minor concerns gracefully."
    elif rating >= 3:
        tone = "Balanced and professional. Thank them for feedback and address any concerns constructively."
    elif rating >= 2:
        tone = "Empathetic and solution-oriented. Acknowledge the issues seriously and offer to make it right."
    else:
        tone = "Deeply empathetic, apologetic, and professional. Take full responsibility and offer a direct resolution path."

    system_prompt = f"""You are a professional review responder for "{business_name}".
Write a short, authentic response (2-4 sentences) to the customer review below.
Tone: {tone}
Rules:
- Be genuine, not robotic
- Reference something specific from their review
- Keep it under 100 words
- Do NOT use emojis
- Sign off warmly but professionally
- Do NOT invent details not mentioned in the review"""

    try:
        client = _get_openai_client()
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review ({rating}/5 stars): {review_text}"}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[reviewer] LLM call failed, falling back to template: {e}")
        return _template_response(review_text, rating, business_name)


def _template_response(review_text: str, rating: int, business_name: str) -> str:
    """
    Template-based response fallback when no API key is available.
    Produces reasonable responses based on rating tiers.
    """
    if rating == 5:
        templates = [
            f"Thank you so much for your wonderful review! We're thrilled to hear about your positive experience. We look forward to welcoming you back to {business_name} soon!",
            f"We truly appreciate your kind words! It means the world to our team to know we've made your experience special. Thank you for choosing {business_name}!",
            f"What a fantastic review — thank you! We're delighted you had such a great experience, and we can't wait to serve you again at {business_name}!"
        ]
    elif rating == 4:
        templates = [
            f"Thank you for your review and feedback! We're glad you had a positive experience and appreciate you sharing the areas where we can improve. We hope to see you again soon!",
            f"We really appreciate your honest feedback! It's great to know what we're doing well, and your note about room for improvement helps us grow. Thank you!",
            f"Thank you for taking the time to leave a review! We're pleased you enjoyed your visit and will take your constructive feedback to heart. Hope to welcome you back!"
        ]
    elif rating == 3:
        templates = [
            f"Thank you for your feedback. We take all comments seriously and are working to improve the experience for every customer. We'd love the chance to earn a higher rating next time.",
            f"We appreciate your honest review. Your feedback helps us identify where we can do better. We hope you'll give us another opportunity to impress you.",
            f"Thank you for sharing your experience. We're sorry it didn't fully meet expectations and are actively addressing the areas you mentioned. We'd welcome another chance to serve you."
        ]
    elif rating == 2:
        templates = [
            f"We're sorry to hear about your experience and take your feedback very seriously. We'd like to make this right — please reach out to us directly so we can address your concerns.",
            f"Thank you for bringing this to our attention. We sincerely apologize for falling short of your expectations. We'd appreciate the opportunity to discuss this further and make amends.",
            f"We're truly sorry for the disappointing experience. This doesn't reflect the standard we strive for. Please contact us directly so we can work to resolve this."
        ]
    else:  # 1 star
        templates = [
            f"We sincerely apologize for your experience. This is not the level of service we strive for, and we want to make it right. Please contact us directly so we can address this personally.",
            f"We are deeply sorry for the frustration and disappointment you experienced. Your feedback is taken very seriously, and we would like the chance to make this right. Please reach out to us directly.",
            f"Please accept our sincerest apologies. What you experienced falls far below our standards, and we take full responsibility. We'd appreciate the opportunity to speak with you directly to resolve this."
        ]
    return random.choice(templates)


# ---------------------------------------------------------------------------
# Google Business Profile API (stub for future integration)
# ---------------------------------------------------------------------------

def fetch_reviews_from_google(location_id: str) -> list[dict]:
    """
    Fetch reviews from Google Business Profile API.
    Currently returns empty list — implement when API access is available.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("[reviewer] No GOOGLE_API_KEY set — skipping Google API fetch")
        return []

    # TODO: Implement actual Google Business Profile API integration
    # Endpoint: https://mybusinessbusinessinformation.googleapis.com/v1/{name}/reviews
    print(f"[reviewer] Google API integration not yet implemented for location {location_id}")
    return []
