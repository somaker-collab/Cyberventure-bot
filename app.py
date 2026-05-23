import requests
from flask import Flask, request
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

app = Flask(__name__)

# ==================== CONFIGURATION ====================
# Replace these with your actual tokens before deploying
FACEBOOK_ACCESS_TOKEN = "YOUR_FACEBOOK_PAGE_ACCESS_TOKEN"
VERIFY_TOKEN = "YOUR_VERIFY_TOKEN"

# OpenRouter API (already provided)
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Facebook Graph API endpoint for sending messages
FB_MESSAGES_URL = "https://graph.facebook.com/v18.0/me/messages"

# ==================== CYBER VENTURE DATA ====================
COMPANY = {
    "name": "Cyber Venture",
    "tagline": "AI-Powered Cybersecurity Startup",
    "email": "cyberventuressupport@proton.me",
    "website": "bugfinder-pvyupdjc.fly.dev",
    "services": [
        "Vulnerability Assessment",
        "Penetration Testing",
        "Security Research",
        "AI-Assisted Threat Detection",
        "Threat Monitoring & Prevention",
        "Web & Application Security",
        "Digital Infrastructure Protection",
        "Security Awareness & Risk Analysis"
    ],
    "revenue_model": (
        "Cyber Venture generates revenue through multiple streams:\n"
        "1. Cybersecurity consulting and assessment fees\n"
        "2. Ongoing security monitoring subscriptions\n"
        "3. Penetration testing service contracts\n"
        "4. AI-powered security tool licensing\n"
        "5. Vulnerability research and reporting\n"
        "6. Security training and awareness programs\n\n"
        "Companies pay for our proactive security services to prevent cyber attacks before they happen."
    ),
    "competitive_advantage": (
        "What makes Cyber Venture different:\n"
        "• Prevention-first approach – we stop attacks before they happen\n"
        "• AI-native platform – built with AI from ground up\n"
        "• Continuous monitoring and adaptation\n"
        "• Transparent reporting and trust-based relationships\n"
        "• Research-driven vulnerability intelligence\n"
        "• Customized security solutions, not one-size-fits-all"
    ),
    "investor_value": (
        "The cybersecurity market exceeds $200B and grows 12-15% annually. "
        "Cyber Venture's AI-powered, prevention-first approach positions us perfectly "
        "in this expanding market with recurring revenue streams."
    ),
    "description": (
        "Cyber Venture is an AI-powered cybersecurity startup focused on proactive digital protection, "
        "vulnerability intelligence, and modern cyber defense solutions."
    ),
    "mission": "Helping businesses stay protected through prevention, intelligence, and trust.",
    "vision": "To become a recognized cybersecurity technology brand known for innovation and intelligent security solutions."
}

# ==================== WEBSITE CACHE ====================
_website_cache = {"content": None, "last_fetched": None}

def fetch_website_content():
    """Fetch and extract text from the Cyber Venture website (cached for 1 hour)."""
    now = datetime.now()
    if _website_cache["content"] and _website_cache["last_fetched"]:
        if (now - _website_cache["last_fetched"]) < timedelta(hours=1):
            return _website_cache["content"]

    try:
        url = f"https://{COMPANY['website']}"
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            clean = "\n".join(lines)
            _website_cache["content"] = clean
            _website_cache["last_fetched"] = now
            return clean
        else:
            print(f"Website fetch failed with status {resp.status_code}")
            return None
    except Exception as e:
        print(f"Website fetch error: {e}")
        return None

def search_website(query):
    """Find lines from the website that contain the query keywords."""
    content = fetch_website_content()
    if not content:
        return None
    keywords = query.lower().split()
    matches = []
    for line in content.split("\n"):
        if any(kw in line.lower() for kw in keywords):
            matches.append(line)
    return "\n".join(matches[:10]) if matches else None

