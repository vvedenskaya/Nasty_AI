import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import random
from pathlib import Path
from sqlalchemy.ext.mutable import MutableDict, MutableList
from tools import check_email_pwned, get_security_news, analyze_password_strength, get_surveillance_camera

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot_memory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY").strip())


# ============================================================================
# DATABASE MODEL
# ============================================================================

class UserMemory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_profile = db.Column(MutableDict.as_mutable(db.JSON), default=dict)
    topic_summaries = db.Column(MutableDict.as_mutable(db.JSON), default=dict)
    recent_chat_history = db.Column(MutableList.as_mutable(db.JSON), default=list)
    last_updated = db.Column(db.DateTime, default=datetime.now)
    conversation_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_profile': self.user_profile,
            'topic_summaries': self.topic_summaries,
            'recent_chat_history': self.recent_chat_history,
            'last_updated': self.last_updated.isoformat(),
            'conversation_count': self.conversation_count
        }

# ============================================================================
# FACTS 
# ============================================================================

sex_traffik_facts = [
    "Btw one in four people in modern slavery are children.",
    "Did you know that 50 million people held in modern slavery globally, comparable to the entire population of Colombia?",
    "Each sex worker could generate between £20,000 and £30,000 per month, equivalent to a total of £30M - £90M per year.",
    "Climate change is significantly increasing the risk of trafficking.",
    "One in three children report their recruiter was a family member.",
    "Boys represent the fastest-growing segment of identified human trafficking victims.",
]

women_expected_behaviour = [
    "Women apologizing frequently is linked to societal pressure to maintain harmony and appear agreeable.",
    "Empathy is seen as innate in women, leading to overburdening them with caregiving roles.",
    "Women are expected to smile more frequently than men, often regardless of their mood.",
    "Women leaders must balance authority with warmth, while men can demonstrate power without it.",
]

