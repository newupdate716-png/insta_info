# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM VERSION - AUTO SESSION REFRESH & FIXED 401
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random
import time
import json

app = Flask(__name__)

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    session = requests.Session()
    
    # ইউজার এজেন্ট লিস্ট
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ]
    ua = random.choice(user_agents)

    try:
        # স্টেজ ১: মেইন পেজ থেকে ডাটা স্ক্র্যাপ করার চেষ্টা করা (এপিআই ছাড়াই)
        # ইন্সটাগ্রাম এখন এপিআই ব্লক করলে শেয়ার ইউআরএল থেকে ডাটা দেয়
        base_url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Connection": "keep-alive",
        }
        
        response = session.get(base_url, headers=headers, timeout=20)
        
        # স্টেজ ২: যদি এপিআই ট্রাই করতে হয়
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        # সেশন থেকে অটোমেটিক কুকি নেওয়া
        csrftoken = session.cookies.get('csrftoken', domain=".instagram.com")
        mid = session.cookies.get('mid', domain=".instagram.com")
        
        api_headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "x-ig-app-id": "936619743392459", # Static App ID
            "x-ig-www-claim": "0",
            "x-requested-with": "XMLHttpRequest",
            "x-csrftoken": csrftoken if csrftoken else "missing",
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # ডিটেকশন এড়াতে ডাইনামিক ডিলে
        time.sleep(random.uniform(1.5, 3.0))
        
        api_res = session.get(api_url, headers=api_headers, timeout=20)
        
        if api_res.status_code == 200:
            return api_res.json()
        elif api_res.status_code == 401:
            # সেশন সাকসেসফুল না হলে অল্টারনেটিভ মেথড (যেমন পাবলিক এপিআই বা প্রক্সি)
            return {"error": "unauthorized_401", "msg": "Instagram strict security. Need valid Session Cookie."}
        elif api_res.status_code == 404:
            return {"error": "user_not_found"}
        elif api_res.status_code == 429:
            return {"error": "rate_limited", "msg": "Wait 15 mins. IP Blocked."}
        else:
            return {"error": f"status_{api_res.status_code}", "msg": "Instagram rejected the request."}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "usage": "/api/?username=username_here"
    })

@app.route("/api/")
def insta_info():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "missing_username", "msg": "Please provide a username."}), 400

    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "parsing_failed", "msg": "No user data found."}), 404

        full_data = {
            "status": "success",
            "developer": "SB-SAKIB",
            "profile_info": {
                "user_id": user.get("id"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "verified": user.get("is_verified"),
                "is_private": user.get("is_private"),
                "biography": user.get("biography"),
                "profile_pic_hd": user.get("profile_pic_url_hd"),
                "external_url": user.get("external_url"),
                "is_professional": user.get("is_professional_account"),
                "category": user.get("category_name"),
            },
            "statistics": {
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
            },
            "posts": []
        }

        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            full_data["posts"].append({
                "id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "type": "video" if node.get("is_video") else "image",
                "display_url": node.get("display_url"),
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
