from flask import Flask, jsonify, request
import requests
import random
import time

app = Flask(__name__)

# ------------------------------------------------------------
# আপনার ল্যাপটপ থেকে প্রাপ্ত ১০০% লাইভ কুকি ও সেশন ডেটা
# ------------------------------------------------------------
INSTAGRAM_COOKIES = {
    "sessionid": "22715817812%3Ae1DRKTGS1Tr65f%3A20%3AAYhGML5_tUzzNvipxxzSFzpg4OfBfvkQ_8Ja6ioqLg",
    "mid": "aiEkjgALAAFQyHoQ_7ohAopWbpPp",
    "ig_did": "208B445A-BCFF-4109-834F-0090422D861E",
    "datr": "jiQhagmH1k9IOMaLokGpkNe_",
    "ds_user_id": "22715817812"
}

def fetch_instagram_via_graphql(username):
    username = username.strip().replace("@", "").lower()
    session = requests.Session()
    
    # ব্রাউজার সেশন কুকি লোড
    session.cookies.update(INSTAGRAM_COOKIES)
    
    # রিয়ালিস্টিক ব্রাউজার হেডার
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    
    # স্টেপ ১: ইনস্টাগ্রামের অফিশিয়াল GraphQL মোবাইল কুয়েরি এন্ডপয়েন্ট
    # এই query_hash টি সরাসরি প্রোফাইলের যাবতীয় ডেটা ও লেটেস্ট পোস্ট স্ক্র্যাপ করে আনে
    QUERY_HASH = "b9a3255c600b57d8760c3c540da38c62" 
    
    graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={QUERY_HASH}&variables={{\"+username+\":\"{username}\",\"child_comment_count\":3,\"fetch_comment_setting_count\":0,\"fetch_has_comment_fields\":false,\"has_threaded_comments\":false}}"
    
    headers = {
        "User-Agent": ua,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-IG-App-ID": "936619743392459",
        "X-IG-WWW-Claim": "hmac.AR3ErBS-2ORcSETu4xRvE9WQMX1F0NJS8NIA055aU6ugANhk",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{username}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Connection": "keep-alive"
    }

    # অ্যান্টি-বট ডিটেকশন এড়াতে হিউম্যান ডিলে
    time.sleep(random.uniform(1.0, 2.5))

    try:
        response = session.get(graphql_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # যদি আইপি ব্লক থাকে তবে অল্টারনেটিভ ডিরেক্ট এন্ডপয়েন্টে ব্যাকআপ ট্রাই করবে
            fallback_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
            fb_res = session.get(fallback_url, headers=headers, timeout=10)
            if fb_res.status_code == 200:
                return fb_res.json()
            return {"error": "rate_limited", "msg": "Instagram is strictly monitoring this IP. Try changing your network/VPN."}
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        else:
            return {"error": f"http_{response.status_code}", "msg": "Instagram firewall blocking the request structure."}
            
    except Exception as e:
        return {"error": "exception", "details": str(e)}

@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB",
        "version": "Premium GraphQL v6.0",
        "usage": "/api/?username=its_d3vil_king",
        "cookie_status": "Live_Authorized"
    })

@app.route("/api/")
def insta_info():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "missing_username", "msg": "Please provide a username parameter."}), 400

    data = fetch_instagram_via_graphql(username)
    
    if "error" in data:
        return jsonify(data), 200

    try:
        # GraphQL অথবা Fallback ডাটা পার্সিং হ্যান্ডলার
        user = data.get("data", {}).get("user") or data.get("graphql", {}).get("user")
        
        if not user:
            return jsonify({"error": "parsing_failed", "msg": "User data not found or account is private."}), 404

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
                "profile_pic_hd": user.get("profile_pic_url_hd") or user.get("profile_pic_url"),
                "external_url": user.get("external_url")
            },
            "statistics": {
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
            },
            "posts": []
        }

        # পোস্ট ডেটা প্রসেসিং
        timeline = user.get("edge_owner_to_timeline_media", {})
        edges = timeline.get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            full_data["posts"].append({
                "id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "type": "video" if node.get("is_video") else "image",
                "display_url": node.get("display_url"),
                "likes": node.get("edge_liked_by", {}).get("count") or node.get("edge_media_preview_like", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp")
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
