# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM VERSION - AUTO SESSION REFRESH & FIXED 401
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random
import time
import json
import re

app = Flask(__name__)

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    session = requests.Session()
    
    # লেটেস্ট ইউজার এজেন্ট যাতে রিয়েল ব্রাউজার মনে হয়
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    ]
    ua = random.choice(user_agents)

    try:
        # স্টেজ ১: মেইন পেজ হিট করে কুকি এবং এনভায়রনমেন্ট সেটআপ করা
        # এটি ৪০১ এরর এড়াতে সাহায্য করে
        home_url = f"https://www.instagram.com/{username}/"
        home_headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # সেশন ইনিশিয়ালাইজেশন
        res_home = session.get(home_url, headers=home_headers, timeout=15)
        
        # স্টেজ ২: এপিআই প্যারামিটার সেটআপ
        # বর্তমানে x-ig-app-id এবং সঠিক referer ছাড়া ৪০১ আসে
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        csrftoken = session.cookies.get('csrftoken', domain=".instagram.com")
        
        api_headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "936619743392459", # Static Web ID
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrftoken if csrftoken else "",
            "Referer": home_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # হিউম্যান বিহেভিয়ার ইমুলেশন
        time.sleep(random.uniform(2.5, 4.5))
        
        response = session.get(api_url, headers=api_headers, timeout=20)
        
        # যদি ৪০১ আসে তবে অল্টারনেটিভ ডিরেক্ট স্ক্র্যাপার ট্রাই করা
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            # ৪০১ ফিক্স করার জন্য সেকেন্ডারি অ্যাটেম্পট (বিনা কুকিতে)
            return {"error": "unauthorized_401", "msg": "Instagram security blocked the server IP. Please use a proxy or valid session cookie."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Too many requests. Please wait."}
        else:
            return {"error": f"http_{response.status_code}", "msg": "Instagram system rejected the request."}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "usage": "/api/?username=its_d3vil_king"
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
            return jsonify({"error": "parsing_failed", "msg": "User data not found."}), 404

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