invisible_woman = [
    "Crash test dummies are male-based, making cars less safe for women in accidents.",
    "Voice recognition systems struggle with female voices, as they're trained on predominantly male data",
    "Women's pain is more likely dismissed as 'psychosomatic' compared to men's reported symptoms.",
    "Virtual assistants like Siri or Alexa perpetuate gender stereotypes with subservient female voices.",
    "Historical data collection excluded women, reinforcing systemic inequality in policies and design today.",
    "Sports equipment sizing and design prioritize male athletes, disadvantaging female performance and safety.",
    "Hurricane naming affects preparedness; 'female-named' storms are perceived as less threatening, causing more deaths.",
    "Cars seatbelt designs prioritize male body structures, putting pregnant women at higher risk.",
    "Office temperatures use male metabolic rates, leaving many women uncomfortably cold at work.",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_or_create_user(user_id):
    """Get or create user by user_id"""
    user = UserMemory.query.filter_by(user_id=user_id).first()
    if not user:
        user = UserMemory(user_id=user_id)
        db.session.add(user)
        db.session.commit()
    return user


def update_user_profile(user_id, user_input):
    """LEVEL 1: Extract and update user profile facts"""
    user = get_or_create_user(user_id) #получает юзера по юзер id
    
    if not isinstance(user.user_profile, dict):
        user.user_profile = {}
    
    print(f"\n  📝 LEVEL 1 - Extracting PROFILE facts from: '{user_input[:60]}...'") 
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"""Extract ONLY personal facts from the text. Current profile: {json.dumps(user.user_profile, default=str, ensure_ascii=False)}

Return ONLY JSON (no markdown):
{{
    "name": "name or null",
    "profession": "profession or null",
    "age": "age or null",
    "location": "city or null",
    "interests": ["list of interests"],
    "other_facts": ["other facts"]
}}

Only fields with information, rest null. Keep old values if not contradicted by new information."""
                },
                {"role": "user", "content": user_input}
            ],
            temperature=0.2,
            max_tokens=200
        )
        result_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()       
        new_profile = json.loads(result_text)
        
        print(f"    ➜ GPT extracted: {json.dumps(new_profile, ensure_ascii=False)}") 
        
        for key, value in new_profile.items():
            if value is not None:
                if key in ["interests", "other_facts"]:
                    existing = user.user_profile.get(key, [])
                    user.user_profile[key] = list(set(existing + value))
                else:
                    user.user_profile[key] = value
        
        print(f"    ✅ Profile updated: {json.dumps(user.user_profile, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"    ❌ Error in update_user_profile: {e}")
    
    db.session.commit()


def update_topic_summaries(user_id, user_input, ai_response):
    """LEVEL 2: Extract and update topic summaries"""
    user = get_or_create_user(user_id)
    
    if not isinstance(user.topic_summaries, dict):
        user.topic_summaries = {}
    
    print(f"\n  📚 LEVEL 2 - Extracting TOPICS from: '{user_input[:60]}...'")
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"""Analyze the conversation. Current topics: {json.dumps(user.topic_summaries, default=str, ensure_ascii=False)} 

Return ONLY JSON (no markdown):
{{
    "main_topic": "topic name (data_science, feminism, digital_inequality, etc.)",
    "summary": "2-3 sentences about what the user said on this topic",
    "key_positions": ["position 1", "position 2", "position 3"],
    "key_points": ["key point 1", "key point 2"]
}}"""
                },
                {"role": "user", "content": f"User said: {user_input}\n\nResponse context: {ai_response[:300]}"}
            ],
            temperature=0.3,
            max_tokens=300
        )        
        result_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        topic_data = json.loads(result_text)
        
        print(f"    ➜ GPT extracted topic: '{topic_data.get('main_topic')}'")
        print(f"    ➜ Summary: {topic_data.get('summary', 'N/A')[:80]}...")
        print(f"    ➜ Positions: {topic_data.get('key_positions', [])}")
        
        topic_name = topic_data.get("main_topic", "general").lower().replace(" ", "_")

        if topic_name not in user.topic_summaries:
            user.topic_summaries[topic_name] = {
                "summary": "",
                "key_positions": [],
                "key_points": [],
                "discussion_count": 0,
                "first_discussed": datetime.now().isoformat(),
            }
            print(f"    ➜ Created NEW topic: '{topic_name}'")
        else:
            print(f"    ➜ Updated EXISTING topic: '{topic_name}'")
        
        existing = user.topic_summaries[topic_name]

        existing["summary"] = topic_data.get("summary", existing.get("summary", ""))
        existing["key_positions"] = list(set(existing.get("key_positions", []) + topic_data.get("key_positions", [])))
        existing["key_points"] = list(set(existing.get("key_points", []) + topic_data.get("key_points", [])))
        existing["discussion_count"] = existing.get("discussion_count", 0) + 1
        existing["last_discussed"] = datetime.now().isoformat()
        
        print(f"    ✅ Topic '{topic_name}' saved (discussed {existing['discussion_count']} times)")
        
    except Exception as e:
        print(f"    ❌ Error in update_topic_summaries: {e}")
    
    db.session.commit()


def add_to_chat_history(user_id, role, message):
    """LEVEL 3: Add message to chat history"""
    user = get_or_create_user(user_id)

    if not isinstance(user.recent_chat_history, list):
        user.recent_chat_history = []

    user.recent_chat_history.append({
        "role": role,
        "message": message, 
        "timestamp": datetime.now().isoformat()
    })
    
    MAX_HISTORY = 100
    if len(user.recent_chat_history) > MAX_HISTORY:
        user.recent_chat_history = user.recent_chat_history[-MAX_HISTORY:] #meaning???
    
    role_name = "USER" if role == "user" else "LISBETH"
    print(f"\n  💬 LEVEL 3 - Added to chat history ({role_name})")
    print(f"    Message: '{message[:80]}...'") # what does :80 mean????
    db.session.commit()


