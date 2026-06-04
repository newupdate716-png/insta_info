from flask import Flask, jsonify, request
import requests
import random
import time
import re

app = Flask(__name__)

# ------------------------------------------------------------
# আপনার ল্যাপটপ থেকে প্রাপ্ত ১০০% রিয়াল ও ফ্রেশ কুকি সেটআপ
# ------------------------------------------------------------
INSTAGRAM_COOKIES = {
    "sessionid": "22715817812%3Ae1DRKTGS1Tr65f%3A20%3AAYhGML5_tUzzNvipxxzSFzpg4OfBfvkQ_8Ja6ioqLg",
    "mid": "aiEkjgALAAFQyHoQ_7ohAopWbpPp",
    "ig_did": "208B445A-BCFF-4109-834F-0090422D861E",
    "datr": "jiQhagmH1k9IOMaLokGpkNe_",
    "ds_user_id": "22715817812"
}

def get_instagram_context(username):
    username = username.strip().replace("@", "").lower()
    session = requests.Session()
    
    # আপনার অ্যাকাউন্টের অরিজিনাল সেশন কুকিজ ব্রাউজার থেকে সেশনে পুশ করা হচ্ছে
    session.cookies.update(INSTAGRAM_COOKIES)
    
    # রিয়ালিস্টিক ইউজার এজেন্ট
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    ]
    ua = random.choice(user_agents)
    
    # ফার্স্ট ফেজ: সিএসআরএফ টোকেন লাইভ জেনারেট করার চেষ্টা
    base_url = f"https://www.instagram.com/{username}/"
    try:
        init_res = session.get(base_url, headers={"User-Agent": ua}, timeout=10)
        csrf_match = re.search(r'"csrf_token":"([^"]+)"', init_res.text)
        csrf_token = csrf_match.group(1) if csrf_match else "missing"
    except Exception:
        csrf_token = "missing"

    if csrf_token != "missing":
        session.cookies.update({"csrftoken": csrf_token})
    else:
        session.cookies.update({"csrftoken": "pA7bY7vX8O9z1m2n3q4r5s6t7u8v9w0x"})

    # প্রিমিয়াম ইন্টারনাল মোবাইল-ওয়েব এন্ডপয়েন্ট
    api_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    
    headers = {
        "User-Agent": ua,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-IG-App-ID": "936619743392459", 
        "X-ASBD-ID": "129477",
        "X-IG-WWW-Claim": "hmac.AR3ErBS-2ORcSETu4xRvE9WQMX1F0NJS8NIA055aU6ugANhk", # আপনার পাঠানো লাইভ ক্লেম টোকেন
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": session.cookies.get("csrftoken"),
        "Referer": base_url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Connection": "keep-alive"
    }

    # সেফ ডিলে (ইনস্টাগ্রাম সার্ভার সেফটি)
    time.sleep(random.uniform(1.5, 3.0))

    try:
        response = session.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"error": "rate_limited", "msg": "Instagram is blocking temp requests. Please wait a few minutes."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        else:
            return {"error": f"http_{response.status_code}", "msg": "Request rejected. Check if your account cookie is active."}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "version": "Premium Full-Authorized v5.0",
        "usage": "/api/?username=its_d3vil_king",
        "cookie_status": "Fully_Authorized_Live"
    })

@app.route("/api/")
def insta_info():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "missing_username", "msg": "Please provide a username parameter."}), 400

    data = get_instagram_context(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "parsing_failed", "msg": "User data structural error or account hidden."}), 404

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

        # পোস্ট প্রসেস লুপ
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
