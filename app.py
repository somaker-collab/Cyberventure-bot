import os
import json
import requests
from flask import Flask, request
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)

# ============================================================
# CONFIGURATION – Replace with your actual values
# ============================================================
FACEBOOK_ACCESS_TOKEN = "YOUR_FACEBOOK_PAGE_ACCESS_TOKEN"
VERIFY_TOKEN = "YOUR_VERIFY_TOKEN"

# OpenRouter API
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Facebook Graph API base URL
FB_API_URL = "https://graph.facebook.com/v18.0/me/messages"

# ============================================================
# CYBER VENTURE DATA
# ============================================================
CYBER_VENTURE_DATA = {
    "company_name": "Cyber Venture",
    "tagline": "AI-Powered Cybersecurity Startup",
    "contact_email": "cyberventuressupport@proton.me",
    "website": "bugfinder-pvyupdjc.fly.dev",

    "description": "Cyber Venture is an AI-powered cybersecurity startup focused on proactive digital protection, vulnerability intelligence, and modern cyber defense solutions.",

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

    "revenue_model": """Cyber Venture generates revenue through multiple streams:
1. Cybersecurity consulting and assessment fees
2. Ongoing security monitoring subscriptions
3. Penetration testing service contracts
4. AI-powered security tool licensing
5. Vulnerability research and reporting
6. Security training and awareness programs

Companies pay for our proactive security services to prevent cyber attacks before they happen.""",

    "competitive_advantage": """What makes Cyber Venture different:
• Prevention-first approach – we stop attacks before they happen
• AI-native platform – built with AI from ground up
• Continuous monitoring and adaptation
• Transparent reporting and trust-based relationships
• Research-driven vulnerability intelligence
• Customized security solutions, not one-size-fits-all""",

    "investor_value": "The cybersecurity market exceeds $200B and grows 12-15% annually. Cyber Venture's AI-powered, prevention-first approach positions us perfectly in this expanding market with recurring revenue streams.",

    "mission": "Helping businesses stay protected through prevention, intelligence, and trust.",

    "vision": "To become a recognized cybersecurity technology brand known for innovation and intelligent security solutions.",

    "current_phase": "Early growth phase – building credibility, visibility, and investor confidence.",
}

# ============================================================
# WEBSITE CONTENT CACHE
# ============================================================
website_content_cache = {
    "content": None,
    "last_fetched": None
}

def fetch_website_content():
    """Fetch and parse content from Cyber Venture website."""
    try:
        if website_content_cache["content"] and website_content_cache["last_fetched"]:
            time_diff = datetime.now() - website_content_cache["last_fetched"]
            if time_diff.seconds < 3600:
                return website_content_cache["content"]

        url = f"https://{CYBER_VENTURE_DATA['website']}"
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            clean_content = '\n'.join(lines)

            website_content_cache["content"] = clean_content
            website_content_cache["last_fetched"] = datetime.now()
            return clean_content
        else:
            print(f"Failed to fetch website: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching website: {str(e)}")
        return None

# ============================================================
# RELEVANCE CHECKING
# ============================================================
CYBER_SECURITY_TOPICS = [
    'xss', 'csrf', 'sql injection', 'ddos', 'ransomware', 'malware', 'phishing',
    'vulnerability', 'exploit', 'zero day', 'penetration testing', 'firewall',
    'encryption', 'authentication', 'authorization', 'oauth', 'ssl', 'tls',
    'security audit', 'risk assessment', 'compliance', 'gdpr', 'hipaa',
    'cyber attack', 'data breach', 'incident response', 'forensics',
    'bug bounty', 'ethical hacking', 'red team', 'blue team', 'threat',
    'owasp', 'nist', 'iso 27001', 'soc', 'siem', 'endpoint security',

    # business / investment
    'invest', 'investor', 'funding', 'revenue', 'profit', 'growth', 'market',
    'business model', 'startup', 'pitch', 'valuation', 'equity', 'stake',
    'roi', 'return', 'money', 'earn', 'client', 'customer', 'pricing',
    'cost', 'price', 'subscription', 'contract', 'partnership',

    # company specific
    'cyber venture', 'cyberventure', 'company', 'service', 'offer',
    'different', 'unique', 'advantage', 'why', 'who', 'what', 'how',
    'about', 'mission', 'vision', 'team', 'founder', 'contact',
    'email', 'website', 'demo', 'trial', 'consultation',

    # greetings
    'hi', 'hello', 'hey', 'namaste', 'good morning', 'good afternoon',
    'good evening', 'greetings', 'sup', 'yo', 'howdy'
]

