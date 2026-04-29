from flask import Flask, jsonify, request
import requests
import time
import random

app = Flask(__name__)

def fetch_instagram_profile(username):
    username = username.strip().replace("@", "")
    
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
    }

    try:
        time.sleep(random.uniform(0.5, 1.2))
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"error": "user_not_found"}
        elif response.status_code == 429:
            return {"error": "rate_limited"}
        else:
            return {"error": f"http_{response.status_code}"}

    except Exception as e:
        return {"error": "exception", "details": str(e)}


@app.route("/")
def home():
    return jsonify({
        "status": "Online",
        "developer": "SB-SAKIB (Fixed Version)",
        "usage": "/api/?username=instagram"
    })


@app.route("/api/")
def insta_info():
    username = request.args.get("username")

    if not username:
        return jsonify({"error": "missing_username"}), 400

    data = fetch_instagram_profile(username)

    if "error" in data:
        return jsonify(data)

    try:
        user = data.get("graphql", {}).get("user")

        if not user:
            return jsonify({"error": "parsing_failed"}), 500

        full_data = {
            "status": "success",
            "profile_info": {
                "user_id": user.get("id"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "verified": user.get("is_verified"),
                "is_private": user.get("is_private"),
                "biography": user.get("biography"),
                "external_url": user.get("external_url"),
                "profile_pic": user.get("profile_pic_url_hd"),
            },
            "statistics": {
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
            },
            "posts": []
        }

        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])

        for edge in edges:
            node = edge.get("node", {})

            full_data["posts"].append({
                "id": node.get("id"),
                "shortcode": node.get("shortcode"),
                "type": "video" if node.get("is_video") else "image",
                "display_url": node.get("display_url"),
                "caption": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", ""),
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "timestamp": node.get("taken_at_timestamp"),
                "views": node.get("video_view_count") if node.get("is_video") else 0
            })

        return jsonify(full_data)

    except Exception as e:
        return jsonify({"error": "processing_error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)