# ------------------------------------------------------------
# Instagram Info API — Credit: Anmol (@FOREVER_HIDDEN)
# Premium Version for Vercel Deployment
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import random

app = Flask(__name__)

def get_premium_headers(username):
    # র্যান্ডম ইউজার এজেন্ট দিলে ব্লক হওয়ার চান্স কমে
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ]
    
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "x-ig-app-id": "936619743392459",  # Standard Instagram Web App ID
        "x-ig-www-claim": "0",
        "x-requested-with": "XMLHttpRequest",
        "x-asbd-id": "129477",
        "Referer": f"https://www.instagram.com/{username}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

def fetch_instagram_profile(username):
    # এই URL টি বর্তমানে সবচেয়ে বেশি কার্যকর
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    session = requests.Session()
    try:
        response = session.get(
            url, 
            headers=get_premium_headers(username), 
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"error": "Rate Limited", "message": "Instagram blocked this request temporarily. Try again later or use a proxy."}
        else:
            return {"error": "Failed to fetch", "status": response.status_code}
            
    except Exception as e:
        return {"error": "Exception occurred", "details": str(e)}

@app.route("/")
def health_check():
    return jsonify({"status": "Online", "credit": "Anmol (@FOREVER_HIDDEN)"})

@app.route("/api/insta=<username>")
def insta_info(username):
    # সরাসরি ইউজারনেম ক্লিন করা
    username = username.strip()
    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 200 # এরর হলেও রেসপন্স দিবে যাতে আপনি বুঝতে পারেন

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "User not found or data structure mismatch"}), 404

        # প্রিমিয়াম ডাটা ফরম্যাট
        response_data = {
            "status": "success",
            "credit": "Anmol (@FOREVER_HIDDEN)",
            "profile": {
                "id": user.get("id"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "is_private": user.get("is_private"),
                "is_verified": user.get("is_verified"),
                "biography": user.get("biography"),
                "external_url": user.get("external_url"),
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
                "profile_pic_hd": user.get("profile_pic_url_hd")
            },
            "recent_posts": []
        }

        # পোস্ট লুপ
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges[:10]:
            node = edge.get("node", {})
            response_data["recent_posts"].append({
                "id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "display_url": node.get("display_url"),
                "is_video": node.get("is_video"),
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "caption": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "")
            })
            
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": "Parsing error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