# ==================== RELEVANCE DETECTION ====================
RELEVANT_KEYWORDS = [
    "cyber", "security", "hack", "vulnerability", "xss", "csrf", "sql injection",
    "ddos", "ransomware", "malware", "phishing", "exploit", "zero day",
    "penetration test", "firewall", "encryption", "threat", "incident response",
    "bug bounty", "ethical hacking", "owasp", "nist", "iso 27001",
    "invest", "investor", "funding", "revenue", "profit", "growth", "market",
    "business model", "startup", "pitch", "valuation", "equity", "roi",
    "money", "earn", "client", "customer", "pricing", "subscription",
    "partnership", "cyber venture", "cyberventure", "company", "service",
    "different", "unique", "advantage", "about", "contact", "email", "demo",
    "greetings", "hi", "hello", "hey", "namaste", "good morning", "good afternoon"
]

OFF_TOPIC_KEYWORDS = [
    "mathematics", "physics", "chemistry", "biology", "science branches",
    "movie", "song", "music", "game", "sport", "cricket", "football",
    "hollywood", "celebrity", "dating", "marriage", "relationship",
    "weather", "news", "politics", "joke", "funny", "recipe", "food",
    "restaurant", "history", "geography", "literature", "poetry", "art",
    "philosophy", "maths", "algebra", "calculus", "trigonometry"
]

def message_is_relevant(text):
    """Return True if the message is related to Cyber Venture or cybersecurity."""
    lower = text.lower().strip()
    # Allow simple greetings immediately
    greetings = ["hi", "hello", "hey", "namaste", "good morning", "good afternoon", "good evening"]
    if lower in greetings or any(lower.startswith(g) for g in greetings):
        return True

    # Reject messages containing clearly off-topic keywords,
    # but if they also contain business terms, allow them.
    for bad in OFF_TOPIC_KEYWORDS:
        if bad in lower:
            business = ["cyber", "security", "invest", "revenue", "business", "company", "venture"]
            if not any(b in lower for b in business):
                return False
            else:
                return True

    # Check for any relevant keyword
    for kw in RELEVANT_KEYWORDS:
        if kw in lower:
            return True

    # If message is long and contains tech/business words, consider it relevant
    if len(lower.split()) > 5:
        tech = ["security", "cyber", "hack", "attack", "vulnerability", "computer", "network", "app", "data"]
        if any(t in lower for t in tech):
            return True

    return False

# ==================== AI RESPONSE ====================
def build_system_prompt(extra_website_info=""):
    """Create the system prompt for the AI, optionally including website data."""
    website_section = ""
    if extra_website_info:
        website_section = f"\nRELEVANT WEBSITE CONTENT:\n{extra_website_info}\n"

    prompt = f"""You are a professional assistant for Cyber Venture, an AI-powered cybersecurity startup.
Use ONLY the information provided below to answer. Do NOT make up facts.

COMPANY DETAILS:
- Name: {COMPANY['name']}
- Email: {COMPANY['email']}
- Website: {COMPANY['website']}
- Services: {', '.join(COMPANY['services'])}
- Revenue Model: {COMPANY['revenue_model']}
- Competitive Advantage: {COMPANY['competitive_advantage']}
- Description: {COMPANY['description']}
- Mission: {COMPANY['mission']}
- Vision: {COMPANY['vision']}

{website_section}

RULES:
1. Only answer if the question is about Cyber Venture, cybersecurity, or business/investment.
2. For greetings, respond warmly and briefly introduce the company.
3. For cybersecurity questions (XSS, SQL injection, etc.), explain the concept and mention how Cyber Venture helps.
4. For business questions (revenue, investment, pricing), use the exact data above.
5. For questions like "what makes you different", use the Competitive Advantage info.
6. If the question is off-topic (e.g., mathematics, movies), reply: "I'm here to discuss Cyber Venture and cybersecurity topics only. How can I help you in that area?"
7. If you don't know the answer, reply: "I don't have that specific information. Please email us at {COMPANY['email']} and our team will help you."

Always be concise and professional. Do not add information not provided above.
"""
    return prompt

