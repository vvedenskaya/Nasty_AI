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
        headers = {'User-Agent': 'WASP-Chatbot/1.0'}
        response = requests.get(url, headers=headers, timeout=5)

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
            return {
                "status": "ERROR",
                "message": f"⚠️ API error: {response.status_code}",
                "found": 0
            }

    except Exception as e:
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

def get_surveillance_camera(last_url=None):
    """Returns a link to a direct MJPEG stream, avoiding the last one used"""
    import random
    # Updated list with very stable public MJPEG streams
    cameras = [
        {"url": "http://61.211.241.239/nphMotionJpeg?Resolution=640x480&Quality=Standard", "type": "mjpeg", "loc": "Tokyo, Japan"},
        {"url": "http://128.10.52.41/mjpg/video.mjpg", "type": "mjpeg", "loc": "Purdue University"},
        {"url": "http://91.190.227.11:80/cgi-bin/faststream.jpg?stream=half&fps=15&rand=15421", "type": "mjpeg", "loc": "Ski Resort"},
        {"url": "http://158.58.130.148/mjpg/video.mjpg", "type": "mjpeg", "loc": "Venice, Italy"},
        {"url": "http://185.10.80.33:8082/mjpg/video.mjpg", "type": "mjpeg", "loc": "Old Town Square"},
        {"url": "http://213.193.89.202/mjpg/video.mjpg", "type": "mjpeg", "loc": "Prague, Czech Republic"},
        {"url": "http://194.218.96.92/mjpg/video.mjpg", "type": "mjpeg", "loc": "Stockholm, Sweden"},
        {"url": "http://195.225.101.106/mjpg/video.mjpg", "type": "mjpeg", "loc": "Swiss Alps"},
        {"url": "http://81.149.56.38:8081/mjpg/video.mjpg", "type": "mjpeg", "loc": "UK Port Feed"},
        {"url": "http://77.106.153.2/mjpg/video.mjpg", "type": "mjpeg", "loc": "European Highway"}
    ]
    
    # Filter out the last seen camera if possible
    available_cameras = [c for c in cameras if c["url"] != last_url]
    if not available_cameras: # Fallback if only 1 camera exists
        available_cameras = cameras
        
    selected = random.choice(available_cameras)
    
    return {
        "status": "success",
        "link": selected["url"],
        "type": selected["type"],
        "location": selected["loc"],
        "message": f"👁️ Accessing surveillance feed... Connection established: {selected['loc']}"
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
        # gbv=1 (no JS version), safe=active, udm=14 (web-only filter for clean results), igu=1 (iframe allowed)
        encoded_query = urllib.parse.quote(dork)
        results.append({
            "platform": platform,
            "url": f"https://www.google.com/search?q={encoded_query}&gbv=1&safe=active&udm=14&igu=1"
        })
        
    return {
        "status": "success",
        "target": query,
        "results": results,
        "message": f"🔍 Generated OSINT dorks for: {query}"
    }