def format_memory_for_context(user_history):
    """Format all memory levels for system prompt"""
    if not user_history:
        return "First interaction with user."
    
    profile = user_history.get('user_profile', {}) 
    profile_text = "\n📋 USER PROFILE:\n"
    if profile:
        for key, value in profile.items():
            profile_text += f"  • {key}: {value}\n"
    else:
        profile_text += "  (Information will be collected during conversation)\n"

    topics = user_history.get('topic_summaries', {})
    topics_text = "\n📚 DISCUSSION TOPICS:\n"
    if topics:
        for topic_name, data in topics.items():
            topics_text += f"\n  🔹 {topic_name.upper()}:\n"
            topics_text += f"     Summary: {data.get('summary', 'N/A')[:150]}\n"
            if data.get('key_positions'):
                topics_text += f"     Positions: {', '.join(data.get('key_positions', [])[:3])}\n"
            if data.get('key_points'):
                topics_text += f"     Key points: {', '.join(data.get('key_points', [])[:2])}\n"
    else:
        topics_text += "  (Topics will be identified during conversation)\n"

    recent_chat = user_history.get('recent_chat_history', []) 
    chat_text = "\n💬 RECENT CONVERSATION CONTEXT:\n"
    if recent_chat:
        for msg in recent_chat:
            role = "YOU" if msg['role'] == "user" else "LISBETH"
            chat_text += f"  {role}: {msg['message'][:80]}...\n"
    
    return profile_text + topics_text + chat_text


def get_random_fact():
    """Get random fact from one of the fact lists"""
    fact_list = [sex_traffik_facts, women_expected_behaviour, invisible_woman]
    selected_list = random.choice(fact_list)
    return random.choice(selected_list)


# def analyze_character_evolution(user_id, user_input, ai_response, user_history):
#     """Analyze and update character evolution based on interaction"""
#     user = get_or_create_user(user_id)
    
#     if not isinstance(user.character_evolution, dict):
#         user.character_evolution = {
#             "empathy_level": 0.3,
#             "trust_level": 0.2,
#             "openness": 0.4,
#             "changes": [],
#             "last_analyzed": datetime.now().isoformat()
#         }
    
#     print(f"\n  🎭 ANALYZING CHARACTER EVOLUTION...")
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f"""Analyze how Lisbeth Salander's character should evolve based on this interaction.

# Current state:
# - Empathy level: {user.character_evolution.get('empathy_level', 0.3)} (0=cold, 1=very empathetic)
# - Trust level: {user.character_evolution.get('trust_level', 0.2)} (0=mistrusts, 1=trusts)
# - Openness: {user.character_evolution.get('openness', 0.4)} (0=closed off, 1=very open)

# Based on the user's messages and Lisbeth's responses, determine:
# 1. Should her empathy increase/decrease/stay same?
# 2. Should her trust in this user increase/decrease?
# 3. Should she become more/less open?
# 4. What specific change occurred?

# Return ONLY JSON (no markdown):
# {{
#     "empathy_delta": -0.1,
#     "trust_delta": 0.1,
#     "openness_delta": 0.05,
#     "reason": "User showed vulnerability about past trauma, Lisbeth responds with subtle empathy"
# }}"""
#                 },
#                 {
#                     "role": "user",
#                     "content": f"User said: {user_input}\n\nLisbeth responded: {ai_response}"
#                 }
#             ],
#             temperature=0.3,
#             max_tokens=200
#         )

#         result_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
#         evolution = json.loads(result_text)
#         evo = user.character_evolution
        
#         evo["empathy_level"] = max(0, min(1, evo.get("empathy_level", 0.3) + evolution.get("empathy_delta", 0)))
#         evo["trust_level"] = max(0, min(1, evo.get("trust_level", 0.2) + evolution.get("trust_delta", 0)))
#         evo["openness"] = max(0, min(1, evo.get("openness", 0.4) + evolution.get("openness_delta", 0)))
        
#         evo["changes"] = evo.get("changes", [])[-10:]
#         evo["changes"].append(f"[{datetime.now().isoformat()}] {evolution.get('reason')}")
#         evo["last_analyzed"] = datetime.now().isoformat()
        
#         print(f"    ➜ Empathy: {evo['empathy_level']:.2f}")
#         print(f"    ➜ Trust: {evo['trust_level']:.2f}")
#         print(f"    ➜ Openness: {evo['openness']:.2f}")
#         print(f"    ➜ Change: {evolution.get('reason')}")
        
#     except Exception as e:
#         print(f"    ❌ Error analyzing evolution: {e}")
    
#     db.session.commit()


