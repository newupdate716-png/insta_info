# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM VERSION - FIXED 401 UNAUTHORIZED ISSUE
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random
import time
import re

app = Flask(__name__)

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    session = requests.Session()
    
    # Instagram-এর মেইন পেজ ভিজিট করে কুকি এবং CSRF টোকেন কালেক্ট করা
    base_url = "https://www.instagram.com/"
    init_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    try:
        # Initial call to get cookies
        response_init = session.get(base_url, headers=init_headers, timeout=15)
        csrftoken = response_init.cookies.get('csrftoken') or "missing"
        
        # API URL
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        # Updated Headers with CSRF and valid ID
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "x-ig-app-id": "936619743392459", # Standard Public Web ID
            "x-fb-ls-reg": "0",
            "x-asbd-id": "129477",
            "x-ig-www-claim": "0",
            "x-requested-with": "XMLHttpRequest",
            "x-csrftoken": csrftoken,
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # Rate limit এড়াতে সামান্য ডিলে
        time.sleep(random.uniform(1.0, 2.0))
        
        response = session.get(api_url, headers=api_headers, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {"error": "unauthorized_401", "msg": "Instagram requires valid login cookies or session."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Instagram IP Blocked. Use Proxy or try after 10 mins."}
        else:
            return {"error": f"http_{response.status_code}", "msg": response.text[:100]}
            
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
            return jsonify({"error": "parsing_failed", "msg": "User data not found. This account might be restricted or private."}), 404

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
                "business_category": user.get("business_category_name"),
                "is_professional": user.get("is_professional_account"),
                "is_business": user.get("is_business_account"),
                "profile_pic_hd": user.get("profile_pic_url_hd"),
                "external_url": user.get("external_url"),
                "pronouns": user.get("pronouns"),
                "fbid": user.get("fbid"),
                "has_guides": user.get("has_guides"),
                "is_joined_recently": user.get("is_joined_recently"),
            },
            "statistics": {
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
            },
            "highlights": [
                {"id": h.get("id"), "title": h.get("title")} 
                for h in user.get("highlight_reel_ids", [])
            ],
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
                "video_url": node.get("video_url") if node.get("is_video") else None,
                "caption": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "") if node.get("edge_media_to_caption", {}).get("edges") else "",
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp"),
                "location": node.get("node", {}).get("location", {}).get("name") if node.get("location") else None,
                "views": node.get("video_view_count") if node.get("is_video") else 0,
                "accessibility_caption": node.get("accessibility_caption")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