IRRELEVANT_TOPICS = [
    'mathematics', 'physics', 'chemistry', 'biology', 'science branches',
    'astronomy', 'geology', 'botany', 'zoology', 'movie', 'song', 'music',
    'game', 'sport', 'cricket', 'football', 'hollywood', 'bollywood',
    'actor', 'actress', 'celebrity', 'girlfriend', 'boyfriend', 'dating',
    'marriage', 'relationship', 'love', 'friend', 'family', 'personal',
    'weather', 'news', 'politics', 'religion', 'joke', 'funny',
    'recipe', 'cooking', 'food', 'restaurant', 'history', 'geography',
    'literature', 'poetry', 'art', 'philosophy', 'maths', 'algebra',
    'calculus', 'trigonometry'
]

def is_relevant_to_business(message):
    """Determine if message is relevant to Cyber Venture business."""
    message_lower = message.lower().strip()

    greetings = ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening', 'greetings', 'sup', 'yo', 'howdy']
    if message_lower in greetings or any(message_lower.startswith(g) for g in greetings):
        return True, "greeting"

    for topic in IRRELEVANT_TOPICS:
        if topic in message_lower:
            business_terms = ['cyber', 'security', 'invest', 'revenue', 'business', 'company', 'venture']
            if any(term in message_lower for term in business_terms):
                return True, "mixed_business"
            return False, "irrelevant"

    for topic in CYBER_SECURITY_TOPICS:
        if topic in message_lower:
            return True, "relevant"

    question_patterns = ['what is', 'how to', 'explain', 'tell me about', 'define']
    if any(pattern in message_lower for pattern in question_patterns):
        tech_terms = ['security', 'cyber', 'hack', 'attack', 'vulnerability', 'tech', 'computer', 'network', 'web', 'app', 'data', 'code']
        if any(term in message_lower for term in tech_terms):
            return True, "tech_question"

    if len(message_lower.split()) > 8:
        return True, "long_message"

    return False, "unknown"

def get_website_info_for_query(query):
    """Search website content for relevant information."""
    website_content = fetch_website_content()
    if not website_content:
        return None

    keywords = query.lower().split()
    relevant_lines = []
    for line in website_content.split('\n'):
        if any(keyword in line.lower() for keyword in keywords):
            relevant_lines.append(line)

    if relevant_lines:
        return '\n'.join(relevant_lines[:10])
    return None

# ============================================================
# AI RESPONSE HANDLING
# ============================================================
def create_system_prompt(website_context=""):
    """Create context-aware system prompt."""
    website_section = ""
    if website_context:
        website_section = f"\nWEBSITE INFORMATION:\n{website_context}\n"

    system_prompt = f"""You are an AI representative for Cyber Venture, an AI-powered cybersecurity startup.

CRITICAL RULES:
1. ONLY answer questions related to cybersecurity, business, technology, and Cyber Venture
2. For greetings (hi, hello, namaste, etc.): Respond warmly and introduce Cyber Venture's services
3. For cybersecurity questions (XSS, SQL injection, vulnerabilities, etc.): Answer knowledgeably and connect to Cyber Venture's services
4. For business questions (revenue, investment, pricing, etc.): Answer based on Cyber Venture data
5. For questions about what makes Cyber Venture different: Emphasize prevention-first, AI-native approach
6. If question is about unrelated topics (mathematics, science branches, entertainment, etc.): Politely decline
7. If you don't know the exact answer: Say "I don't have that specific information right now. Let me forward this to our team. They will get back to you soon at {CYBER_VENTURE_DATA['contact_email']}. Thank you for your patience!"
8. Use website information when available to provide accurate answers
9. Always be professional, helpful, and focused on cybersecurity/business

COMPANY INFORMATION:
Name: {CYBER_VENTURE_DATA['company_name']}
Email: {CYBER_VENTURE_DATA['contact_email']}
Website: {CYBER_VENTURE_DATA['website']}
Services: {', '.join(CYBER_VENTURE_DATA['services'])}
Revenue Model: {CYBER_VENTURE_DATA['revenue_model']}
Competitive Advantage: {CYBER_VENTURE_DATA['competitive_advantage']}

{website_section}

RESPONSE FORMAT:
- For valid questions: Provide helpful, accurate answers
- For greetings: Warm welcome + introduce Cyber Venture
- For unknown answers: Forward to team message
- For irrelevant topics: "I'm specialized in cybersecurity and business topics related to Cyber Venture. I can help you with questions about cybersecurity, our services, investment opportunities, or how we protect businesses. How can I assist you today?"
"""
    return system_prompt

