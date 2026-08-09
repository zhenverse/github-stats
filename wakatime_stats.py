import os
import requests
import html
import datetime

# --- 1. Theme Configuration ---
CSS_STYLES = '''
    <style>
        :root {
            --bg: #ffffff;
            --border: #e1e4e8;
            --title: rgb(36, 41, 46);
            --text-primary: rgb(36, 41, 46);
            --text-secondary: rgb(88, 96, 105);
            --bar-bg: #ebedf0;
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
        
        .card-bg { fill: var(--bg); stroke: var(--border); }
        .header { font: 600 16px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color: var(--title); fill: var(--title); }
        .lang-name { font: 600 13px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color: var(--text-primary); fill: var(--text-primary); }
        .lang-percent { font: 400 12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; color: var(--text-secondary); fill: var(--text-secondary); }
        .bar-bg { fill: var(--bar-bg); }
    </style>
'''

# --- 2. Basic Settings ---
CARD_WIDTH = 495
CARD_HEIGHT = 195
PADDING = 25
MAX_ITEMS = 8  # Max 8 items (4 rows)
OUTPUT_DIR = "generated"
WAKATIME_API_KEY = os.environ.get("WAKATIME_API_KEY")

GITHUB_COLORS = {}

def fetch_github_colors():
    global GITHUB_COLORS
    print("Fetching official GitHub colors...")
    try:
        r = requests.get("https://raw.githubusercontent.com/ozh/github-colors/master/colors.json", timeout=10)
        if r.status_code == 200:
            GITHUB_COLORS = r.json()
            print("✅ GitHub colors loaded successfully.")
        else:
            print(f"⚠️ Failed to fetch colors: HTTP {r.status_code}. Will use fallback colors.")
    except Exception as e:
        print(f"⚠️ Exception fetching colors: {e}. Will use fallback colors.")

def get_color(lang_name):
    mapping = {
        "Vue.js": "Vue",
        "React": "JavaScript",
        "C++": "C++",
        "TeX": "TeX"
    }
    lookup_name = mapping.get(lang_name, lang_name)

    if lookup_name in GITHUB_COLORS and "color" in GITHUB_COLORS[lookup_name]:
        color = GITHUB_COLORS[lookup_name]["color"]
        if color: 
            return color
            
    return "#8b949e"

def fetch_wakatime(endpoint):
    """Fetch data from WakaTime API."""
    if not WAKATIME_API_KEY:
        print("Error: WAKATIME_API_KEY not found in environment variables.")
        return None
        
    try:
        url = f"https://wakatime.com/api/v1/users/current/{endpoint}?api_key={WAKATIME_API_KEY}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"Error fetching {endpoint}: HTTP {r.status_code}")
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
    final_langs = []
    
    if languages:
        if len(languages) > MAX_ITEMS:
            final_langs = languages[:MAX_ITEMS-1]
            other_langs = languages[MAX_ITEMS-1:]
            other_total_seconds = sum(l.get('total_seconds', 0) for l in other_langs)
            other_percent = sum(l.get('percent', 0) for l in other_langs)
            
            final_langs.append({
                'name': 'Other',
                'percent': other_percent,
                'total_seconds': other_total_seconds,
                'text': format_duration(other_total_seconds)
            })
        else:
            final_langs = languages

    bar_svg = ""
    bar_width = CARD_WIDTH - (PADDING * 2)
    current_x = PADDING
    
    # Draw Background Bar
    bar_svg += f'<rect x="{PADDING}" y="60" width="{bar_width}" height="10" rx="5" class="bar-bg" />'
    
    # Draw Colored Segments
    for lang in final_langs:
        if lang['percent'] < 0.1: continue 
        
        color = get_color(lang['name'])
        width = (bar_width * lang['percent']) / 100
        bar_svg += f'<rect x="{current_x}" y="60" width="{width}" height="10" fill="{color}" />'
        current_x += width

    # Draw Language List
    list_svg = ""
    col_1_x = PADDING
    col_2_x = PADDING + (CARD_WIDTH / 2) + 10 
    start_y = 95
    line_height = 25
    
    for i, lang in enumerate(final_langs):
        color = get_color(lang['name'])
        x = col_1_x if i % 2 == 0 else col_2_x
        y = start_y + (i // 2) * line_height
        display_name = html.escape(lang['name'])
        time_text = lang.get('text', f"{lang['percent']}%")
        
        list_svg += f'''
        <g transform="translate({x}, {y})">
            <circle cx="6" cy="-5" r="5" fill="{color}"/>
            <text x="18" y="0" class="lang-name">{display_name}</text>
            <text x="18" y="0" dx="180" class="lang-percent" text-anchor="end">{time_text}</text>
        </g>
        '''

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
    
    fetch_github_colors()

    all_time_data = fetch_wakatime("stats/all_time")
    if all_time_data and 'languages' in all_time_data:
        svg = create_svg("WakaTime All-Time", all_time_data['languages'])
        with open(os.path.join(OUTPUT_DIR, "waka_all_time.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print("✅ Generated waka_all_time.svg")

    week_data = fetch_wakatime("stats/last_7_days")
    if week_data and 'languages' in week_data:
        svg = create_svg("WakaTime Last 7 Days", week_data['languages'])
        with open(os.path.join(OUTPUT_DIR, "waka_week.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print("✅ Generated waka_week.svg")

if __name__ == "__main__":
    main()