# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# Premium Quality - Full Data Fetching Version
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random

app = Flask(__name__)

def get_premium_headers(username):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "x-ig-app-id": "936619743392459",
        "x-asbd-id": "129477",
        "x-requested-with": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{username}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

def fetch_instagram_profile(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    session = requests.Session()
    try:
        response = session.get(url, headers=get_premium_headers(username), timeout=15)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"error": "Rate Limited", "message": "Instagram blocked temporary. Use Proxy."}
        else:
            return {"error": "Failed to fetch", "status": response.status_code}
    except Exception as e:
        return {"error": "Exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({"status": "Active", "dev": "SB-SAKIB", "usage": "/api/insta=username"})

@app.route("/api/insta=<username>")
def insta_info(username):
    username = username.strip().replace("@", "")
    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "User not found or data structure mismatch"}), 404

        # সর্বোচ্চ ডিটেলস ডাটা স্ট্রাকচার
        response_data = {
            "status": "success",
            "credit": "SB-SAKIB (@sakib01994)",
            "profile_data": {
                "id": user.get("id"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "biography": user.get("biography"),
                "bio_links": user.get("bio_links", []),
                "is_private": user.get("is_private"),
                "is_verified": user.get("is_verified"),
                "profile_pic_hd": user.get("profile_pic_url_hd"),
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
                "category_name": user.get("category_name"),
                "is_business_account": user.get("is_business_account"),
                "is_professional_account": user.get("is_professional_account"),
                "pronouns": user.get("pronouns"),
                "fbid": user.get("fbid"),
            },
            "recent_posts": []
        }

        # পোস্টের আরও বিস্তারিত ডাটা আনা হচ্ছে
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            caption_text = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""
            
            response_data["recent_posts"].append({
                "post_id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "display_url": node.get("display_url"),
                "is_video": node.get("is_video"),
                "video_url": node.get("video_url") if node.get("is_video") else None,
                "video_view_count": node.get("video_view_count") if node.get("is_video") else 0,
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "caption": caption_text,
                "timestamp": node.get("taken_at_timestamp"),
                "location": node.get("location"),
                "owner_id": node.get("owner", {}).get("id")
            })
            
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": "Parsing error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)
