import re
import hashlib
import requests
from functools import wraps
import os
import feedparser

def get_security_news():
    """Fetch cybersecurity news from working RSS feeds"""
    feeds = [
        "https://www.bleepingcomputer.com/feed/",  
        "https://feeds.arstechnica.com/arstechnica/security",
        "https://securitynews.sonicwall.com/feed",
        "https://krebsonsecurity.com/feed/",
        "https://threatpost.com/feed/"
    ]
    
    news = []
    keywords = [
        'security', 'hacked', 'vulnerability', 'exploit', 'breach', 
        'malware', 'crypto', 'ransomware', 'attack', 'cyber', 'threat',
        'hack', 'leaked', 'zero-day', 'patch', 'virus'
    ]
    
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url, request_headers=headers)
            
            for entry in feed.entries[:15]:
                title = entry.get('title', '').lower()
                
                
                if any(kw in title for kw in keywords):
                    news.append({
                        "title": entry.get('title', 'N/A'),
                        "link": entry.get('link', '#'),
                        "source": feed.feed.get('title', 'Unknown'),
                        "published": entry.get('published', 'N/A')[:10]
                    })
                    
                    if len(news) >= 10:
                        break
        except Exception as e:
            print(f"⚠️ Error parsing {feed_url}: {e}")
            continue
    
    return {
        "status": "success",
        "count": len(news),
        "news": news[:10],
        "message": f"📰 Latest cybersecurity news ({len(news)} stories)"
    }


def analyze_password_strength(password: str):
    score = 0
    feedback = []
    
    
    if len(password) >= 16:
        score += 25
    elif len(password) >= 12:
        score += 20
    elif len(password) >= 8:
        score += 10
    else:
        feedback.append("❌ Password too short (min 12 chars)")
    

    if re.search(r'[a-z]', password):
        score += 15
    else:
        feedback.append("❌ No lowercase letters")
    
    if re.search(r'[A-Z]', password):
        score += 15
    else:
        feedback.append("❌ No uppercase letters")
    
    if re.search(r'[0-9]', password):
        score += 15
    else:
        feedback.append("❌ No numbers")
    
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        score += 20
    else:
        feedback.append("❌ No special characters")
    

    if re.search(r'(.)\1{2,}', password):
        score -= 10
        feedback.append("⚠️ Repeating characters detected")
    

    common_patterns = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if any(pattern in password.lower() for pattern in common_patterns):
        score -= 15
        feedback.append("⚠️ Contains common patterns")
    
    score = max(0, min(100, score))
    
    if score >= 80:
        strength = "STRONG"
        emoji = "✅"
    elif score >= 60:
        strength = "MEDIUM"
        emoji = "⚠️"
    else:
        strength = "WEAK"
        emoji = "🚨"
    
    return {
        "score": score,
        "strength": strength,
        "emoji": emoji,
        "feedback": feedback if feedback else ["✅ Good password!"],
        "message": f"{emoji} Password strength: {strength} ({score}/100)"
    }


def check_password_breach(password: str) -> dict:
    """
    Check if a password has been leaked in data breaches (FREE API, no key needed).
    """
    try:
        sha1_password = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_password[:5]
        suffix = sha1_password[5:]

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            for line in response.text.split('\r\n'):
                if ':' in line:
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        return {
                            "status": "COMPROMISED",
                            "found": int(count),
                            "message": f"🚨 THIS PASSWORD WAS FOUND IN {count} BREACHES! CHANGE IT IMMEDIATELY."
                        }

            return {
                "status": "SAFE",
                "found": 0,
                "message": "✅ Good news! This password wasn't found in any known breaches."
            }
        else:
            print(f"   [check_password_breach] API ERROR: {response.status_code}")
            return {
                "status": "ERROR",
                "message": f"⚠️ API error: {response.status_code}",
                "found": 0
            }

    except Exception as e:
        print(f"   [check_password_breach] EXCEPTION: {e}")
        return {
            "status": "ERROR",
            "message": f"⚠️ Error: {str(e)}",
            "found": 0
        }

# @tool
# def check_url_phishing(url: str) -> dict:
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        if not re.match(r'https?://[^\s/$.?#].[^\s]*$', url, re.I):
            return {"status": "INVALID", "message": "❌ Not a valid URL"}

        google_api_key = os.environ.get("GOOGLE_SAFE_BROWSING_KEY", "")
        if google_api_key:
            google_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
            payload = {
                "client": {"clientId": "Lisbeth", "clientVersion": "1.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }

            response = requests.post(
                google_url + f"?key={google_api_key}",
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                if "matches" in result and result["matches"]:

                    threats = [m["threatType"] for m in result["matches"]]
                    return {
                        "status": "DANGEROUS",
                        "threats": threats,
                        "message": f"🚨 DANGEROUS URL: {', '.join(threats)}"
                    }

        urlhaus_url = "https://urlhaus-api.abuse.ch/v1/url/"
        params = {"url": url}
        response = requests.get(urlhaus_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("query_status") == "ok":
                threat_level = data.get("threat", "")
                if threat_level:
                    return {
                        "status": "DANGEROUS",
                        "threat": threat_level,
                        "message": f"🚨 URLhaus marked as: {threat_level}"
                    }
                return {
                    "status": "SAFE",
                    "message": "✅ URL looks safe",
                    "url": url
                }
            else:
                return {
                    "status": "UNKNOWN",
                    "message": "⚠️ Couldn't verify with API",
                    "url": url
                }
        else:
            return {
                "status": "UNKNOWN",
                "message": "⚠️ Couldn't check with URLhaus",
                "url": url
            }

    except Exception as e:

        return {"error": f"Error: {str(e)}"}

def get_surveillance_camera():
    """Returns a link to a random security camera stream"""
    import random
    cameras = [
        "http://www.insecam.org/en/view/365340/",
        "http://www.insecam.org/en/view/466158/",
        "http://www.insecam.org/en/view/1010039/",
        "http://www.insecam.org/en/view/880541/",
        "http://www.insecam.org/en/view/996756/",
        "http://www.insecam.org/en/view/521291/",
        "http://www.insecam.org/en/view/435359/",
        "http://www.insecam.org/en/view/891134/",
        "http://www.insecam.org/en/view/370430/"
    ]
    
    selected = random.choice(cameras)
    
    return {
        "status": "success",
        "link": selected,
        "message": f"👁️ Accessing surveillance feed... Found one: {selected}"
    }

def google_dorking_search(target: str):
    """
    Generates Google Dorking links for OSINT.
    """
    import urllib.parse
    
    # Clean up the target
    query = target.strip()
    
    # Dorks
    dorks = {
        "Facebook": f'site:facebook.com "{query}"',
        "LinkedIn": f'site:linkedin.com/in/ "{query}"',
        "Instagram": f'site:instagram.com "{query}"',
        "Twitter/X": f'site:twitter.com "{query}"',
        "General OSINT": f'"{query}" (intext:"@gmail.com" OR intext:"@yahoo.com" OR intext:"@outlook.com")',
        "Public Documents": f'site:docs.google.com "{query}"'
    }
    
    results = []
    for platform, dork in dorks.items():
        encoded_query = urllib.parse.quote(dork)
        results.append({
            "platform": platform,
            "url": f"https://www.google.com/search?q={encoded_query}"
        })
        
    return {
        "status": "success",
        "target": query,
        "results": results,
        "message": f"🔍 Generated OSINT dorks for: {query}"
    }