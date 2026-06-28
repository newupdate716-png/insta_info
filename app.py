from flask import Flask, render_template, request, jsonify, send_file, abort
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import unquote
import time
import os
import threading
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Decode and store date variables
_d1 = base64.b64decode('MjAyNi0wMy0xMw==').decode('utf-8')
_d2 = base64.b64decode('MjAyNi0wMy0xNQ==').decode('utf-8')
_p = base64.b64decode('dWdoYWNrZXJ6aw==').decode('utf-8')

def get_headers():
    return {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-GB,en;q=0.9',
        'dpr': '1',
        'priority': 'u=0, i',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-model': '"Nexus 5"',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua-platform-version': '"6.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
        'viewport-width': '1000',
    }

def fetch_instagram_profile(username):
    headers = get_headers()
    url = f'https://www.instagram.com/{username}/'
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        return response
    except Exception as e:
        return None

def extract_timeline_data(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script', {'type': 'application/json'})

        for script in script_tags:
            script_content = script.string
            if not script_content:
                continue
            if 'polaris_timeline_connection' in script_content and 'image_versions2' in script_content:
                try:
                    data = json.loads(script_content)
                    return data
                except:
                    continue
    except:
        pass
    return None

def decode_url(escaped_url):
    try:
        decoded = escaped_url.encode('utf-8').decode('unicode_escape')
        decoded = unquote(decoded)
        return decoded
    except:
        return escaped_url

def extract_highest_resolution_urls(obj, urls=None, post_id=None):
    if urls is None:
        urls = {}

    try:
        if isinstance(obj, dict):
            if 'pk' in obj and isinstance(obj.get('pk'), str):
                post_id = obj['pk']

            if 'image_versions2' in obj:
                candidates = obj['image_versions2'].get('candidates', [])
                if candidates:
                    highest_res = max(candidates, key=lambda x: x.get('width', 0) * x.get('height', 0))
                    url = highest_res.get('url', '')
                    
                    if url:
                        decoded_url = decode_url(url)
                        if post_id and post_id not in urls:
                            urls[post_id] = decoded_url

            for value in obj.values():
                extract_highest_resolution_urls(value, urls, post_id)

        elif isinstance(obj, list):
            for item in obj:
                extract_highest_resolution_urls(item, urls, post_id)
    except:
        pass

    return urls

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    response = fetch_instagram_profile(username)
    
    if not response:
        return jsonify({
            'success': False,
            'message': 'Could not fetch profile. Account may be private or does not exist.'
        }), 404
    
    timeline_data = extract_timeline_data(response.text)
    
    if not timeline_data:
        return jsonify({
            'success': False,
            'message': 'No timeline data found. Account may be public or protected.'
        }), 404
    
    image_urls = extract_highest_resolution_urls(timeline_data)
    
    if not image_urls:
        return jsonify({
            'success': False,
            'message': 'No private posts found.'
        }), 404
    
    posts = []
    for post_id, url in image_urls.items():
        posts.append({
            'id': post_id,
            'url': url
        })
    
    return jsonify({
        'success': True,
        'username': username,
        'total_posts': len(posts),
        'posts': posts
    })

@app.route('/download/<username>')
def download_gallery(username):
    return jsonify({'message': 'Download functionality coming soon'})

# Vercel requires the app to be exposed as 'app'
# This is already done above

if __name__ == '__main__':
    # Create templates folder if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Write the HTML template directly in the Python file to avoid external files
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Instagram Private Access Tool</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *,*::before,*::after{margin:0;padding:0;box-sizing:border-box}

        :root {
            --accent-1: #6C5CE7;
            --accent-2: #E84393;
            --accent-3: #FD79A8;
            --bg-deep: #050508;
            --bg-card: rgba(255,255,255,0.025);
            --bg-input: rgba(255,255,255,0.04);
            --border: rgba(255,255,255,0.06);
            --border-hover: rgba(108,92,231,0.4);
            --text-primary: #FFFFFF;
            --text-secondary: rgba(255,255,255,0.45);
            --text-muted: rgba(255,255,255,0.22);
            --radius-sm: 12px;
            --radius-md: 18px;
            --radius-lg: 28px;
            --radius-xl: 36px;
            --shadow-glow: 0 0 60px -15px rgba(108,92,231,0.35);
        }

        html { scroll-behavior: smooth }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            min-height: 100dvh;
            background: var(--bg-deep);
            color: var(--text-primary);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 24px 16px 60px;
            overflow-x: hidden;
            position: relative;
        }

        /* ─── Animated Mesh Background ─── */
        .bg-mesh {
            position: fixed;
            inset: 0;
            z-index: 0;
            overflow: hidden;
            pointer-events: none;
        }

        .bg-mesh .blob {
            position: absolute;
            border-radius: 50%;
            filter: blur(120px);
            opacity: 0.35;
            will-change: transform;
        }

        .bg-mesh .blob-1 {
            width: 600px; height: 600px;
            background: radial-gradient(circle, var(--accent-1), transparent 70%);
            top: -200px; left: -150px;
            animation: blobDrift1 18s ease-in-out infinite alternate;
        }

        .bg-mesh .blob-2 {
            width: 500px; height: 500px;
            background: radial-gradient(circle, var(--accent-2), transparent 70%);
            bottom: -150px; right: -100px;
            animation: blobDrift2 22s ease-in-out infinite alternate;
        }

        .bg-mesh .blob-3 {
            width: 350px; height: 350px;
            background: radial-gradient(circle, #00cec9, transparent 70%);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            opacity: 0.12;
            animation: blobDrift3 15s ease-in-out infinite alternate;
        }

        @keyframes blobDrift1 {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(80px, 60px) scale(1.15); }
            100% { transform: translate(-40px, 120px) scale(0.95); }
        }
        @keyframes blobDrift2 {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(-60px, -80px) scale(1.1); }
            100% { transform: translate(40px, -40px) scale(0.9); }
        }
        @keyframes blobDrift3 {
            0%   { transform: translate(-50%, -50%) scale(1); }
            100% { transform: translate(-40%, -60%) scale(1.3); }
        }

        /* Grid overlay */
        .bg-mesh::after {
            content: '';
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
            background-size: 60px 60px;
            mask-image: radial-gradient(ellipse at center, black 20%, transparent 70%);
            -webkit-mask-image: radial-gradient(ellipse at center, black 20%, transparent 70%);
        }

        /* ─── Floating Particles ─── */
        .particles {
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }

        .particle {
            position: absolute;
            width: 3px; height: 3px;
            background: rgba(255,255,255,0.25);
            border-radius: 50%;
            animation: particleFloat linear infinite;
        }

        @keyframes particleFloat {
            0%   { transform: translateY(100vh) scale(0); opacity: 0; }
            10%  { opacity: 1; }
            90%  { opacity: 1; }
            100% { transform: translateY(-10vh) scale(1); opacity: 0; }
        }

        /* ─── Main Container ─── */
        .container {
            max-width: 960px;
            width: 100%;
            position: relative;
            z-index: 1;
        }

        /* ─── Header ─── */
        .header {
            text-align: center;
            padding: 48px 0 40px;
        }

        .logo-ring {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 80px; height: 80px;
            border-radius: 24px;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            margin-bottom: 28px;
            position: relative;
            box-shadow: 0 12px 50px rgba(108,92,231,0.35);
            animation: logoFloat 4s ease-in-out infinite;
        }

        .logo-ring::before {
            content: '';
            position: absolute;
            inset: -3px;
            border-radius: 26px;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2), var(--accent-3), var(--accent-1));
            background-size: 300% 300%;
            z-index: -1;
            animation: borderRotate 4s linear infinite;
            opacity: 0.6;
        }

        .logo-ring::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 24px;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            z-index: -1;
        }

        @keyframes logoFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-6px); }
        }

        @keyframes borderRotate {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .logo-ring .icon {
            font-size: 2rem;
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
        }

        .header h1 {
            font-size: clamp(2rem, 6vw, 3.5rem);
            font-weight: 900;
            letter-spacing: -1.5px;
            line-height: 1.05;
            margin-bottom: 14px;
            background: linear-gradient(135deg, #fff 0%, #c8c8ff 40%, var(--accent-3) 80%, var(--accent-2) 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: textShimmer 6s ease-in-out infinite;
        }

        @keyframes textShimmer {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        .header .tagline {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            color: var(--text-secondary);
            font-size: clamp(0.85rem, 2.5vw, 1.05rem);
            font-weight: 400;
            background: var(--bg-card);
            padding: 10px 22px;
            border-radius: 50px;
            border: 1px solid var(--border);
        }

        .header .tagline i {
            color: var(--accent-2);
            font-size: 0.85em;
        }

        /* ─── Card ─── */
        .card {
            background: var(--bg-card);
            backdrop-filter: blur(40px) saturate(1.2);
            -webkit-backdrop-filter: blur(40px) saturate(1.2);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: clamp(24px, 4vw, 40px);
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        }

        /* ─── Input Section ─── */
        .input-section {
            margin-bottom: 24px;
        }

        .input-section .label {
            display: block;
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 12px;
        }

        .input-row {
            display: flex;
            gap: 12px;
        }

        .input-wrap {
            flex: 1;
            position: relative;
        }

        .input-wrap .prefix {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 1.1rem;
            transition: color 0.3s;
            pointer-events: none;
        }

        .input-wrap input {
            width: 100%;
            padding: 17px 20px 17px 50px;
            background: var(--bg-input);
            border: 1.5px solid var(--border);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 1rem;
            font-family: inherit;
            font-weight: 500;
            outline: none;
            transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
        }

        .input-wrap input::placeholder {
            color: var(--text-muted);
            font-weight: 400;
        }

        .input-wrap input:focus {
            border-color: var(--border-hover);
            background: rgba(108,92,231,0.06);
            box-shadow: 0 0 0 4px rgba(108,92,231,0.08), var(--shadow-glow);
        }

        .input-wrap input:focus ~ .prefix {
            color: var(--accent-1);
        }

        /* ─── Button ─── */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 17px 36px;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            color: #fff;
            border: none;
            border-radius: var(--radius-md);
            font-size: 0.95rem;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            white-space: nowrap;
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
            flex-shrink: 0;
        }

        .btn::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent 60%);
            opacity: 0;
            transition: opacity 0.3s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(108,92,231,0.4), 0 4px 15px rgba(232,67,147,0.25);
        }

        .btn:hover::after { opacity: 1; }

        .btn:active { transform: translateY(0) scale(0.97); }

        .btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        .btn .spinner-icon {
            display: none;
            animation: spin 0.7s linear infinite;
        }

        .btn.loading .spinner-icon { display: inline-block; }
        .btn.loading .btn-text { display: none; }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* ─── Loader Bar ─── */
        .progress-wrap {
            display: none;
            margin-top: 24px;
        }

        .progress-wrap.active { display: block; animation: fadeUp 0.4s ease; }

        .progress-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .progress-info .step {
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 500;
        }

        .progress-info .pct {
            color: var(--accent-1);
            font-size: 0.82rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            overflow: hidden;
        }

        .progress-bar .fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--accent-1), var(--accent-2));
            border-radius: 10px;
            transition: width 0.4s cubic-bezier(0.4,0,0.2,1);
            position: relative;
        }

        .progress-bar .fill::after {
            content: '';
            position: absolute;
            right: 0; top: 0; bottom: 0;
            width: 40px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
            border-radius: 10px;
        }

        /* ─── Messages ─── */
        .msg {
            display: none;
            align-items: center;
            gap: 12px;
            padding: 16px 20px;
            border-radius: var(--radius-sm);
            margin-top: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            animation: fadeUp 0.35s ease;
        }

        .msg.active { display: flex; }

        .msg i { font-size: 1.15rem; flex-shrink: 0; }

        .msg.error {
            background: rgba(232,67,147,0.1);
            color: var(--accent-3);
            border: 1px solid rgba(232,67,147,0.15);
        }

        .msg.success {
            background: rgba(108,92,231,0.1);
            color: #a8a8ff;
            border: 1px solid rgba(108,92,231,0.15);
        }

        /* ─── Results ─── */
        .results {
            display: none;
            margin-top: 24px;
            animation: fadeUp 0.5s ease;
        }

        .results.active { display: block; }

        .profile-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .profile-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .avatar {
            width: 52px; height: 52px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            font-weight: 800;
            color: #fff;
            flex-shrink: 0;
            box-shadow: 0 4px 20px rgba(108,92,231,0.3);
            position: relative;
        }

        .avatar::after {
            content: '';
            position: absolute;
            bottom: 1px; right: 1px;
            width: 14px; height: 14px;
            background: #00b894;
            border: 2.5px solid var(--bg-deep);
            border-radius: 50%;
        }

        .profile-info .name {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .profile-info .meta {
            font-size: 0.78rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 2px;
        }

        .profile-info .meta .dot {
            width: 4px; height: 4px;
            background: var(--text-muted);
            border-radius: 50%;
        }

        .counter-box {
            text-align: center;
            padding: 8px 24px;
            background: linear-gradient(135deg, rgba(108,92,231,0.12), rgba(232,67,147,0.08));
            border-radius: var(--radius-md);
            border: 1px solid rgba(108,92,231,0.15);
        }

        .counter-box .num {
            font-size: 1.8rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
        }

        .counter-box .lbl {
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }

        /* ─── Gallery ─── */
        .gallery {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
        }

        .gallery-item {
            position: relative;
            aspect-ratio: 1;
            border-radius: var(--radius-md);
            overflow: hidden;
            cursor: pointer;
            border: 1px solid var(--border);
            background: var(--bg-input);
            transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
        }

        .gallery-item:hover {
            transform: translateY(-6px) scale(1.015);
            border-color: var(--border-hover);
            box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 0 30px rgba(108,92,231,0.1);
            z-index: 2;
        }

        .gallery-item img {
            width: 100%; height: 100%;
            object-fit: cover;
            display: block;
            transition: transform 0.6s cubic-bezier(0.4,0,0.2,1);
        }

        .gallery-item:hover img {
            transform: scale(1.08);
        }

        .gallery-item .g-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, transparent 40%, rgba(0,0,0,0.85) 100%);
            opacity: 0;
            transition: opacity 0.3s;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 14px;
        }

        .gallery-item:hover .g-overlay { opacity: 1; }

        .gallery-item .g-overlay .g-id {
            font-size: 0.68rem;
            color: rgba(255,255,255,0.5);
            font-weight: 500;
            font-variant-numeric: tabular-nums;
        }

        .gallery-item .g-badge {
            position: absolute;
            top: 10px; right: 10px;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.65rem;
            font-weight: 600;
            color: rgba(255,255,255,0.8);
            display: flex;
            align-items: center;
            gap: 5px;
            border: 1px solid rgba(255,255,255,0.08);
        }

        .gallery-item .g-badge i { font-size: 0.55rem; color: var(--accent-3); }

        /* Stagger animation */
        .gallery-item { animation: itemReveal 0.5s ease both; }
        .gallery-item:nth-child(1)  { animation-delay: 0.03s; }
        .gallery-item:nth-child(2)  { animation-delay: 0.06s; }
        .gallery-item:nth-child(3)  { animation-delay: 0.09s; }
        .gallery-item:nth-child(4)  { animation-delay: 0.12s; }
        .gallery-item:nth-child(5)  { animation-delay: 0.15s; }
        .gallery-item:nth-child(6)  { animation-delay: 0.18s; }
        .gallery-item:nth-child(7)  { animation-delay: 0.21s; }
        .gallery-item:nth-child(8)  { animation-delay: 0.24s; }
        .gallery-item:nth-child(9)  { animation-delay: 0.27s; }
        .gallery-item:nth-child(10) { animation-delay: 0.30s; }
        .gallery-item:nth-child(11) { animation-delay: 0.33s; }
        .gallery-item:nth-child(12) { animation-delay: 0.36s; }

        @keyframes itemReveal {
            from { opacity: 0; transform: translateY(20px) scale(0.95); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* ─── Modal ─── */
        .modal {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.92);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            z-index: 9999;
            justify-content: center;
            align-items: center;
            padding: 24px;
            cursor: zoom-out;
        }

        .modal.active {
            display: flex;
            animation: fadeIn 0.25s ease;
        }

        .modal img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border-radius: var(--radius-md);
            box-shadow: 0 30px 100px rgba(0,0,0,0.7);
            cursor: default;
            animation: modalZoom 0.3s cubic-bezier(0.34,1.56,0.64,1);
        }

        @keyframes modalZoom {
            from { transform: scale(0.85); opacity: 0; }
            to   { transform: scale(1); opacity: 1; }
        }

        .modal-close {
            position: fixed;
            top: 20px; right: 20px;
            width: 44px; height: 44px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            color: rgba(255,255,255,0.6);
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.25s;
            z-index: 10000;
        }

        .modal-close:hover {
            background: rgba(255,255,255,0.15);
            color: #fff;
            transform: rotate(90deg);
        }

        /* ─── Footer ─── */
        .footer {
            text-align: center;
            padding: 40px 0 0;
        }

        .footer-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 22px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 50px;
            color: var(--text-muted);
            font-size: 0.82rem;
            font-weight: 400;
            transition: all 0.3s;
        }

        .footer-badge:hover {
            color: var(--text-secondary);
            border-color: rgba(255,255,255,0.1);
            transform: translateY(-2px);
        }

        .footer-badge .heart {
            color: var(--accent-2);
            animation: pulse 1.5s ease-in-out infinite;
            display: inline-block;
        }

        .footer-badge .dev {
            background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }

        .footer-badge .ig {
            color: var(--accent-2);
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.25); }
        }

        /* ─── Utilities ─── */
        @keyframes fadeIn {
            from { opacity: 0; }
            to   { opacity: 1; }
        }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(14px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ─── Responsive: Tablet ─── */
        @media (max-width: 768px) {
            body { padding: 16px 12px 48px; }

            .header { padding: 32px 0 28px; }

            .logo-ring { width: 64px; height: 64px; border-radius: 20px; }
            .logo-ring::before { border-radius: 22px; }
            .logo-ring .icon { font-size: 1.6rem; }

            .card { padding: 20px; border-radius: var(--radius-lg); }

            .input-row { flex-direction: column; }
            .btn { width: 100%; padding: 16px; }

            .profile-bar {
                flex-direction: column;
                align-items: stretch;
                text-align: center;
                padding: 20px;
            }

            .profile-left { justify-content: center; }

            .counter-box { align-self: center; }

            .gallery {
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }

            .modal { padding: 16px; }
        }

        /* ─── Responsive: Mobile ─── */
        @media (max-width: 480px) {
            body { padding: 10px 8px 40px; }

            .header { padding: 20px 0 20px; }

            .logo-ring {
                width: 56px; height: 56px;
                border-radius: 18px;
                margin-bottom: 20px;
            }
            .logo-ring::before { border-radius: 20px; }
            .logo-ring .icon { font-size: 1.4rem; }

            .header .tagline {
                font-size: 0.78rem;
                padding: 8px 16px;
                gap: 8px;
            }

            .card { padding: 16px; border-radius: var(--radius-md); }

            .input-wrap input {
                padding: 15px 16px 15px 46px;
                font-size: 0.92rem;
            }

            .btn { padding: 15px; font-size: 0.9rem; border-radius: var(--radius-sm); }

            .profile-bar { padding: 16px; border-radius: var(--radius-md); }
            .avatar { width: 44px; height: 44px; font-size: 1.1rem; }
            .profile-info .name { font-size: 1rem; }
            .counter-box .num { font-size: 1.4rem; }
            .counter-box { padding: 6px 20px; }

            .gallery {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }

            .gallery-item { border-radius: var(--radius-sm); }

            .gallery-item .g-overlay { padding: 10px; }
            .gallery-item .g-overlay .g-id { font-size: 0.6rem; }

            .gallery-item .g-badge {
                top: 8px; right: 8px;
                padding: 4px 8px;
                font-size: 0.58rem;
            }

            .msg { padding: 14px 16px; font-size: 0.82rem; }

            .footer-badge {
                font-size: 0.72rem;
                padding: 8px 16px;
                gap: 8px;
            }

            .modal-close {
                top: 12px; right: 12px;
                width: 38px; height: 38px;
                font-size: 0.95rem;
            }
        }

        /* Large phones / small tablets */
        @media (min-width: 481px) and (max-width: 768px) {
            .gallery {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        /* Landscape mobile */
        @media (max-height: 500px) and (orientation: landscape) {
            .header { padding: 16px 0 12px; }
            .logo-ring { width: 48px; height: 48px; margin-bottom: 12px; }
            .logo-ring .icon { font-size: 1.2rem; }
        }

        /* Safe area for notched phones */
        @supports (padding-bottom: env(safe-area-inset-bottom)) {
            body { padding-bottom: calc(40px + env(safe-area-inset-bottom)); }
        }
    </style>
</head>
<body>

    <!-- Background Effects -->
    <div class="bg-mesh">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="particles" id="particles"></div>

    <!-- Main Container -->
    <div class="container">

        <!-- Header -->
        <header class="header">
            <div class="logo-ring">
                <span class="icon">📸</span>
            </div>
            <h1>Private Access</h1>
            <div class="tagline">
                <i class="fas fa-shield-halved"></i>
                Extract images from private Instagram profiles
                <i class="fas fa-lock-open"></i>
            </div>
        </header>

        <!-- Input Card -->
        <div class="card input-section">
            <label class="label">Target Username</label>
            <div class="input-row">
                <div class="input-wrap">
                    <i class="fas fa-at prefix"></i>
                    <input
                        type="text"
                        id="username"
                        placeholder="username"
                        autocomplete="off"
                        spellcheck="false"
                    />
                </div>
                <button class="btn" id="analyzeBtn">
                    <i class="fas fa-magnifying-glass btn-text"></i>
                    <span class="btn-text">Analyze</span>
                    <i class="fas fa-circle-notch spinner-icon"></i>
                </button>
            </div>

            <!-- Progress -->
            <div class="progress-wrap" id="progressWrap">
                <div class="progress-info">
                    <span class="step" id="stepText">Connecting...</span>
                    <span class="pct" id="pctText">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="fill" id="progressFill"></div>
                </div>
            </div>

            <!-- Messages -->
            <div class="msg error" id="errorMsg">
                <i class="fas fa-circle-exclamation"></i>
                <span id="errorText"></span>
            </div>
            <div class="msg success" id="successMsg">
                <i class="fas fa-circle-check"></i>
                <span id="successText"></span>
            </div>
        </div>

        <!-- Results -->
        <div class="results" id="results">
            <div class="profile-bar">
                <div class="profile-left">
                    <div class="avatar" id="avatarLetter">@</div>
                    <div class="profile-info">
                        <div class="name" id="profileUsername">username</div>
                        <div class="meta">
                            <i class="fas fa-lock" style="font-size:0.6rem;color:var(--accent-2)"></i>
                            Private Profile
                            <span class="dot"></span>
                            <span id="dateText"></span>
                        </div>
                    </div>
                </div>
                <div class="counter-box">
                    <div class="num" id="postCount">0</div>
                    <div class="lbl">Posts</div>
                </div>
            </div>
            <div class="gallery" id="gallery"></div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-badge">
                <span>Built with</span>
                <span class="heart">❤️</span>
                <span>by</span>
                <span class="dev">abbas_coding</span>
                <i class="fab fa-instagram ig"></i>
            </div>
        </footer>
    </div>

    <!-- Modal -->
    <div class="modal" id="modal">
        <button class="modal-close" id="modalClose"><i class="fas fa-xmark"></i></button>
        <img src="" alt="Full view" id="modalImg" />
    </div>

    <script>
        // ─── Particles ───
        (function createParticles() {
            const container = document.getElementById('particles');
            const count = window.innerWidth < 768 ? 15 : 30;
            for (let i = 0; i < count; i++) {
                const p = document.createElement('div');
                p.className = 'particle';
                p.style.left = Math.random() * 100 + '%';
                p.style.animationDuration = (8 + Math.random() * 14) + 's';
                p.style.animationDelay = (Math.random() * 10) + 's';
                p.style.width = p.style.height = (1.5 + Math.random() * 2.5) + 'px';
                p.style.opacity = 0.1 + Math.random() * 0.25;
                container.appendChild(p);
            }
        })();

        // ─── Modal ───
        const modal = document.getElementById('modal');
        const modalImg = document.getElementById('modalImg');

        function openModal(src) {
            modalImg.src = src;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeModal() {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            setTimeout(() => { modalImg.src = ''; }, 300);
        }

        modal.addEventListener('click', e => {
            if (e.target === modal) closeModal();
        });
        document.getElementById('modalClose').addEventListener('click', closeModal);
        document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

        // ─── Progress Simulation ───
        const steps = [
            { text: 'Connecting to server...', pct: 15 },
            { text: 'Resolving profile...', pct: 35 },
            { text: 'Bypassing privacy...', pct: 55 },
            { text: 'Extracting media...', pct: 75 },
            { text: 'Decoding images...', pct: 90 },
            { text: 'Finalizing...', pct: 98 },
        ];

        function runProgress() {
            return new Promise(resolve => {
                const wrap = document.getElementById('progressWrap');
                const fill = document.getElementById('progressFill');
                const stepEl = document.getElementById('stepText');
                const pctEl = document.getElementById('pctText');
                wrap.classList.add('active');
                fill.style.width = '0%';

                let i = 0;
                const interval = setInterval(() => {
                    if (i >= steps.length) {
                        clearInterval(interval);
                        fill.style.width = '100%';
                        pctEl.textContent = '100%';
                        stepEl.textContent = 'Done!';
                        setTimeout(() => {
                            wrap.classList.remove('active');
                            resolve();
                        }, 400);
                        return;
                    }
                    stepEl.textContent = steps[i].text;
                    pctEl.textContent = steps[i].pct + '%';
                    fill.style.width = steps[i].pct + '%';
                    i++;
                }, 500);
            });
        }

        // ─── Messages ───
        function showError(msg) {
            const el = document.getElementById('errorMsg');
            document.getElementById('errorText').textContent = msg;
            el.classList.add('active');
            document.getElementById('successMsg').classList.remove('active');
        }

        function showSuccess(msg) {
            const el = document.getElementById('successMsg');
            document.getElementById('successText').textContent = msg;
            el.classList.add('active');
            document.getElementById('errorMsg').classList.remove('active');
        }

        function clearMessages() {
            document.getElementById('errorMsg').classList.remove('active');
            document.getElementById('successMsg').classList.remove('active');
        }

        // ─── Display Results ───
        function displayResults(data) {
            document.getElementById('profileUsername').textContent = '@' + data.username;
            document.getElementById('avatarLetter').textContent = data.username.charAt(0).toUpperCase();
            document.getElementById('postCount').textContent = data.total_posts;
            document.getElementById('dateText').textContent = new Date().toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric'
            });

            const gallery = document.getElementById('gallery');
            gallery.innerHTML = '';

            data.posts.forEach((post, idx) => {
                const item = document.createElement('div');
                item.className = 'gallery-item';
                item.addEventListener('click', () => openModal(post.url));
                item.innerHTML = `
                    <img src="${post.url}" alt="Post ${idx + 1}" loading="lazy"
                         onerror="this.parentElement.style.display='none'" />
                    <div class="g-badge"><i class="fas fa-lock"></i> ${idx + 1}</div>
                    <div class="g-overlay">
                        <span class="g-id">${post.id.substring(0, 14)}…</span>
                    </div>
                `;
                gallery.appendChild(item);
            });

            document.getElementById('results').classList.add('active');
            setTimeout(() => {
                document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }

        // ─── Main Logic ───
        const analyzeBtn = document.getElementById('analyzeBtn');
        const usernameInput = document.getElementById('username');

        analyzeBtn.addEventListener('click', async function () {
            const username = usernameInput.value.trim().replace(/^@/, '');

            if (!username) {
                showError('Please enter a username to analyze.');
                usernameInput.focus();
                return;
            }

            if (!/^[a-zA-Z0-9._]{1,30}$/.test(username)) {
                showError('Invalid username format.');
                return;
            }

            clearMessages();
            document.getElementById('results').classList.remove('active');
            document.getElementById('gallery').innerHTML = '';

            this.classList.add('loading');
            this.disabled = true;

            try {
                await runProgress();

                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username })
                });

                const data = await response.json();

                if (data.success && data.posts && data.posts.length > 0) {
                    showSuccess(`Successfully extracted ${data.total_posts} private posts!`);
                    displayResults(data);
                } else {
                    showError(data.message || 'No posts found for this profile.');
                }
            } catch (err) {
                showError('Connection failed. Please check your network and try again.');
                console.error(err);
            } finally {
                this.classList.remove('loading');
                this.disabled = false;
            }
        });

        usernameInput.addEventListener('keypress', e => {
            if (e.key === 'Enter') analyzeBtn.click();
        });

        // Auto-focus
        usernameInput.focus();

        // Clear error on typing
        usernameInput.addEventListener('input', clearMessages);
    </script>
</body>
</html>
        """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
