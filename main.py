from flask import Flask, jsonify, request
import requests
import random
import time

app = Flask(__name__)

# ------------------------------------------------------------
# ইন্সট্রাকশন: আপনার ইনস্টাগ্রাম ব্রাউজার থেকে 'sessionid' কুকিটি সংগ্রহ করুন।
# Chrome -> Inspect -> Application -> Cookies -> instagram.com -> sessionid
# ------------------------------------------------------------
INSTAGRAM_COOKIES = {
    "sessionid": "YOUR_SESSION_ID_HERE", # এখানে আপনার sessionid দিন
}

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    session = requests.Session()
    
    # কুকি সেশনে সেট করা হচ্ছে (এটিই রেট লিমিট সমাধান করবে)
    if INSTAGRAM_COOKIES["sessionid"] != "YOUR_SESSION_ID_HERE":
        session.cookies.update(INSTAGRAM_COOKIES)

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    ]
    ua = random.choice(user_agents)

    try:
        # স্টেজ ১: প্রোফাইল এপিআই কল (সরাসরি সেশন সহ)
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "936619743392459", 
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        # হিউম্যান বিহেভিয়ার ডিলে
        time.sleep(random.uniform(1.5, 3.0))
        
        response = session.get(api_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Instagram is still rate limiting. Change your Session ID or use a Proxy."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        else:
            return {"error": f"http_{response.status_code}", "msg": "Instagram rejected the request. Cookie might be expired."}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "usage": "/api/?username=its_d3vil_king",
        "cookie_status": "Set" if INSTAGRAM_COOKIES["sessionid"] != "YOUR_SESSION_ID_HERE" else "Missing"
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
            return jsonify({"error": "parsing_failed", "msg": "User data not found. Check if the account exists."}), 404

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
                "is_professional": user.get("is_professional_account"),
                "profile_pic_hd": user.get("profile_pic_url_hd"),
                "external_url": user.get("external_url")
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
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
