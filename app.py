import argparse
import requests
from urllib.parse import urlparse
from datetime import datetime
import html
import re
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import pytz

# Load environment variables from .env file
load_dotenv()

# Command line options
arguments = argparse.ArgumentParser(
    prog="mastodon_user_info",
    description="Get all your Mastodon Posts as Diary"
)
arguments.add_argument("url", type=str, nargs='?', default=os.getenv("MASTODON_URL"), help="URL of the Mastodon profile")
arguments.add_argument("--output", type=str, default=os.getenv("OUTPUT_FILE", "posts.html"), help="Output HTML file")
arguments.add_argument("--template", type=str, default="template.html", help="Path to HTML template file")

args = arguments.parse_args()

# Get timezone from .env or set default to 'UTC'
timezone_str = os.getenv("TIMEZONE", "Asia/Kolkata")
try:
    timezone = pytz.timezone(timezone_str)
except pytz.UnknownTimeZoneError:
    print(f"Unknown timezone: {timezone_str}. Using 'UTC' instead.")
    timezone = pytz.timezone("UTC")

def process_diary_content(content):
    # Remove HTML tags
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    if text.startswith("#Diary"):
        diary_content = text[len("#Diary"):].lstrip().strip()
        # Remove extra spaces, commas, and exclamation marks
        diary_content = re.sub(r'[ ,!]+', ' ', diary_content).strip()
        return diary_content

    return None

# Get Mastodon user information
mastodon_url = args.url
mastodon_parts = urlparse(mastodon_url)
mastodon_host = mastodon_parts.netloc
mastodon_path = mastodon_parts.path
mastodon_username = mastodon_path.split("/")[-1]  # Last element of /@example

# Construct API endpoints
user_lookup_api = f"https://{mastodon_host}/api/v1/accounts/lookup?acct={mastodon_username}"

# Fetch user data
try:
    print(f"Fetching user data from: {user_lookup_api}")  # Debugging
    response = requests.get(user_lookup_api)
    response.raise_for_status()  # Raise HTTPError for bad responses
    user_data = response.json()
    print(f"User data: {user_data}")  # Debugging
except requests.RequestException as e:
    print(f"Error fetching user data: {e}")
    raise SystemExit

# Check if an error occurred
if "error" in user_data:
    print("This user doesn't exist.")
    raise SystemExit

# Extract user ID
user_id = user_data.get("id")
if not user_id:
    print("User ID not found.")
    raise SystemExit

# Construct API endpoint for user timeline
user_timeline_api = f"https://{mastodon_host}/api/v1/accounts/{user_id}/statuses"
params = {}
all_posts = []
while True:
    try:
        print(f"Fetching posts from: {user_timeline_api} with params: {params}")  # Debugging
        response = requests.get(user_timeline_api, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        posts = response.json()
        print(f"Posts fetched: {len(posts)}")  # Debugging
        if not posts:
            break
        all_posts.extend(posts)
        # Get the ID of the oldest post to fetch older posts
        oldest_post = posts[-1]
        max_id = int(oldest_post['id']) - 1
        params['max_id'] = max_id
    except requests.RequestException as e:
        print(f"Error fetching posts: {e}")
        raise SystemExit
    except ValueError as e:
        print(f"Error processing post ID: {e}")
        break

# Load the template HTML file
try:
    with open(args.template, "r") as template_file:
        template_content = template_file.read()
    print("Template loaded successfully.")  # Debugging
except FileNotFoundError:
    print(f"Template file {args.template} not found.")
    raise SystemExit

# Prepare posts content
post_entries = []
last_date = None

if isinstance(all_posts, list):
    for post in all_posts:
        if isinstance(post, dict) and not post.get("in_reply_to_id"):  # Exclude replies
            created_at = post.get("created_at", "No date")
            content = post.get("content", "No content").strip()
            
            if not content:
                continue
            
            diary_content = process_diary_content(content)
            
            if not diary_content:
                continue
            
            # Convert to the specified timezone
            try:
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at_dt = created_at_dt.astimezone(timezone)
                formatted_date = created_at_dt.strftime("%d/%m/%Y")
                formatted_time = created_at_dt.strftime("%I:%M %p")
            except ValueError:
                formatted_date = "Invalid date"
                formatted_time = "Invalid time"
            
            decoded_content = html.unescape(diary_content)
            
            # Only add date header if date changes
            if formatted_date != last_date:
                if last_date:
                    post_entries.append("<hr>")
                post_entries.append(f"<p><strong>{formatted_date}</strong></p>")
                last_date = formatted_date
            
            post_entries.append(f"<p class='post-time'>{formatted_time}<br>{decoded_content}</p>")

if not post_entries:
    post_entries.append("<p>No posts with content found.</p>")

# Replace the {{posts}} placeholder with the actual post entries
html_output = template_content.replace("{{posts}}", "\n".join(post_entries))

# Write the final HTML output to the file
try:
    with open(args.output, "w") as output_file:
        output_file.write(html_output)
    print(f"Posts written to {args.output}")  # Debugging
except Exception as e:
    print(f"Error writing to output file: {e}")
