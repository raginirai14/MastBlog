# MastBlog

## Overview

MastBlog is a command-line tool that retrieves posts from a specified Mastodon user's timeline and formats them into a diary-style HTML document. The output can be customized using a template file, and it supports time zone adjustments.

## Features

- Fetch user posts from a Mastodon profile.
- Format posts into an HTML diary with customizable templates.
- Supports timezone adjustments for post timestamps.

## Requirements

- Python 3.x
- The following Python packages:
  - `requests`
  - `beautifulsoup4`
  - `python-dotenv`
  - `pytz`

You can install the required packages using pip:

```bash
pip install requests beautifulsoup4 python-dotenv pytz
```

## Usage

### Command-Line Arguments

```bash
python app.py [options] [url]
```

- `url`: The URL of the Mastodon profile (optional). If not provided, it defaults to the `MASTODON_URL` environment variable.
- `--output`: Specify the output HTML file (optional). Defaults to the `OUTPUT_FILE` environment variable or `posts.html`.
- `--template`: Specify the path to an HTML template file (optional). Defaults to the `TEMPLATE` environment variable or `templates/retro_light.html`.

### Environment Variables

You can configure the following environment variables in a `.env` file:

- `MASTODON_URL`: The URL of the Mastodon profile.
- `OUTPUT_FILE`: The name of the output HTML file (default: `posts.html`).
- `TEMPLATE`: The path to the HTML template file (default: `templates/retro_light.html`).
- `TIMEZONE`: The timezone for post timestamps (default: `Asia/Kolkata`).

### Example

1. Create a `.env` file in the project directory:

   ```dotenv
   MASTODON_URL=https://mastodon.social/@example
   OUTPUT_FILE=my_diary.html
   TEMPLATE=templates/my_template.html
   TIMEZONE=America/New_York
   ```
2. Run the script:

   ```bash
   python app.py
   ```

## Output

The script generates an HTML file containing the user's posts formatted as a diary. Each post is organized by date, and only posts without replies are included. The output file will be named according to the `OUTPUT_FILE` environment variable or `posts.html` if not specified.

## Troubleshooting

- Ensure the Mastodon URL is valid.
- Check that the template file exists at the specified path.
- If you encounter issues with timezone, verify the `TIMEZONE` variable.

## Future Roadmap

- **Post Filtering**: Implement options to filter posts by date range or keywords.
- **User Authentication**: Add support for OAuth to fetch posts from private accounts.
- **Markdown Support**: Enhance content processing to support Markdown formatting.
- **Multi-User Support**: Allow fetching posts from multiple users in a single run.
- **Export Formats**: Add options to export posts in formats other than HTML (e.g., PDF, plain text).
- **User Interface**: Consider creating a simple GUI for users who prefer not to use the command line.

## License

This script is provided under the **GPL V3** License. See the `LICENSE` file for more details.
