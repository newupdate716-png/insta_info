# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM VERSION - ALL DATA & HIGH SUCCESS RATE
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random
import time

app = Flask(__name__)

def fetch_instagram_profile(username):
    # ইউজারনেম ক্লিন করা
    username = username.strip().replace("@", "")
    
    # Instagram এন্ডপয়েন্ট
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    # প্রিমিয়াম হেডার্স যা ব্রাউজারকে নকল করে
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "0",
        "x-requested-with": "XMLHttpRequest",
        "x-asbd-id": "129477",
        "Referer": f"https://www.instagram.com/{username}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    session = requests.Session()
    
    try:
        # রিকোয়েস্ট পাঠানোর আগে ২ সেকেন্ড অপেক্ষা করা (বট ডিটেকশন এড়াতে)
        time.sleep(random.uniform(1.0, 2.5))
        
        response = session.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Instagram IP Blocked. Use Proxy or try after 10 mins."}
        else:
            return {"error": f"http_{response.status_code}", "body": response.text[:200]}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "dev": "SB-SAKIB",
        "endpoint": "/api/insta=shanta"
    })

@app.route("/api/insta=<username>")
def insta_info(username):
    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "parsing_failed", "raw": data}), 500

        # সর্বোচ্চ ডাটা এক্সট্রাকশন (A to Z)
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
                "category": user.get("category_name"),
                "business_category": user.get("business_category_name"),
                "professional": user.get("is_professional_account"),
                "business": user.get("is_business_account"),
                "profile_pic_hd": user.get("profile_pic_url_hd"),
                "external_url": user.get("external_url"),
                "pronouns": user.get("pronouns"),
                "fbid": user.get("fbid"),
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

        # পোস্টের বিস্তারিত তথ্য
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            full_data["posts"].append({
                "id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "type": "video" if node.get("is_video") else "image",
                "display_url": node.get("display_url"),
                "video_url": node.get("video_url") if node.get("is_video") else None,
                "caption": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", ""),
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp"),
                "location": node.get("location", {}).get("name") if node.get("location") else None,
                "views": node.get("video_view_count") if node.get("is_video") else 0
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
