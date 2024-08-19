import argparse
import requests
from urllib.parse import urlparse
from datetime import datetime
import html
import re
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Command line options
arguments = argparse.ArgumentParser(
    prog="mastodon_user_info",
    description="Get all your Mastodon Posts as Diary"
)
arguments.add_argument("url", type=str, nargs='?', default=os.getenv("MASTODON_URL"), help="URL of the Mastodon profile")
arguments.add_argument("--output", type=str, default=os.getenv("OUTPUT_FILE", "posts.html"), help="Output HTML file")

args = arguments.parse_args()

def process_diary_content(content):
    # Remove HTML tags
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    # print(f"Function Called with: '{text}'")  # Debugging line

    if text.startswith("#Diary"):
        diary_content = text[len("#Diary"):].lstrip().strip()
        # Remove extra spaces, commas, and exclamation marks
        diary_content = re.sub(r'[ ,!]+', ' ', diary_content).strip()
        # print(f"Raw Content: '{text}'")  # Debugging line
        # print(f"Processed Content: '{diary_content}'")  # Debugging line
        return diary_content

    # print("Content does not start with '#Diary'.")  # Debugging line
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
    response = requests.get(user_lookup_api)
    response.raise_for_status()  # Raise HTTPError for bad responses
    user_data = response.json()
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
        response = requests.get(user_timeline_api, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        posts = response.json()
        if not posts:
            break
        all_posts.extend(posts)
        # Get the ID of the oldest post to fetch older posts
        oldest_post = posts[-1]
        # Convert ID to integer before performing arithmetic
        max_id = int(oldest_post['id']) - 1
        params['max_id'] = max_id
    except requests.RequestException as e:
        print(f"Error fetching posts: {e}")
        raise SystemExit
    except ValueError as e:
        print(f"Error processing post ID: {e}")
        break

# Prepare HTML output
with open(args.output, "w") as file:
    file.write('<html><head><title>Diary</title></head><link rel="icon" href="cd5.gif" type="image/gif" ><body>\n')
    file.write("<div style=\"display: flex; align-items: center;\">\n <img src=\"book3.gif\" alt=\"diary\" style=\"margin-right: 10px;\">\n <h1>Diary of the Glitch</h1> </div>\n")


    last_date = None

    if isinstance(all_posts, list):
        for post in all_posts:
            if isinstance(post, dict) and not post.get("in_reply_to_id"):  # Exclude replies
                created_at = post.get("created_at", "No date")
                content = post.get("content", "No content").strip()  # Remove leading/trailing whitespace
                
                # Skip empty content
                if not content:
                    continue
                
                # Process content to check if it starts with '#Diary'
                diary_content = process_diary_content(content)
                
                if not diary_content:
                    continue
                
                # Convert the time format
                try:
                    created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = created_at_dt.strftime("%d/%m/%Y")
                    formatted_time = created_at_dt.strftime("%I:%M %p")
                except ValueError:
                    formatted_date = "Invalid date"
                    formatted_time = "Invalid time"
                
                # Decode HTML entities for content
                decoded_content = html.unescape(diary_content)
                
                # Write date only if it has changed
                if formatted_date != last_date:
                    if last_date:
                        file.write("<hr>\n")
                    file.write(f"<p><strong>{formatted_date}</strong></p>\n")
                    last_date = formatted_date
                
                # Write time and content
                file.write(f"<p>{formatted_time}<br/>{decoded_content}</p>\n")
                
        if not all_posts:
            file.write("<p>No posts with content found.</p>\n")
    else:
        file.write("<p>Unexpected response format.</p>\n")
    
    file.write("</body></html>\n")

print(f"Posts written to {args.output}")
