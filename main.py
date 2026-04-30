# ------------------------------------------------------------
# Instagram Info API — Credit: SB-SAKIB (@sakib01994)
# PREMIUM VERSION - AUTO REFRESHING SESSION
# ------------------------------------------------------------

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import random
import time

app = Flask(__name__)
CORS(app)

class InstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ]

    def refresh_session(self, username):
        """অটোমেটিক সেশন এবং সিএসআরএফ টোকেন জেনারেট করা"""
        ua = random.choice(self.user_agents)
        self.session.cookies.clear()
        
        # ১. মেইন পেজ ভিজিট করে কুকি নেওয়া
        init_url = f"https://www.instagram.com/{username}/"
        headers = {"User-Agent": ua}
        
        try:
            res = self.session.get(init_url, headers=headers, timeout=15)
            csrftoken = self.session.cookies.get('csrftoken')
            return csrftoken, ua
        except:
            return None, ua

    def get_profile(self, username):
        username = username.strip().replace("@", "")
        token, ua = self.refresh_session(username)
        
        # টোকেন না পেলে ডিফল্ট রিকোয়েস্ট ট্রাই করবে
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "x-ig-app-id": "936619743392459",
            "x-ig-www-claim": "0",
            "x-requested-with": "XMLHttpRequest",
            "x-asbd-id": "129477",
            "x-csrftoken": token if token else "missing",
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        try:
            # হিউম্যান লাইক ডিলে
            time.sleep(random.uniform(2, 4))
            response = self.session.get(api_url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                return {"error": "unauthorized_401", "msg": "Instagram security updated. Please use a static Session Cookie for 100% stability."}
            elif response.status_code == 429:
                return {"error": "rate_limited", "msg": "IP Blocked by Instagram. Wait 10-15 mins."}
            else:
                return {"error": f"status_{response.status_code}", "msg": "Unexpected error from Instagram."}
        except Exception as e:
            return {"error": "exception", "details": str(e)}

scraper = InstagramScraper()

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "api": "/api/?username=its_d3vil_king"
    })

@app.route("/api/")
def insta_info():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "missing_username"}), 400

    data = scraper.get_profile(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "parsing_failed"}), 404

        return jsonify({
            "status": "success",
            "developer": "SB-SAKIB",
            "profile": {
                "id": user.get("id"),
                "username": user.get("username"),
                "name": user.get("full_name"),
                "bio": user.get("biography"),
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
                "profile_pic": user.get("profile_pic_url_hd"),
                "is_verified": user.get("is_verified"),
                "is_private": user.get("is_private")
            },
            "recent_posts": [
                {
                    "id": p["node"]["id"],
                    "shortcode": p["node"]["shortcode"],
                    "url": p["node"]["display_url"],
                    "likes": p["node"]["edge_liked_by"]["count"]
                } for p in user.get("edge_owner_to_timeline_media", {}).get("edges", [])[:5]
            ]
        })
    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
