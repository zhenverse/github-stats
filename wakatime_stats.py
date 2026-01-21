import os
import requests
import html
import datetime

# --- 1. Theme Configuration ---
CSS_STYLES = '''
    <style>
        :root {
            --bg: #ffffff; /* background */
            --border: #e1e4e8;
            --title: rgb(36, 41, 46);
            --text-primary: rgb(36, 41, 46);
            --text-secondary: rgb(88, 96, 105); /* time, percent */
            --bar-bg: #ebedf0; /* background of progress bar */
        }
        
        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #0d1117;
                --border: #30363d;
                --title: #c9d1d9;
                --text-primary: #c9d1d9;
                --text-secondary: #8b949e;
                --bar-bg: #21262d;
            }
        }
        
        /* Apply variables to SVG elements */
        .card-bg { 
            fill: var(--bg);
            stroke: var(--border); 
        }
        .header { 
            font: 600 16px -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji; 
            color: var(--title);
            fill: var(--title); 
        }
        .lang-name { 
            font: 600 13px -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji; 
            color: var(--text-primary);
            fill: var(--text-primary); 
        }
        .lang-percent { 
            font: 400 12px -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji; 
            color: var(--text-secondary);
            fill: var(--text-secondary); 
        }
        .bar-bg { 
            fill: var(--bar-bg); 
        }
    </style>
'''

# --- 2. Language Color Mapping ---
LANGUAGE_COLORS = {
    "TeX": "#3D6117",
    "Python": "#3572A5",
    "C": "#555555",
    "C++": "#f34b7d",
    "Markdown": "#083fa1",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Bash": "#89e051",
    "Shell": "#89e051",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "CSS": "#563d7c",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Other": "#8b949e"
}

# --- 3. Basic Settings ---
CARD_WIDTH = 495
CARD_HEIGHT = 195
PADDING = 25
MAX_ITEMS = 8  # Max 8 items (4 rows)
OUTPUT_DIR = "generated"
WAKATIME_API_KEY = os.environ.get("WAKATIME_API_KEY")

def fetch_wakatime(endpoint):
    """Fetch data from WakaTime API."""
    if not WAKATIME_API_KEY:
        print("Error: WAKATIME_API_KEY not found in environment variables.")
        return None
        
    try:
        url = f"https://wakatime.com/api/v1/users/current/{endpoint}?api_key={WAKATIME_API_KEY}"
        r = requests.get(url)
        if r.status_code != 200:
            print(f"Error fetching {endpoint}: {r.status_code}")
            return None
        return r.json()['data']
    except Exception as e:
        print(f"Exception fetching {endpoint}: {e}")
        return None

def format_duration(seconds):
    """Format seconds into 'X hrs Y mins' string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours} hrs {minutes} mins"
    else:
        return f"{minutes} mins"

def create_svg(title, languages):
    """Generate SVG image."""
    
    # --- Data Grouping Logic ---
    final_langs = []
    
    if languages:
        # If languages exceed the limit, group the rest into "Other"
        if len(languages) > MAX_ITEMS:
            # Take the top N-1 languages
            final_langs = languages[:MAX_ITEMS-1]
            
            # Calculate stats for the rest
            other_langs = languages[MAX_ITEMS-1:]
            other_total_seconds = sum(l.get('total_seconds', 0) for l in other_langs)
            other_percent = sum(l.get('percent', 0) for l in other_langs)
            
            # Create "Other" entry
            final_langs.append({
                'name': 'Other',
                'percent': other_percent,
                'total_seconds': other_total_seconds,
                'text': format_duration(other_total_seconds)
            })
        else:
            final_langs = languages

    # --- Start Drawing SVG ---
    bar_svg = ""
    bar_width = CARD_WIDTH - (PADDING * 2)
    bar_start_x = PADDING
    current_x = bar_start_x
    
    # 1. Draw Progress Bar Background
    bar_svg += f'<rect x="{PADDING}" y="60" width="{bar_width}" height="10" rx="5" class="bar-bg" />'
    
    # 2. Draw Colored Segments
    for lang in final_langs:
        # Skip very small segments to avoid rendering issues, unless it needs to be counted
        if lang['percent'] < 0.1: continue 
        
        lang_name = lang['name']
        color = LANGUAGE_COLORS.get(lang_name, LANGUAGE_COLORS["Other"])
        
        width = (bar_width * lang['percent']) / 100
        
        bar_svg += f'<rect x="{current_x}" y="60" width="{width}" height="10" fill="{color}" />'
        current_x += width

    # 3. Draw Language List
    list_svg = ""
    col_1_x = PADDING
    col_2_x = PADDING + (CARD_WIDTH / 2) + 10 
    start_y = 95
    line_height = 25
    
    for i, lang in enumerate(final_langs):
        lang_name = lang['name']
        color = LANGUAGE_COLORS.get(lang_name, LANGUAGE_COLORS["Other"])
        
        # Determine column (Left or Right)
        x = col_1_x if i % 2 == 0 else col_2_x
        y = start_y + (i // 2) * line_height
        
        display_name = html.escape(lang_name)
        
        # Use 'text' from API or fallback to percentage
        time_text = lang.get('text', f"{lang['percent']}%")
        
        list_svg += f'''
        <g transform="translate({x}, {y})">
            <circle cx="6" cy="-5" r="5" fill="{color}"/>
            <text x="18" y="0" class="lang-name">{display_name}</text>
            <text x="18" y="0" dx="180" class="lang-percent" text-anchor="end">{time_text}</text>
        </g>
        '''

    # 4. Assemble Final SVG
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    svg_content = f'''<svg width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
    <!-- Generated at: {timestamp} -->
    {CSS_STYLES}
    <rect x="0.5" y="0.5" width="{CARD_WIDTH-1}" height="{CARD_HEIGHT-1}" rx="6" class="card-bg"/>
    <text x="{PADDING}" y="35" class="header">{title}</text>
    {bar_svg}
    {list_svg}
</svg>'''
    return svg_content

def main():
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
        except OSError:
            pass

    print("--- Starting WakaTime Stats Generation ---")

    # 1. All Time
    all_time_data = fetch_wakatime("stats/all_time")
    if all_time_data and 'languages' in all_time_data:
        svg = create_svg("WakaTime All-Time", all_time_data['languages'])
        with open(os.path.join(OUTPUT_DIR, "waka_all_time.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print("✅ Generated waka_all_time.svg")

    # 2. Last 7 Days
    week_data = fetch_wakatime("stats/last_7_days")
    if week_data and 'languages' in week_data:
        svg = create_svg("WakaTime Last 7 Days", week_data['languages'])
        with open(os.path.join(OUTPUT_DIR, "waka_week.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print("✅ Generated waka_week.svg")

if __name__ == "__main__":
    main()