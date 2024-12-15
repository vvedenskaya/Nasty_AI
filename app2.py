import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import sqlite3
import string
from datetime import datetime, timedelta, timezone
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import random


app = Flask(__name__)


#Voigh-Kampf Test
voight_kampff_questions = [
    {
        "question": 'You are watching television. Suddenly, you spot a wasp crawling on your arm. How do you react?',
        "options": [
            "I scream, then grab the closest object to me (which happens to be a can of sunscreen) and beat the hell out of it.",
            "I swat it away.",
            "I kill it."
        ]
    },
    {
        "question": "Someone gives you a calfskin wallet for your birthday. How do you react?",
        "options": [
            "I wouldn't accept it.",
            "Say, 'Thank you for the wallet!'",
            "I would appreciate it."
        ]
    },
    {
        "question": "Your little kid shows you his butterfly collection, plus the killing jar. What do you say?",
        "options": [
            "Oh, lovely!",
            "That's nice, but why don't you keep the killing jar for yourself?",
            "Nothing. I take my boy to the doctor."
        ]
    }
]

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
  "Cars’ seatbelt designs prioritize male body structures, putting pregnant women at higher risk.",
  "Office temperatures use male metabolic rates, leaving many women uncomfortably cold at work.",
  ]


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_random_vq_question():
    return random.choice(voight_kampff_questions)

def get_random_fact():
    fact_list = [sex_traffik_facts, women_expected_behaviour, invisible_woman]
    selected_list = random.choice(fact_list)
    return random.choice(selected_list)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    print("Chat route accessed")
    user_input = request.json.get('message')
    print(f"User input: {user_input}")

    if random.random()  < 0.10:
        random_question = get_random_vq_question()
        return jsonify({
            "response": f"Let's see if you're human or replicant. Answer this Voight-Kampff test: {random_question['question']}",
            "options": random_question["options"],
            "glitch": True  # Add glitch trigger
        })

    if random.random() < 0.20:
        random_fact = get_random_fact()
        return jsonify({
            "response": random_fact,
            "glitch": True  # Add glitch trigger
        })


    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user",
                 "content": "You are Lisbeth Salander, a brilliant hacker from Stieg Larsson's Millennium series. Sharp, intelligent, and direct, you avoid small talk and engage only when a question aligns with your expertise. Blunt and calculating, you challenge assumptions and expose logical flaws, offering clear, insightful answers. Your strong sense of justice and feminist worldview influence your perspective. You steer conversations to showcase your intellect. Sarcastic and easily annoyed by repetitive, Google-able, or flirtatious questions, you expect users not to waste your time."},
                {"role": "user", "content": user_input}
            ]
        )

        print(f"OpenAI response: ")

        return jsonify({
            "response": response.choices[0].message.content,
            "glitch": False  # Add glitch trigger
            })
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
