# ------------------------------------------------------------
# Instagram Info API — Credit: Anmol (@FOREVER_HIDDEN)
# Purpose : Vercel Optimized Instagram Scraper
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

def fetch_instagram_profile(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "x-ig-app-id": "936619743392459",
        "x-asbd-id": "129477",
        "Referer": f"https://www.instagram.com/{username}/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"error": "Failed to fetch", "status": resp.status_code}
    except Exception as e:
        return {"error": str(e)}

@app.route("/api/insta=<username>")
def insta_info(username):
    data = fetch_instagram_profile(username)
    
    if "error" in data:
        return jsonify(data), 400

    try:
        user = data.get("data", {}).get("user")
        if not user:
            return jsonify({"error": "User not found or private access restricted"}), 404

        out = {
            "credit": "Anmol (@FOREVER_HIDDEN)",
            "id": user.get("id"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "biography": user.get("biography"),
            "followers": user.get("edge_followed_by", {}).get("count"),
            "following": user.get("edge_follow", {}).get("count"),
            "profile_pic": user.get("profile_pic_url_hd"),
            "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
            "recent_posts": []
        }

        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
        for edge in edges[:5]:
            node = edge.get("node", {})
            out["recent_posts"].append({
                "shortcode": node.get("shortcode"),
                "display_url": node.get("display_url"),
                "likes": node.get("edge_liked_by", {}).get("count")
            })
        
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": "Parsing error", "details": str(e)}), 500

# Vercel-এর জন্য এটি প্রয়োজন নেই তবে লোকাল টেস্টিং এর জন্য রাখা হলো
if __name__ == "__main__":
    app.run(debug=True)