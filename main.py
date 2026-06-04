from flask import Flask, jsonify, request
import requests
import random
import time
import re

app = Flask(__name__)

# ------------------------------------------------------------
# ইন্সট্রাকশন: আপনার ইনস্টাগ্রাম ব্রাউজার থেকে 'sessionid' কুকিটি দিন।
# রেট লিমিট পুরোপুরি এড়াতে অন্তত ১টি সেশন আইডি দেওয়া জরুরি।
# ------------------------------------------------------------
INSTAGRAM_COOKIES = {
    "sessionid": "YOUR_SESSION_ID_HERE",  # এখানে আপনার আসল sessionid দিন (যদি থাকে)
}

# ফ্রি প্রক্সি লিস্ট জেনারেট করার ফাংশন (যা কোড নিজেই অনলাইন থেকে খুঁজে নেবে)
def get_free_proxies():
    proxies = []
    try:
        # পাবলিক প্রক্সি এপিআই থেকে লাইভ প্রক্সি নেওয়া হচ্ছে
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxies = response.text.strip().split("\r\n")
            # ফরম্যাট ঠিক করা
            proxies = [p for p in proxies if ":" in p]
    except Exception:
        pass
    
    # ব্যাকআপ প্রক্সি লিস্ট (যদি উপরের এপিআই কাজ না করে)
    if not proxies:
        proxies = [
            "185.199.229.156:7492",
            "45.8.105.234:80",
            "198.199.86.11:80",
            "159.203.61.169:3128"
        ]
    return proxies

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    
    # উন্নত এবং লেটেস্ট রিয়ালিস্টিক ইউজার এজেন্ট লিস্ট
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
    ]
    
    # অনলাইন থেকে প্রক্সি কালেক্ট করা
    proxy_list = get_free_proxies()
    
    # সর্বোচ্চ ৩ বার চেষ্টা করবে আলাদা আলাদা প্রক্সি দিয়ে
    for attempt in range(3):
        session = requests.Session()
        
        # কুকি সেটআপ
        if INSTAGRAM_COOKIES["sessionid"] != "YOUR_SESSION_ID_HERE":
            session.cookies.update(INSTAGRAM_COOKIES)
            
        ua = random.choice(user_agents)
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        # ইনস্টাগ্রামের বর্তমান সিকিউরিটি বাইপাস করার জন্য ডায়নামিক হেডার
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
            "Connection": "keep-alive"
        }

        # রান্ডম প্রক্সি সিলেক্ট করা
        current_proxy = random.choice(proxy_list) if proxy_list else None
        proxies_dict = None
        if current_proxy:
            proxies_dict = {
                "http": f"http://{current_proxy}",
                "https://": f"http://{current_proxy}"
            }

        try:
            # হিউম্যান বিহেভিয়ার ডিলে (একটু বাড়িয়ে ৩ থেকে ৫ সেকেন্ড করা হয়েছে)
            time.sleep(random.uniform(3.0, 5.0))
            
            # প্রক্সি ও হেডার সহ রিকোয়েস্ট পাঠানো
            response = session.get(api_url, headers=headers, proxies=proxies_dict, timeout=12)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # রেট লিমিট খেলে পরবর্তী লুপে অন্য প্রক্সি চেষ্টা করবে
                continue
            elif response.status_code == 404:
                return {"error": "user_not_found"}
            
        except Exception:
            # প্রক্সি ডেড হলে বা কানেকশন ফেইল করলে পরবর্তী প্রক্সি ট্রাই করবে
            continue

    # যদি সব প্রক্সি ফেইল করে বা রেট লিমিট দেখায়
    return {
        "error": "rate_limited", 
        "msg": "Instagram is strictly rate limiting. Try adding a valid Session ID or wait a few minutes."
    }

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
