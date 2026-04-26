# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM ULTRA VERSION - ALL POSSIBLE DATA EXTRACTION
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random
import time

app = Flask(__name__)

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
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
        # বট ডিটেকশন এড়াতে ভেরিয়েবল ডিলে
        time.sleep(random.uniform(1.2, 2.8))
        response = session.get(url, headers=headers, timeout=25)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Instagram IP Blocked. Use Proxy or try after some time."}
        else:
            return {"error": f"http_{response.status_code}", "body": response.text[:200]}
            
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
    # কুয়েরি প্যারামিটার থেকে ইউজারনেম নেওয়া
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "missing_parameter", "msg": "Please provide a username (?username=name)"}), 400

    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "parsing_failed", "raw": data}), 500

        # প্রিমিয়াম লেভেলের ডাটা এক্সট্রাকশন
        full_data = {
            "status": "success",
            "developer": "SB-SAKIB",
            "account_details": {
                "user_id": user.get("id"),
                "fbid": user.get("fbid"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "biography": user.get("biography"),
                "external_url": user.get("external_url"),
                "pronouns": user.get("pronouns"),
                "is_verified": user.get("is_verified"),
                "is_private": user.get("is_private"),
                "is_professional_account": user.get("is_professional_account"),
                "is_business_account": user.get("is_business_account"),
                "category_name": user.get("category_name"),
                "business_category_name": user.get("business_category_name"),
                "is_joined_recently": user.get("is_joined_recently"),
                "has_ar_effects": user.get("has_ar_effects"),
                "has_clips": user.get("has_clips"),
                "has_guides": user.get("has_guides"),
                "has_channel": user.get("has_channel"),
                "profile_pic_url": user.get("profile_pic_url"),
                "profile_pic_url_hd": user.get("profile_pic_url_hd"),
            },
            "statistics": {
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
                "total_igtv_videos": user.get("edge_felix_video_timeline", {}).get("count"),
            },
            "mutual_info": {
                "mutual_followers_count": user.get("edge_mutual_followed_by", {}).get("count", 0),
            },
            "highlights": [
                {"id": h.get("id"), "title": h.get("title")} 
                for h in user.get("highlight_reel_ids", [])
            ],
            "recent_posts": []
        }

        # পোস্টের আরও গভীর ডাটা এক্সট্রাকশন
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            full_data["recent_posts"].append({
                "post_id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "dimensions": node.get("dimensions"),
                "display_url": node.get("display_url"),
                "is_video": node.get("is_video"),
                "video_url": node.get("video_url") if node.get("is_video") else None,
                "video_view_count": node.get("video_view_count") if node.get("is_video") else 0,
                "caption": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", ""),
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "comments_disabled": node.get("comments_disabled"),
                "taken_at": node.get("taken_at_timestamp"),
                "location": node.get("location", {}).get("name") if node.get("location") else None,
                "accessibility_caption": node.get("accessibility_caption")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    # লোকাল রান করার জন্য
    app.run(host='0.0.0.0', port=5000, debug=True)