def get_ai_reply(user_message):
    """Call OpenRouter API and return the AI response."""
    # First, search website for relevant info
    website_info = search_website(user_message)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": f"https://{COMPANY['website']}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openai/gpt-3.5-turbo",  # Cheaper and faster; change to gpt-4 if needed
        "messages": [
            {"role": "system", "content": build_system_prompt(website_info)},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:
        resp = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=15)
        if resp.status_code == 200:
            reply = resp.json()["choices"][0]["message"]["content"]
            # Safety check – if AI says it doesn't know, return a helpful fallback
            if any(phrase in reply.lower() for phrase in ["i don't know", "i don't have", "i'm not sure"]):
                return f"I don't have that information yet. Please email us at {COMPANY['email']} and our team will get back to you soon."
            return reply
        else:
            print(f"OpenRouter error: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print(f"OpenRouter exception: {e}")
        return None

def get_fallback_response(user_message):
    """Pre-defined responses when the AI call fails."""
    lower = user_message.lower()

    # Greetings
    if any(greeting in lower for greeting in ["hi", "hello", "hey", "namaste"]):
        return f"Hello! 👋 Welcome to Cyber Venture, your AI-powered cybersecurity partner. We offer vulnerability assessment, penetration testing, and AI-driven threat detection. How can I help secure your business today?"

    # Revenue
    if any(word in lower for word in ["revenue", "earn", "money", "profit", "income"]):
        return f"💰 {COMPANY['revenue_model']}\n\n📧 For detailed financials: {COMPANY['email']}"

    # Why different
    if any(phrase in lower for phrase in ["different", "unique", "advantage", "why you", "what makes"]):
        return f"🛡️ {COMPANY['competitive_advantage']}\n\n📧 Learn more: {COMPANY['email']}"

    # Investment
    if any(word in lower for word in ["invest", "investor", "funding", "pitch"]):
        return f"🚀 {COMPANY['investor_value']}\n\n📧 For pitch deck: {COMPANY['email']}"

    # Technical cybersecurity
    if any(term in lower for term in ["xss", "csrf", "sql injection", "vulnerability", "attack", "hack"]):
        return f"That's a great cybersecurity question! At Cyber Venture we specialize in preventing such threats. For a detailed technical discussion, please email {COMPANY['email']} and our experts will help you."

    # Default
    return f"I don't have that specific information. Please email us at {COMPANY['email']} and our team will assist you."

# ==================== FACEBOOK MESSAGING ====================
def send_fb_message(recipient_id, text):
    """Send a text message to a Facebook user."""
    params = {"access_token": FACEBOOK_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    try:
        resp = requests.post(FB_MESSAGES_URL, params=params, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"FB send error: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"FB send exception: {e}")

def send_typing_on(recipient_id):
    """Send typing indicator."""
    params = {"access_token": FACEBOOK_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "sender_action": "typing_on"
    }
    try:
        requests.post(FB_MESSAGES_URL, params=params, json=payload, timeout=5)
    except Exception:
        pass

# ==================== WEBHOOK ROUTES ====================
@app.route("/webhook", methods=["GET"])
def verify():
    """Facebook webhook verification."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming Facebook messages."""
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender = event.get("sender", {}).get("id")
                if not sender:
                    continue
                msg = event.get("message")
                if msg and "text" in msg:
                    text = msg["text"]
                    process_message(sender, text)
    return "OK", 200

def process_message(sender_id, text):
    """Determine relevance, get response, and send it."""
    print(f"📨 [{sender_id}] {text}")

    if not message_is_relevant(text):
        reply = "I'm here to discuss Cyber Venture and cybersecurity topics only. How can I help you in that area?"
    else:
        reply = get_ai_reply(text)
        if reply is None:
            reply = get_fallback_response(text)

    # Facebook limits message length to 2000 characters
    max_len = 2000
    if len(reply) <= max_len:
        send_typing_on(sender_id)
        send_fb_message(sender_id, reply)
    else:
        # Split into chunks
        chunks = [reply[i:i+max_len] for i in range(0, len(reply), max_len)]
        for chunk in chunks:
            send_typing_on(sender_id)
            send_fb_message(sender_id, chunk)
    print(f"✅ Replied")

# ==================== OTHER ENDPOINTS ====================
@app.route("/")
def index():
    return f"""
    <h1>{COMPANY['name']} Chatbot</h1>
    <p>Status: Operational</p>
    <p>Contact: {COMPANY['email']}</p>
    """, 200

@app.route("/health")
def health():
    return {"status": "healthy", "company": COMPANY['name']}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
