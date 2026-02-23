import os
import requests
import json
from google import genai
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
import csv
import subprocess

# --- 1. CONFIGURATION & API KEYS ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCnJhKSKLg17LIEwFu0NAYV7-t_eHCgGF4")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "yiF1s2-7cS9xvKBVJ2-2Yo4FtOFe_xO5px9hpfSGV_Q")

# Initialize the Gemini client (Using the NEW google-genai library)
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. AI CONTENT GENERATION (GEMINI) ---
def generate_article(keyword):
    print(f"Generating article with Gemini for: {keyword}...")
    
    prompt = f"""
    Act as a certified fitness expert and SEO specialist. Write an engaging, 1000-word SEO-optimized HTML-formatted blog post about '{keyword}'. 
    Use <h2> and <h3> tags for structure, and <p> for paragraphs. 
    Include internal link placeholders like [LINK_TO_OTHER_POST] where appropriate.
    Do not include the <h1> tag.
    At the very bottom, include a strong medical disclaimer stating this is for informational purposes only and not medical advice.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    return response.text

# --- 3. UNSPLASH IMAGE FETCHING ---
def get_featured_image(keyword):
    print(f"Fetching image for: {keyword}...")
    url = "https://api.unsplash.com/photos/random"
    params = {
        "query": keyword,
        "orientation": "landscape",
        "client_id": UNSPLASH_ACCESS_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "url": data['urls']['regular'],
            "alt_text": data['alt_description'] or keyword,
            "credit_name": data['user']['name'],
            "credit_link": data['user']['links']['html']
        }
    return None 

# --- 4. DATA PERSISTENCE (POSTS LOG) ---
def load_posts_log():
    if os.path.exists("posts.json"):
        with open("posts.json", "r") as f:
            return json.load(f)
    return []

def save_posts_log(posts):
    with open("posts.json", "w") as f:
        json.dump(posts, f, indent=4)

# --- 5. ASSEMBLE HTML ---
def build_html_page(keyword, article_html, image_data, date_str):
    print(f"Assembling HTML for {keyword}...")
    
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('post_template.html')
    
    slug = keyword.lower().replace(" ", "-").replace("'", "").replace('"', "")
    
    final_html = template.render(
        title=keyword.title(),
        date=date_str,
        image_url=image_data['url'],
        image_alt=image_data['alt_text'],
        credit_name=image_data['credit_name'],
        credit_link=image_data['credit_link'],
        article_body=article_html
    )
    
    filename = f"{slug}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    return filename, slug

def update_index(posts):
    print("Updating index.html...")
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('index_template.html')
    
    # Sort posts by date descending (rough sort)
    sorted_posts = sorted(posts, key=lambda x: x['date'], reverse=True)
    
    final_html = template.render(posts=sorted_posts)
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)

# --- 6. GIT AUTOMATION ---
def git_push():
    print("Pushing updates to GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-post: {datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Successfully pushed to GitHub!")
    except Exception as e:
        print(f"Git push failed: {e}")

# --- 7. BATCH PROCESSOR ---
def run_batch(num_posts=1):
    posts = load_posts_log()
    used_keywords = [p['keyword'] for p in posts]
    
    available_keywords = []
    with open('keywords.csv', mode='r') as file:
        reader = csv.DictReader(file)
        available_keywords = [row['keyword'] for row in reader if row['keyword'] not in used_keywords]

    if not available_keywords:
        print("No new keywords found in keywords.csv!")
        return

    count = 0
    for keyword in available_keywords:
        if count >= num_posts:
            break
            
        article_content = generate_article(keyword)
        image_info = get_featured_image(keyword)
        
        if image_info:
            date_str = datetime.now().strftime("%B %d, %Y")
            filename, slug = build_html_page(keyword, article_content, image_info, date_str)
            
            posts.append({
                "keyword": keyword,
                "title": keyword.title(),
                "url": filename,
                "date": date_str,
                "image_url": image_info['url'],
                "image_alt": image_info['alt_text']
            })
            count += 1
        else:
            print(f"Skipping {keyword} due to image fetch failure.")

    save_posts_log(posts)
    update_index(posts)
    
    if count > 0:
        git_push()

if __name__ == "__main__":
    # Change num_posts to generate more at once
    run_batch(num_posts=1)