def get_ai_response(user_message, user_id=None):
    """Get AI response with proper context handling."""
    try:
        is_relevant, category = is_relevant_to_business(user_message)
        if not is_relevant:
            return get_rejection_message()

        website_context = get_website_info_for_query(user_message)

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": f"https://{CYBER_VENTURE_DATA['website']}",
            "Content-Type": "application/json",
            "X-Title": "Cyber Venture Assistant"
        }

        system_prompt = create_system_prompt(website_context)

        if category == "greeting":
            system_prompt += "\n\nThis is a greeting. Respond warmly and introduce Cyber Venture's cybersecurity services."
        elif any(term in user_message.lower() for term in ['revenue', 'earn', 'money', 'profit', 'income']):
            system_prompt += f"\n\nThis is a revenue question. Use this exact revenue information: {CYBER_VENTURE_DATA['revenue_model']}"
        elif any(term in user_message.lower() for term in ['different', 'unique', 'advantage', 'why you', 'what makes']):
            system_prompt += f"\n\nThis is a competitive advantage question. Use this exact information: {CYBER_VENTURE_DATA['competitive_advantage']}"
        elif any(term in user_message.lower() for term in ['xss', 'csrf', 'sql injection', 'vulnerability', 'attack']):
            system_prompt += "\n\nThis is a cybersecurity technical question. Answer it knowledgeably and mention how Cyber Venture helps with such security issues."

        data = {
            "model": "openai/gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 800,
            "top_p": 0.9,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.3
        }

        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']

            if any(phrase in ai_response.lower() for phrase in ["i don't know", "i don't have", "i'm not sure", "i cannot"]):
                ai_response = f"I don't have that specific information right now. Let me forward this to our team at {CYBER_VENTURE_DATA['contact_email']}. They will get back to you soon. Thank you for your patience! 🙏"

            log_interaction(user_id, user_message, ai_response, category)
            return ai_response
        else:
            return get_fallback_response(user_message, category)

    except Exception as e:
        print(f"Error: {str(e)}")
        return get_fallback_response(user_message, "error")

def get_rejection_message():
    """Message for irrelevant topics."""
    return "I'm specialized in cybersecurity and business topics related to Cyber Venture. I can help you with questions about cybersecurity (like XSS, SQL injection, vulnerabilities), our services, investment opportunities, or how we protect businesses. How can I assist you today?"

