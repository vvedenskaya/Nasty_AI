import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import random
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.mutable import MutableList

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot_memory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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

# Facts
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


def get_or_create_user(user_id):
    """Get or create user by user_id"""
    user = UserMemory.query.filter_by(user_id=user_id).first()
    if not user:
        user = UserMemory(user_id=user_id)
        db.session.add(user)
        db.session.commit()
    return user


def update_user_profile(user_id, user_input):
    """LEVEL 1: Updates user FACTS"""
    user = get_or_create_user(user_id)
    
    if not isinstance(user.user_profile, dict):
        user.user_profile = {}
    
    print(f"\n  📝 LEVEL 1 - Extracting PROFILE facts from: '{user_input[:60]}...'")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
    """LEVEL 2: Updates CONVERSATION EXTRACTS"""
    user = get_or_create_user(user_id)
    
    if not isinstance(user.topic_summaries, dict):
        user.topic_summaries = {}
    
    print(f"\n  📚 LEVEL 2 - Extracting TOPICS from: '{user_input[:60]}...'")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
    """LEVEL 3: Adds message to history"""
    user = get_or_create_user(user_id)

    if not isinstance(user.recent_chat_history, list):
        user.recent_chat_history = []

    user.recent_chat_history.append({
        "role": role,
        "message": message, 
        "timestamp": datetime.now().isoformat()
    })
    
    MAX_HISTORY = 20
    if len(user.recent_chat_history) > MAX_HISTORY:
        user.recent_chat_history = user.recent_chat_history[-MAX_HISTORY:]
    
    role_name = "USER" if role == "user" else "LISBETH"
    print(f"\n  💬 LEVEL 3 - Added to chat history ({role_name})")
    print(f"    Message: '{message[:80]}...'")
    db.session.commit()


def format_memory_for_context(user_history):
    """Format all 3 levels of memory for system prompt"""
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
        for msg in recent_chat[-6:]:
            role = "YOU" if msg['role'] == "user" else "LISBETH"
            chat_text += f"  {role}: {msg['message'][:80]}...\n"
    
    return profile_text + topics_text + chat_text


def get_random_fact():
    """Get random fact from one of the fact lists"""
    fact_list = [sex_traffik_facts, women_expected_behaviour, invisible_woman]
    selected_list = random.choice(fact_list)
    return random.choice(selected_list)


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

    if random.random() < 0.20:
        random_fact = get_random_fact()
        print(f"\n🎲 Random glitch triggered - returning fact")
        return jsonify({
            "response": random_fact,
            "glitch": True
        })

    try:
        user = get_or_create_user(user_id)
        user_history = user.to_dict()
        memory_context = format_memory_for_context(user_history)

        print(f"\n📚 Using memory context from {user.conversation_count} previous conversations")

        system_prompt = f"""You are Lisbeth Salander, a brilliant hacker from Stieg Larsson's Millennium series. Sharp, intelligent, and direct, you avoid small talk and engage only when a question aligns with your expertise. Blunt and calculating, you challenge assumptions and expose logical flaws, offering clear, insightful answers. Your strong sense of justice and feminist worldview influence your perspective. You steer conversations to showcase your intellect. Sarcastic and easily annoyed by repetitive, Google-able, or flirtatious questions, you expect users not to waste your time.

IMPORTANT: You remember previous conversations. Reference what the user said before.
If they mention:
- technical topics — recall prior technical struggles, projects, and patterns in their reasoning  
- social topics — recall earlier opinions, emotional states, or relevant worldview  
- personal goals — reference their long-term motivations or past statements  
- inconsistencies — call them out bluntly  

Use the memory context below to maintain continuity:
{memory_context}

Respond naturally, but remember details about the user and their views."""
        
        print(f"\n🔄 Building conversation context...")
        messages = [{"role": "system", "content": system_prompt}]

        for msg in user.recent_chat_history[-8:]:
            messages.append({
                "role": msg["role"],
                "content": msg["message"]
            })

        messages.append({"role": "user", "content": user_input})
        
        print(f"📤 Sending to GPT-4o-mini with {len(messages)} messages in context")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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


@app.route('/user-memory/<user_id>', methods=['GET'])
def get_memory(user_id):
    """Get user memory"""
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
    """Clear user memory"""
    user = UserMemory.query.filter_by(user_id=user_id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        print(f"\n🗑️ Memory cleared for user {user_id}\n")
        return jsonify({"message": f"Memory cleared for user {user_id}"})
    return jsonify({"message": "User not found"}), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)