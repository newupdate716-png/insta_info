from flask import Flask, jsonify, request
import requests
import random
import time
import json
import re

app = Flask(__name__)

# ============================================
# মাল্টিপল এন্ডপয়েন্ট সাপোর্ট (যদি একটায় রেট লিমিট আসে)
# ============================================

# ফ্রি Instagram API এন্ডপয়েন্ট লিস্ট (একটায় না কাজ করলে অন্যটা ব্যবহার হবে)
FREE_APIS = [
    "https://instagram-api.vercel.app/api/info?username={}",
    "https://insta-api.koyeb.app/api/info?username={}",
    "https://instagram-profile-downloader-download-instagram-profile.vercel.app/api/info?username={}",
    "https://insta-stalker-api.vercel.app/api/info?username={}"
]

def fetch_from_multiple_sources(username):
    """একাধিক সোর্স থেকে ডাটা আনার চেষ্টা করে"""
    
    for api_url_template in FREE_APIS:
        try:
            api_url = api_url_template.format(username)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and data.get('username'):
                    return {"success": True, "data": data, "source": api_url}
        except:
            continue
    
    return {"success": False}

def fetch_from_instagram_direct(username):
    """সরাসরি Instagram থেকে fetch (প্রথম চেষ্টা)"""
    
    # ব্যাকরণিক ভুল মার্জিন
    username = username.strip().replace("@", "")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    try:
        url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
        
        # স্লো ডাউন (রেট লিমিট কমানোর জন্য)
        time.sleep(random.uniform(0.5, 1.0))
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Rate limit from Instagram. Using backup..."}
        else:
            return {"error": f"http_{response.status_code}"}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

def extract_public_data(username):
    """পাবলিক পেজ থেকে ডাটা এক্সট্রাক্ট"""
    
    try:
        url = f'https://www.instagram.com/{username}/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # JSON ডাটা খোঁজা
            pattern = r'window\._sharedData\s*=\s*({.*?});'
            match = re.search(pattern, response.text)
            
            if match:
                data = json.loads(match.group(1))
                user_data = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {})
                
                if user_data:
                    return format_user_data(user_data)
        
        return None
    except:
        return None

def format_user_data(user):
    """ডাটা ফরম্যাট"""
    return {
        "status": "success",
        "developer": "SB-SAKIB",
        "profile_info": {
            "user_id": user.get("id"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "verified": user.get("is_verified", False),
            "is_private": user.get("is_private", False),
            "biography": user.get("biography", ""),
            "profile_pic_hd": user.get("profile_pic_url_hd", user.get("profile_pic_url")),
            "external_url": user.get("external_url", "")
        },
        "statistics": {
            "followers": user.get("edge_followed_by", {}).get("count", 0),
            "following": user.get("edge_follow", {}).get("count", 0),
            "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
        },
        "posts": []
    }

@app.route('/')
def home():
    return jsonify({
        "status": "Online ✅",
        "developer": "SB-SAKIB",
        "message": "Instagram API - Working without sessionid",
        "endpoints": {
            "/api?username=USERNAME": "Get Instagram profile data",
            "/health": "Check server status"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/api')
def get_instagram_data():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "Username required", "example": "/api?username=instagram"}), 400
    
    # স্টেপ ১: প্রথমে সরাসরি Instagram চেষ্টা
    result = fetch_from_instagram_direct(username)
    
    # স্টেপ ২: রেট লিমিট আসলে ব্যাকআপ API ব্যবহার
    if result.get("error") == "rate_limited":
        backup = fetch_from_multiple_sources(username)
        
        if backup["success"]:
            return jsonify({
                "status": "success",
                "source": "backup_api",
                "data": backup["data"]
            })
        
        # স্টেপ ৩: পাবলিক ডাটা এক্সট্রাক্ট
        public_data = extract_public_data(username)
        if public_data:
            return jsonify(public_data)
        
        # স্টেপ ৪: সব ব্যর্থ হলে
        return jsonify({
            "error": "rate_limited",
            "message": "Instagram is rate limiting. Please try after 2-3 minutes.",
            "solution": "Use VPN or wait 5 minutes before retry",
            "developer": "SB-SAKIB"
        }), 429
    
    # সফল হলে
    if result and "data" in result:
        user = result["data"]["user"]
        return jsonify(format_user_data(user))
    
    if result and "user" in result:
        return jsonify(format_user_data(result["user"]))
    
    return jsonify({
        "error": "not_found",
        "message": f"Username '{username}' not found or account is private",
        "developer": "SB-SAKIB"
    }), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)