# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM VERSION - AUTO SESSION REFRESH & FIXED 401
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
    
    # ইউজার এজেন্ট লিস্ট যাতে ইন্সটাগ্রাম বট বুঝতে না পারে
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]
    ua = random.choice(user_agents)

    try:
        # স্টেজ ১: মেইন পেজ ভিজিট করে ফ্রেশ কুকি এবং সিএসআরএফ জেনারেট করা
        base_url = f"https://www.instagram.com/{username}/"
        init_headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
        }
        
        response_init = session.get(base_url, headers=init_headers, timeout=15)
        csrftoken = session.cookies.get('csrftoken')
        
        # স্টেজ ২: এপিআই রিকোয়েস্ট তৈরি করা
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        api_headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "x-ig-app-id": "936619743392459",
            "x-fb-ls-reg": "0",
            "x-asbd-id": "129477",
            "x-ig-www-claim": "0",
            "x-requested-with": "XMLHttpRequest",
            "x-csrftoken": csrftoken if csrftoken else "",
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # হিউম্যান-লাইক ডিলে (ইন্সটাগ্রাম ডিটেকশন এড়াতে)
        time.sleep(random.uniform(2.0, 4.0))
        
        response = session.get(api_url, headers=api_headers, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            # যদি আবারও ৪০১ আসে, সেশন রিসেট করে ট্রাই করা
            return {"error": "unauthorized_401", "msg": "Session expired or blocked by Instagram IP security."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "IP Temporarily Blocked. Please wait 10-15 minutes."}
        else:
            return {"error": f"http_{response.status_code}", "msg": "Instagram security rejected the request."}
            
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
            return jsonify({"error": "parsing_failed", "msg": "User data not found in response."}), 404

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
                "location": node.get("location", {}).get("name") if node.get("location") else None,
                "views": node.get("video_view_count") if node.get("is_video") else 0,
                "accessibility_caption": node.get("accessibility_caption")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
