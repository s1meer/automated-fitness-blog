import os
import requests
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import csv
import random

# --- 1. CONFIGURATION & API KEYS ---
# Ensure you set these environment variables before running, e.g.
# export GEMINI_API_KEY="your_key"
# export UNSPLASH_ACCESS_KEY="your_key"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your_gemini_api_key_here")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "your_unsplash_access_key_here")

genai.configure(api_key=GEMINI_API_KEY)

# --- 2. AI CONTENT GENERATION ---
def generate_article(keyword):
    print(f"Generating article for: {keyword}...")
    
    prompt = f"""
    Act as a certified personal trainer. Write an engaging, 800-word HTML-formatted blog post about '{keyword}'. 
    Use <h2> and <h3> tags for structure, and <p> for paragraphs. 
    Do not include the <h1> tag (I will add that separately).
    At the very bottom, include a strong medical disclaimer stating this is for informational purposes only and not medical advice.
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text

# --- 3. UNSPLASH IMAGE FETCHING ---
def get_featured_image(keyword):
    print(f"Fetching image for: {keyword}...")
    url = f"https://api.unsplash.com/photos/random"
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
    return None # Fallback if API fails

# --- 4. ASSEMBLE HTML WITH JINJA2 ---
def build_html_page(keyword, article_html, image_data):
    print("Assembling HTML...")
    
    # Set up Jinja2 to look for templates in the current directory
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('post_template.html')
    
    # Generate the safe URL slug (e.g., "kettlebell-workouts")
    slug = keyword.lower().replace(" ", "-")
    date_str = datetime.now().strftime("%B %d, %Y")
    
    # Render the template with our dynamic variables
    final_html = template.render(
        title=keyword.title(),
        date=date_str,
        image_url=image_data['url'],
        image_alt=image_data['alt_text'],
        credit_name=image_data['credit_name'],
        credit_link=image_data['credit_link'],
        article_body=article_html
    )
    
    # Save the new file
    filename = f"{slug}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"✅ Success! Saved as {filename}")
    return filename, slug, date_str

# --- 5. UPDATE INDEX ---
def update_index(title, url_slug, date_str, image_url, image_alt):
    print("Updating index.html...")
    
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('index_template.html')
    
    # In a real app, you'd parse existing posts or load from a JSON/CSV database
    # For simplicity, we just rebuild the index with this 1 new post 
    # To fully automate, you should maintain a 'posts.json' list.
    
    posts = [
        {
            "title": title,
            "url": f"{url_slug}.html",
            "date": date_str,
            "image_url": image_url,
            "image_alt": image_alt
        }
    ]
    
    final_html = template.render(posts=posts)
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("✅ Index updated!")

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    # In the future, this will pull from a CSV. For now, we hardcode a test keyword.
    target_keyword = "beginner kettlebell exercises"
    image_keyword = "kettlebell"
    
    # Run the pipeline
    article_content = generate_article(target_keyword)
    image_info = get_featured_image(image_keyword)
    
    if image_info:
        filename, slug, date_str = build_html_page(target_keyword, article_content, image_info)
        update_index(target_keyword.title(), slug, date_str, image_info['url'], image_info['alt_text'])
    else:
        print("Failed to fetch image. Aborting to prevent incomplete page.")
