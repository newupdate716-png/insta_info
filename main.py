from flask import Flask, jsonify, request
import requests
import random
import time
import uuid

app = Flask(__name__)

# ------------------------------------------------------------
# প্রিমিয়াম কনফিগারেশন: আপনার sessionid এখানে দিন।
# ডাইনামিক কুকি জেনারেটরের কারণে এটি এখন অনেক বেশি শক্তিশালী কাজ করবে।
# ------------------------------------------------------------
INSTAGRAM_COOKIES = {
    "sessionid": "YOUR_SESSION_ID_HERE", # আপনার আসল সেশন আইডি দিন
}

def generate_uuid():
    return str(uuid.uuid4())

def get_premium_public_proxies():
    """অনলাইন থেকে হাই-স্পিড এবং এলিট লেভেলের পাবলিক প্রক্সি স্ক্র্যাপ করার প্রিমিয়াম মেথড"""
    proxies = []
    sources = [
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=yes&anonymity=elite",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
    ]
    
    # যেকোনো একটি সোর্স থেকে রেন্ডমলি প্রক্সি তুলে নেওয়া
    try:
        url = random.choice(sources)
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            raw_proxies = response.text.strip().split("\n")
            for p in raw_proxies:
                p = p.strip()
                if p and ":" in p:
                    proxies.append(p)
    except Exception:
        pass

    # ব্যাকআপ সলিড প্রক্সি লিস্ট (যদি অনলাইন সোর্স সাময়িক ডাউন থাকে)
    if not proxies:
        proxies = [
            "38.154.227.167:5868",
            "185.199.229.156:7492",
            "45.8.105.234:80",
            "198.199.86.11:80",
            "143.198.225.178:80"
        ]
    return proxies

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "").lower()
    proxy_pool = get_premium_public_proxies()
    
    # প্রিমিয়াম অ্যান্ড্রোয়েড অ্যাপ ইউজার-এজেন্ট রোটেশন
    android_user_agents = [
        "Instagram 319.0.0.36.107 Android (33/13; 440dpi; 1080x2260; Xiaomi/Redmi; Redmi Note 12 Pro; ruby; qcom; en_US; 571629851)",
        "Instagram 315.0.0.28.104 Android (31/11; 480dpi; 1080x2400; samsung; SM-G998B; o1s; exynos2100; en_GB; 560378418)",
        "Instagram 311.0.0.32.118 Android (32/12; 420dpi; 1080x2340; OnePlus; CPH2449; OP552BL1; qcom; en_US; 549320872)"
    ]

    # সর্বোচ্চ ৫ বার ট্রাই করবে প্রক্সি ও সেশন রোটেট করে
    for attempt in range(5):
        session = requests.Session()
        ua = random.choice(android_user_agents)
        
        # ডাইনামিক ডিভাইস ও সেশন ট্র্যাকিং টোকেন জেনারেট
        device_id = f"android-{generate_uuid()[:16]}"
        uuid_val = generate_uuid()
        phone_id = generate_uuid()

        # বেস কুকি সেটআপ (ইনস্টাগ্রাম সার্ভারকে ট্রাস্ট করানোর জন্য)
        session.cookies.update({
            "mid": generate_uuid()[:12],
            "ig_did": generate_uuid().upper(),
            "csrftoken": generate_uuid()[:32],
        })
        
        # আপনার আসল সেশন আইডি থাকলে সেটা পুশ হবে
        if INSTAGRAM_COOKIES["sessionid"] != "YOUR_SESSION_ID_HERE":
            session.cookies.update({"sessionid": INSTAGRAM_COOKIES["sessionid"]})

        # অফিসিয়াল ইনস্টাগ্রাম এন্ড্রয়েড এপিআই স্ট্রাকচার হেডার
        headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "936619743392459", # Instagram Web/Android Client App ID
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "X-IG-Capabilities": "36r/0g==",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Device-ID": device_id,
            "X-MID": session.cookies.get("mid"),
            "Referer": f"https://www.instagram.com/{username}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive"
        }

        # এপিআই এন্ডপয়েন্ট
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        # প্রক্সি সিলেকশন
        chosen_proxy = random.choice(proxy_pool) if proxy_pool else None
        proxies = {
            "http": f"http://{chosen_proxy}",
            "https": f"http://{chosen_proxy}"
        } if chosen_proxy else None

        try:
            # ইনস্টাগ্রামের অ্যান্টি-বট এড়াতে র্যান্ডমাইজড হিউম্যান ডিলে (৪ থেকে ৭ সেকেন্ড)
            time.sleep(random.uniform(4.0, 7.0))
            
            response = session.get(api_url, headers=headers, proxies=proxies, timeout=15)
            
            if response.status_code == 200:
                res_json = response.json()
                if "data" in res_json and res_json["data"].get("user"):
                    return res_json  # ১০০% সফল রেসপন্স
            
            # যদি এই প্রক্সিটি রেট লিমিট খায় বা ব্লক হয়
            if response.status_code in [429, 403]:
                print(f"[Attempt {attempt+1}] Rate limited with proxy {chosen_proxy}. Retrying with another...")
                time.sleep(3) # পরবর্তী প্রক্সিতে যাওয়ার আগে ছোট ব্রেক
                continue
                
            if response.status_code == 404:
                return {"error": "user_not_found"}
                
        except Exception as e:
            # কানেকশন ড্রপ করলে পরবর্তী প্রক্সিতে শিফট করবে
            continue

    # সব চেষ্টা ব্যর্থ হলে এই সেফ রেসপন্স দেবে
    return {
        "error": "rate_limited", 
        "msg": "Instagram firewall is hyper-active. Please update your sessionid cookie or try after 5 minutes."
    }

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "version": "Premium v3.0 (Anti-Block)",
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

        # পোস্ট প্রসেসিং লুপ
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