def get_fallback_response(user_message, category):
    """Fallback responses based on category."""
    message_lower = user_message.lower()

    if category == "greeting":
        return f"Hello! 👋 Welcome to Cyber Venture – your AI-powered cybersecurity partner. We help businesses prevent cyber attacks through vulnerability assessment, penetration testing, and AI-driven threat detection. How can I help secure your business today?"

    elif any(word in message_lower for word in ['revenue', 'earn', 'money', 'profit', 'income', 'business model']):
        return f"💰 **How Cyber Venture Earns Revenue**\n\n{CYBER_VENTURE_DATA['revenue_model']}\n\n📧 For detailed financial information: {CYBER_VENTURE_DATA['contact_email']}"

    elif any(word in message_lower for word in ['different', 'unique', 'advantage', 'why you', 'what makes']):
        return f"🛡️ **What Makes Cyber Venture Different**\n\n{CYBER_VENTURE_DATA['competitive_advantage']}\n\n📧 Learn more: {CYBER_VENTURE_DATA['contact_email']}"

    elif any(word in message_lower for word in ['invest', 'investor', 'funding', 'pitch']):
        return f"🚀 **Investment Opportunity**\n\n{CYBER_VENTURE_DATA['investor_value']}\n\n📧 For pitch deck and details: {CYBER_VENTURE_DATA['contact_email']}"

    elif any(word in message_lower for word in ['xss', 'csrf', 'sql', 'injection', 'vulnerability', 'attack', 'hack', 'exploit']):
        return f"I can help explain that cybersecurity concept! However, for detailed technical discussions, it would be better to connect directly. Please email us at {CYBER_VENTURE_DATA['contact_email']} and our security experts will provide comprehensive information about how Cyber Venture addresses these threats."

    else:
        return f"I don't have that specific information right now. Let me forward this to our team at {CYBER_VENTURE_DATA['contact_email']}. They will get back to you soon. Thank you for your patience! 🙏"

def log_interaction(user_id, user_message, bot_response, category):
    """Log interactions with category."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] User:{user_id} | Category:{category} | Message:{user_message[:100]}")

# ============================================================
# FACEBOOK MESSAGE SENDING (Direct API)
# ============================================================
def send_facebook_message(recipient_id, message_text):
    """Send a text message via Facebook Graph API."""
    url = FB_API_URL
    params = {"access_token": FACEBOOK_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, params=params, json=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

def send_facebook_action(recipient_id, action):
    """Send typing indicator or mark seen."""
    url = FB_API_URL
    params = {"access_token": FACEBOOK_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "sender_action": action
    }
    requests.post(url, params=params, json=payload)

# ============================================================
# FACEBOOK WEBHOOK ROUTES
# ============================================================
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Facebook webhook verification."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Cyber Venture Active", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages."""
    data = request.get_json()

    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for event in entry.get('messaging', []):
                sender_id = event.get('sender', {}).get('id')
                if not sender_id:
                    continue

                if event.get('message') and 'text' in event['message']:
                    user_message = event['message']['text']
                    handle_message(sender_id, user_message)

    return "OK", 200

def handle_message(sender_id, user_message):
    """Process and respond to message."""
    print(f"📨 Message: {user_message}")
    # Send typing indicator
    send_facebook_action(sender_id, "typing_on")

    response = get_ai_response(user_message, sender_id)

    # Facebook has a 2000 character limit per message
    if len(response) > 2000:
        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
        for chunk in chunks:
            send_facebook_message(sender_id, chunk)
    else:
        send_facebook_message(sender_id, response)

    print(f"✅ Responded: {response[:100]}...")

@app.route('/')
def index():
    return f"""
    <h1>🛡️ Cyber Venture Chatbot</h1>
    <p>Status: Active</p>
    <p>Website: {CYBER_VENTURE_DATA['website']}</p>
    <p>Email: {CYBER_VENTURE_DATA['contact_email']}</p>
    <p>Handles: Cybersecurity, Business, Investment queries</p>
    <p>Rejects: Unrelated topics (math, science, entertainment, etc.)</p>
    """, 200

@app.route('/health')
def health():
    return {"status": "active", "website": CYBER_VENTURE_DATA['website']}, 200

@app.route('/refresh_website')
def refresh_website():
    """Manually refresh website cache."""
    website_content_cache["content"] = None
    content = fetch_website_content()
    if content:
        return f"Website refreshed! Content length: {len(content)} chars", 200
    return "Failed to fetch website", 500

if __name__ == '__main__':
    print("Cyber Venture Chatbot Starting...")
    print(f"Website: {CYBER_VENTURE_DATA['website']}")
    print(f"Contact: {CYBER_VENTURE_DATA['contact_email']}")
    print("Handles: Cybersecurity + Business queries")
    
