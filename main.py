#!/usr/bin/env python3
from flask import Flask, jsonify, request
import requests
import random
import time
import json
import re
import hashlib
import sys
from collections import Counter

app = Flask(__name__)

# --- Obfuscated Source Check Mechanism (Original Logic Preserved 100%) ---
exec(__import__('base64').b64decode("U09VUkNFID0gInRlbGVncmFtLmRvZy9jb2Rlc2J5TW8iClNPVVJDRV9IQVNIID0gaGFzaGxpYi5zaGEyNTYoU09VUkNFLmVuY29kZSgpKS5oZXhkaWdlc3QoKQoKZGVmIGNoZWNrX3NvdXJjZSgpOgogICAgY3VycmVudCA9IGhhc2hsaWIuc2hhMjU2KFNPVVJDRS5lbmNvZGUoKSkuaGV4ZGlnZXN0KCkKICAgIGlmIGN1cnJlbnQgIT0gU09VUkNFX0hBU0g6CiAgICAgICAgc3lzLmV4aXQoMCkKCmNoZWNrX3NvdXJjZSgp"))

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

class InstagramPremiumOSINT:
    def __init__(self):
        self.cookies = INSTAGRAM_COOKIES
        self.query_hash = "b9a3255c600b57d8760c3c540da38c62"
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    def extract_username(self, text):
        text = text.strip()
        match = re.search(r'(?:https?://)?(?:www\.)?instagram\.com/([^/?]+)', text)
        if match:
            return match.group(1).lower()
        return text.lstrip('@').lower()

    def fetch_profile(self, username):
        session = requests.Session()
        session.cookies.update(self.cookies)
        
        graphql_url = f"https://www.instagram.com/graphql/query/?query_hash={self.query_hash}&variables={{\"+username+\":\"{username}\",\"child_comment_count\":3,\"fetch_comment_setting_count\":0,\"fetch_has_comment_fields\":false,\"has_threaded_comments\":false}}"
        
        headers = {
            "User-Agent": self.ua,
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
                # ফলব্যাক মেকানিজম
                fallback_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
                fb_res = session.get(fallback_url, headers=headers, timeout=10)
                if fb_res.status_code == 200:
                    return fb_res.json()
                return {"error": "rate_limited", "msg": "Instagram is strictly monitoring this IP."}
            elif response.status_code == 404:
                return {"error": "user_not_found"}
            else:
                return {"error": f"http_{response.status_code}", "msg": "Instagram firewall blocking request structure."}
        except Exception as e:
            return {"error": "exception", "details": str(e)}

    def safe_get(self, obj, *keys, default="N/A"):
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, default)
            else:
                return default
        return obj if obj is not None else default

    def analyze_bio(self, bio):
        if not bio:
            return {"emails": [], "urls": [], "hashtags": [], "mentions": []}
        return {
            "emails": re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', bio),
            "urls": re.findall(r'https?://[^\s]+', bio),
            "hashtags": re.findall(r'#\w+', bio),
            "mentions": re.findall(r'@\w+', bio)
        }

    def process_report(self, data, limit=20):
        user = data.get("data", {}).get("user") or data.get("graphql", {}).get("user")
        if not user:
            return {"error": "parsing_failed", "msg": "User data not found or account is private."}

        bio = self.safe_get(user, 'biography', default="")
        bio_info = self.analyze_bio(bio)

        media = user.get('edge_owner_to_timeline_media', {})
        edges = media.get('edges', [])
        
        posts = []
        locations = Counter()
        all_hashtags = Counter()
        all_mentions = Counter()
        tagged_users = Counter()
        
        total_likes = 0
        total_comments = 0
        total_views = 0
        video_count = 0

        for edge in edges[:limit]:
            node = edge.get('node', {})
            if not node:
                continue
            
            shortcode = self.safe_get(node, 'shortcode')
            is_video = node.get('is_video', False)
            
            # ক্যাপশন এনালাইসিস
            caption = self.safe_get(node, 'edge_media_to_caption', 'edges', 0, 'node', 'text', default="")
            if caption:
                for h in re.findall(r'#\w+', caption):
                    all_hashtags[h] += 1
                for m in re.findall(r'@\w+', caption):
                    all_mentions[m] += 1

            # লোকেশন ট্র্যাকিং
            loc_name = self.safe_get(node, 'location', 'name', default=None)
            if loc_name:
                locations[loc_name] += 1

            # ট্যাগড ইউজার ট্র্যাকিং
            post_tagged = []
            tagged = node.get('edge_media_to_tagged_user', {}).get('edges', [])
            for tag in tagged:
                u = tag.get('node', {}).get('user', {}).get('username')
                if u:
                    tagged_users[u] += 1
                    post_tagged.append(u)

            # কো-অথর ট্র্যাকিং
            post_coauthors = []
            coauthors = node.get('coauthor_producers', [])
            for author in coauthors:
                if author.get('username'):
                    post_coauthors.append(author.get('username'))

            # মিউজিক ট্র্যাকিং
            music_info = node.get('clips_music_attribution_info')
            music = None
            if music_info and music_info.get('artist_name') and music_info.get('song_name'):
                music = f"{music_info.get('artist_name')} - {music_info.get('song_name')}"

            # লাইক ও কমেন্ট স্ট্যাটিস্টিকস
            likes = self.safe_get(node, 'edge_liked_by', 'count', default=0)
            if likes == 0 or likes == "N/A":
                likes = self.safe_get(node, 'edge_media_preview_like', 'count', default=0)
            
            comments = self.safe_get(node, 'edge_media_to_comment', 'count', default=0)
            views = node.get('video_view_count', 0) if is_video else 0

            total_likes += int(likes) if str(likes).isdigit() else 0
            total_comments += int(comments) if str(comments).isdigit() else 0
            
            if is_video:
                total_views += int(views) if str(views).isdigit() else 0
                video_count += 1

            posts.append({
                "id": node.get("id"),
                "shortcode": shortcode,
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "type": "video" if is_video else "image",
                "product_type": self.safe_get(node, 'product_type'),
                "timestamp": node.get('taken_at_timestamp'),
                "likes": likes,
                "comments": comments,
                "caption": caption,
                "display_url": self.safe_get(node, 'display_url'),
                "thumbnail": self.safe_get(node, 'thumbnail_src'),
                "location": loc_name,
                "tagged": post_tagged,
                "coauthors": post_coauthors,
                "music": music,
                "video_url": node.get('video_url'),
                "video_view_count": views if is_video else None,
                "video_duration": node.get('video_duration') if is_video else None
            })

        # কমপ্লিট প্রিমিয়াম আউটপুট স্ট্রাকচার অবিকল রাখা হয়েছে
        return {
            "status": "success",
            "developer": "SB-SAKIB",
            "version": "Premium GraphQL v6.0",
            "profile_info": {
                "user_id": self.safe_get(user, 'id'),
                "username": self.safe_get(user, 'username'),
                "full_name": self.safe_get(user, 'full_name'),
                "eimu_id": self.safe_get(user, 'eimu_id'),
                "fbid": self.safe_get(user, 'fbid'),
                "verified": self.safe_get(user, 'is_verified', default=False),
                "is_private": self.safe_get(user, 'is_private', default=False),
                "is_business": self.safe_get(user, 'is_business_account', default=False),
                "is_professional": self.safe_get(user, 'is_professional_account', default=False),
                "is_joined_recently": self.safe_get(user, 'is_joined_recently', default=False),
                "highlight_reel_count": self.safe_get(user, 'highlight_reel_count', default=0),
                "pronouns": self.safe_get(user, 'pronouns', default=[]),
                "biography": bio,
                "bio_analysis": bio_info,
                "category": self.safe_get(user, 'category_name'),
                "profile_pic_hd": self.safe_get(user, 'profile_pic_url_hd') or self.safe_get(user, 'profile_pic_url'),
                "external_url": self.safe_get(user, 'external_url'),
                "business_details": {
                    "business_contact_method": self.safe_get(user, 'business_contact_method'),
                    "business_email": self.safe_get(user, 'business_email'),
                    "business_phone_number": self.safe_get(user, 'business_phone_number')
                }
            },
            "statistics": {
                "followers": self.safe_get(user, 'edge_followed_by', 'count', default=0),
                "following": self.safe_get(user, 'edge_follow', 'count', default=0),
                "total_posts": self.safe_get(media, 'count', default=0),
            },
            "posts": posts,
            "aggregates": {
                "engagement": {
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "avg_likes_per_post": total_likes // len(posts) if posts else 0,
                    "avg_comments_per_post": total_comments // len(posts) if posts else 0,
                    "total_video_views": total_views,
                    "avg_views_per_video": total_views // video_count if video_count > 0 else 0
                },
                "locations_visited": dict(locations),
                "most_used_hashtags": dict(all_hashtags),
                "most_mentioned_users": dict(all_mentions),
                "users_tagged_in_posts": dict(tagged_users)
            }
        }


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
    username_param = request.args.get('username')
    
    if not username_param:
        return jsonify({"error": "missing_username", "msg": "Please provide a username parameter."}), 400

    osint = InstagramPremiumOSINT()
    clean_username = osint.extract_username(username_param)
    
    # সেশন ডেটা স্ক্র্যাপ ইঞ্জিন রান
    raw_data = osint.fetch_profile(clean_username)
    
    if "error" in raw_data:
        return jsonify(raw_data), 200

    # অ্যাডভান্সড রিপোর্ট প্রোসেস জেনারেটর
    final_report = osint.process_report(raw_data, limit=20)
    return jsonify(final_report)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
