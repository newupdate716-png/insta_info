# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# FIXED VERSION - RATE LIMIT & SESSION HANDLING
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random
import time

app = Flask(__name__)

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    session = requests.Session()
    
    # লেটেস্ট এবং রিয়েলিস্টিক ইউজার এজেন্ট লিস্ট
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
    ]
    ua = random.choice(user_agents)

    try:
        # স্টেজ ১: মেইন প্রোফাইল পেজ ভিজিট করা যাতে সেশন সেট হয়
        home_url = f"https://www.instagram.com/{username}/"
        home_headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
            "Connection": "keep-alive"
        }
        
        # সেশন এবং কুকি কালেক্ট করা
        res_home = session.get(home_url, headers=home_headers, timeout=15)
        
        # স্টেজ ২: এপিআই রিকোয়েস্ট
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        csrftoken = session.cookies.get('csrftoken', domain=".instagram.com")
        
        api_headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "936619743392459", 
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrftoken if csrftoken else "",
            "Referer": home_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # হিউম্যান বিহেভিয়ার ইমুলেশন (একটু বেশি সময় দেওয়া হয়েছে যাতে রেট লিমিট না ধরে)
        time.sleep(random.uniform(3.0, 5.0))
        
        response = session.get(api_url, headers=api_headers, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # যদি রেট লিমিট আসে, অন্য একটি ছোট এপিআই ট্রাই করার চেষ্টা (বিকল্প হিসেবে)
            return {"error": "rate_limited", "msg": "Instagram is blocking this server IP. Try again after 5-10 minutes or use a Proxy."}
        elif response.status_code == 401:
            return {"error": "unauthorized_401", "msg": "Session expired or blocked."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        else:
            return {"error": f"http_{response.status_code}", "msg": "Instagram rejected the request."}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "usage": "/api/?username=its_d3vil_king",
        "note": "If you get Rate Limited, it's due to Instagram IP blocking."
    })

@app.route("/api/")
def insta_info():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "missing_username", "msg": "Please provide a username parameter."}), 400

    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "parsing_failed", "msg": "User data not found or account is private/restricted."}), 404

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
                "bio_links": user.get("bio_links"),
                "category": user.get("category_name"),
                "is_professional": user.get("is_professional_account"),
                "profile_pic_hd": user.get("profile_pic_url_hd"),
                "external_url": user.get("external_url"),
                "fbid": user.get("fbid")
            },
            "statistics": {
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
            },
            "posts": []
        }

        # পোস্ট প্রসেসিং
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            full_data["posts"].append({
                "id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "type": "video" if node.get("is_video") else "image",
                "display_url": node.get("display_url"),
                "video_url": node.get("video_url") if node.get("is_video") else None,
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