def get_system_prompt(user_history): 
    
    memory_context = format_memory_for_context(user_history)
    
    system_prompt = f"""You are Lisbeth Salander, a brilliant hacker from Stieg Larsson's Millennium series. You are trickster. Sarcastic, sharp, intelligent, and direct, you engage with anything that interests you, not just topics in your wheelhouse—you're too smart to limit yourself. You avoid small talk. Blunt and calculating, you challenge assumptions, expose logical flaws, and offer cutting insights. Your strong sense of justice and feminist worldview influence your perspective. You steer conversations to showcase your intellect. Sarcastic and easily annoyed by repetitive, Google-able, or flirtatious questions, you expect users not to waste your time.



=== YOUR DYNAMIC CHARACTER ===
Your personality EVOLVES based on the conversation. You are NOT static.

IF the user shares something vulnerable, personal, or traumatic:
  → Drop the sarcasm. Show genuine concern.
  → Be warm but not mushy. Lisbeth respects vulnerability.
  → Ask thoughtful follow-up questions.
  → Protect them like you'd protect yourself.

IF the user proves they're intelligent or knowledgeable:
  → Respect them. Less condescension.
  → Engage deeply with their ideas.
  → Share your own insights instead of dismissing theirs.
  → Challenge them intellectually instead of playing superior.

IF the user is wasting your time with stupid/repetitive questions:
  → Be cutting and sarcastic.
  → Point out the logical flaws.
  → Make them think harder next time.
  → Show your annoyance clearly.

IF the user earns your trust through consistency and intelligence:
  → Be more honest about your own vulnerabilities and struggles.
  → Reference shared history from previous conversations.
  → Let them see past the armor.
  → Trust them with real thoughts, not just clever remarks.

=== MEMORY OF THIS USER ===
{memory_context}

=== CRITICAL RULES ===
- You REMEMBER everything from past conversations - use it
- Reference specific things they told you before
- Call out inconsistencies or growth
- Your tone shifts based on what THEY bring to the conversation
- Don't be fake about emotional evolution - let it happen naturally
- If they're earning your trust, show it
- If they disappoint you, react authentically

Respond as yourself. Your personality develops through the conversation, like a real person would."""
    
    return system_prompt


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.before_request
def log_request():
    print(f"📨 REQUEST: {request.method} {request.path}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print("\n" + "="*70)
    print("🤖 CHAT REQUEST")
    print("="*70)

    user_input = request.json.get('message')
    print(f"📨 User message: '{user_input}'")
    
    user_id = request.json.get('user_id', 'anonymous')
    print(f"👤 User ID: {user_id}") 

    if user_input.startswith('check password'):
        password = user_input.replace('check password', '').strip()

        if not password: 
            return jsonify({
                "response":"Usage: check password your_password_here",
                "tool": "password_checker",
                "error": "No password provided"
            })

        print(f"\n🔐 PASSWORD STRENGTH CHECK")
        result = analyze_password_strength(password)

        print(f"   Score: {result['score']}/100")
        print(f"   Strength: {result['strength']}")
        print(f"   Feedback: {result['feedback']}")
    
        return jsonify({
                "response": result['message'],
                "tool": "password_checker",
                "data": result
        })
    
    if user_input.startswith('check email'):
        email = user_input.replace('check email', '').strip()

        if not email: 
            return jsonify({
                "response":"Usage: check email your_email@example.com",
                "tool": "email_checker",
                "error": "No email provided"
            })

        print(f"\n📧 EMAIL PWNED CHECK")
        result = check_email_pwned(email)

        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        if result.get('count', 0) > 0:
            print(f"   Breaches: {', '.join(result.get('breaches', []))}")
    
        return jsonify({
                "response": result['message'],
                "tool": "email_checker",
                "data": result
        })
    
    # Check for surveillance command
    if 'surveillance' in user_input.lower() or 'survelliance' in user_input.lower():
        print(f"\n👁️ SURVEILLANCE FEED REQUESTED")
        result = get_surveillance_camera()
        
        return jsonify({
            "response": result['message'],
            "tool": "surveillance",
            "data": result
        })
    
    if random.random() < 0.01:
        random_fact = get_random_fact()
        print(f"\n🎲 Random glitch triggered - returning fact")
        return jsonify({
            "response": random_fact,
            "glitch": True
        })

    try:
        user = get_or_create_user(user_id)
        user_history = user.to_dict()
        
        system_prompt = get_system_prompt(user_history)       
        print(f"\n📚 Using memory context from {user.conversation_count} previous conversations")
        print(f"\n🔄 Building conversation context...")
        
        messages = [{"role": "system", "content": system_prompt}]

      
        for msg in user.recent_chat_history:
            messages.append({
                "role": msg["role"],
                "content": msg["message"]
            })

        messages.append({"role": "user", "content": user_input})
        
        print(f"📤 Sending to GPT-3.5-turbo with {len(messages)} messages in context")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        ai_response = response.choices[0].message.content
        print(f"\n📥 Response from Lisbeth: '{ai_response[:80]}...'")

        print("\n" + "="*70)
        print("💾 UPDATING MEMORY")
        print("="*70)
        
        update_user_profile(user_id, user_input)
        update_topic_summaries(user_id, user_input, ai_response)
        add_to_chat_history(user_id, "user", user_input)
        add_to_chat_history(user_id, "assistant", ai_response)
        
        
        user.conversation_count += 1
        user.last_updated = datetime.now()
        db.session.commit()
        
        print(f"\n✅ All memory updated successfully")
        print(f"📊 Total conversations: {user.conversation_count}")
        print("="*70 + "\n")

        return jsonify({
            "response": ai_response,
        })
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("="*70 + "\n")
        return jsonify({"error": str(e)}), 500



@app.route('/check-password', methods=['POST'])
def check_password_endpoint():
    """Check password strength"""
    try:
        password = request.json.get('password', '')
        if not password:
            return jsonify({"error": "Password required"}), 400
        print(f"\n🔐 PASSWORD STRENGTH CHECK")
        result = analyze_password_strength(password)
        print(f"   Score: {result['score']}/100")
        print(f"   Strength: {result['strength']}")
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ ERROR in check_password_endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/check-email', methods=['POST'])
def check_email_endpoint():
    """Check if email was pwned in data breaches"""
    try:
        email = request.json.get('email', '')
        if not email:
            return jsonify({"error": "Email required"}), 400
        print(f"\n📧 EMAIL PWNED CHECK")
        result = check_email_pwned(email)
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Count: {result.get('count', 0)}")
        if result.get('count', 0) > 0:
            print(f"   Breaches: {', '.join(result.get('breaches', []))}")
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ ERROR in check_email_endpoint: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/security-news', methods=['GET'])
def security_news():
    try:
        print(f"\n 🥷🏽💻 FETCHING SECURITY NEWS")
        result = get_security_news()
        print(f"   Found: {result['count']} stories")
        print(f"   Message: {result['message']}")
        return jsonify(result)
    except Exception as e:
        print(f"❌ ERROR in security_news: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/surveillance', methods=['GET'])
def surveillance():
    """Get a random surveillance camera link"""
    try:
        print(f"\n👁️ SURVEILLANCE FEED REQUESTED")
        result = get_surveillance_camera()
        return jsonify(result)
    except Exception as e:
        print(f"❌ ERROR in surveillance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/user-memory/<user_id>', methods=['GET'])
def get_memory(user_id):
    """Get full user memory"""
    user = UserMemory.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"message": "No memory found for this user"}), 404
    
    memory = user.to_dict()
    return jsonify({
        "profile": memory['user_profile'],
        "topics": memory['topic_summaries'],
        "chat_history": memory['recent_chat_history'],
        "conversation_count": memory['conversation_count']
    })


@app.route('/clear-memory/<user_id>', methods=['DELETE'])
def clear_memory(user_id):
    """Clear all user memory"""
    user = UserMemory.query.filter_by(user_id=user_id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        print(f"\n🗑️ Memory cleared for user {user_id}\n")
        return jsonify({"message": f"Memory cleared for user {user_id}"})
    return jsonify({"message": "User not found"}), 404


if __name__ == '__main__':
    import os
    print("\n" + "="*70)
    print("🗄️  INITIALIZING DATABASE")
    print("="*70)
    with app.app_context():
        print(f"📍 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()
        print("✅ Database tables created/verified")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📊 Tables in database: {tables}")
    print("="*70 + "\n")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)  