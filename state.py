import sys
import os
import re
import spacy
import textdistance

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def normalize_line(line):
    """Normalize a line by lowercasing, removing links, and collapsing spaces."""
    line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
    line = re.sub(r'[^\w\s]', '', line.lower()).strip()
    return line

def is_image_line(line):
    """Check if line contains an image markdown or image-related content."""
    return (re.search(r'!\[.*?\]\(.*?\)', line) is not None or
            any(term in line.lower() for term in ['image:', 'img:', 'picture:', 'photo:']))

def is_ui_junk(line):
    """Check if line contains UI elements, icons, or non-content elements."""
    line_lower = line.lower()
    
    # Common UI/icon terms
    ui_terms = [
        'icon', 'avatar', 'logo', 'button', 'nav', 'navbar', 'menu', 
        'hamburger', 'dropdown', 'toggle', 'footer', 'header', 'banner',
        'sidebar', 'widget', 'chatbot', 'cookie', 'notification', 'alert',
        'tooltip', 'badge', 'card', 'carousel', 'slider', 'modal', 'popup',
        'tab', 'accordion', 'breadcrumb', 'pagination', 'loader', 'spinner',
        'progress', 'checkbox', 'radio', 'switch', 'input', 'textarea',
        'select', 'form', 'label', 'field', 'close', 'minimize', 'maximize',
        'expand', 'collapse', 'zoom', 'scroll', 'drag', 'drop', 'overlay',
        'backdrop', 'splash', 'placeholder', 'toolbar', 'ribbon', 'fab',
        'stepper', 'chip', 'divider', 'snackbar', 'toast', 'dialog'
    ]
    
    # File extensions to exclude
    file_extensions = [
        r'\.svg',   r'\.gif',  r'\.ico',   r'\.bmp',   r'\.tiff',  r'\.eps',   r'\.ai',    r'\.psd',
        r'\.jpg',   r'\.jpeg', r'\.png',   r'\.webp',  r'\.avif',  r'\.heic',  r'\.raw',   r'\.cr2',
        r'\.mp4',   r'\.mov',  r'\.avi',   r'\.mkv',   r'\.flv',   r'\.wmv',   r'\.mpeg',  r'\.3gp',
        r'\.mp3',   r'\.wav',  r'\.aac',   r'\.ogg',   r'\.flac',  r'\.m4a',   r'\.wma',   r'\.amr',
        r'\.pdf',   r'\.docx', r'\.xlsx',  r'\.pptx',  r'\.odt',   r'\.rtf',   r'\.tex',   r'\.csv',
        r'\.ttf',   r'\.otf',  r'\.woff',  r'\.woff2', r'\.eot',   r'\.fon',   r'\.fnt',
        r'\.zip',   r'\.rar',  r'\.7z',    r'\.tar',   r'\.gz',    r'\.bz2',   r'\.xz',
        r'\.exe',   r'\.dll',  r'\.msi',   r'\.bat',   r'\.cmd',   r'\.sh',    r'\.pyc',
        r'\.db',    r'\.sqlite', r'\.sql', r'\.bak',   r'\.log',   r'\.tmp',   r'\.swp',
        r'\.torrent', r'\.iso', r'\.img',  r'\.vmdk',  r'\.vdi',   r'\.ova',   r'\.apk',
        r'\.ipa',   r'\.jar',  r'\.class', r'\.java',  r'\.cs',    r'\.vb',    r'\.rb',
        r'\.php',   r'\.asp',  r'\.jsp',   r'\.aspx',  r'\.cgi',   r'\.pl',    r'\.lua'
    ]
    
    # Patterns that indicate non-content elements
    patterns = [
        r'\b\d+x\d+\b',  # Image dimensions (e.g., 100x100)
        r'\b\d+px\b',    # Pixel sizes
        r'#[0-9a-f]{3,6}',  # Hex colors
        r'\b(rgb|rgba|hsl|hsla)\([^)]+\)',  # Color functions
        r'\b(click|tap|hover|press|select|swipe|pinch)\b',
        r'\b(loading|spinner|progress)\b',
        r'©\s*\d{4}',  # Copyright
        r'all rights reserved',
        r'terms of service|privacy policy',
        r'cookie consent',
        r'[\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF]'  # Common Unicode symbols/icons
    ]
    
    # Check for UI terms
    if any(term in line_lower for term in ui_terms):
        return True
    
    # Check for file extensions
    if any(re.search(ext, line_lower) for ext in file_extensions):
        return True
    
    # Check for patterns
    if any(re.search(pattern, line_lower) for pattern in patterns):
        return True
    
    # Check for empty or very short lines
    if len(line.strip()) < 3:
        return True
    
    return False

def is_contact_line(line):
    """Check if line contains contact information."""
    contact_patterns = [
        r'email\s*:', 
        r'phone\s*:', 
        r'mobile\s*:', 
        r'tel:', 
        r'address\s*:',
        r'http[s]?://',
        r'\b(contact|connect|reach|follow)\b',
        r'linkedin\.com|facebook\.com|instagram\.com|twitter\.com',
        r'github\.com|youtube\.com|whatsapp|telegram',
        r'\b[\w\.-]+@[\w\.-]+\.\w+\b'  # Email regex
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in contact_patterns)

def needs_newline_after(current_line, next_line):
    """Determine if we need a newline after current line."""
    if is_image_line(current_line):
        return True
    if current_line.startswith('#') and not next_line.startswith('#'):
        return True
    if ('address' in current_line.lower() and 
        any(x in next_line.lower() for x in ['phone', 'mobile', 'email'])):
        return True
    return False

def split_contact_lines(line):
    """Split combined contact information into separate lines."""
    # Split different contact info types
    line = re.sub(r'([^\s])(Email\s*:)', r'\1\n\2', line, flags=re.IGNORECASE)
    line = re.sub(r'(Email\s*:[^\n]+)(http[s]?://)', r'\1\n\2', line, flags=re.IGNORECASE)
    line = re.sub(r'(\bPhone\b[^\n]+)(\bMobile\b)', r'\1\n\2', line, flags=re.IGNORECASE)
    line = re.sub(r'(\bAddress\b[^\n]+)(\bEmail\b)', r'\1\n\2', line, flags=re.IGNORECASE)
    
    # Split multiple URLs
    line = re.sub(r'(https?://[^\s]+)\s+(https?://)', r'\1\n\2', line)
    
    return line

def clean_and_restructure_file(file_path):
    """Cleans and restructures a text file with proper formatting."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return

    seen_exact = set()
    seen_normalized = {}
    cleaned_lines = []
    current_section = None
    section_content = []

    for i, line in enumerate(lines):
        original_line = line.strip()
        line = line.strip()

        # Skip empty or junk lines
        if not line or is_ui_junk(line):
            continue

        # Handle social media links
        if is_contact_line(line):
            line = split_contact_lines(line)
            for sub_line in line.split('\n'):
                if sub_line.strip() and not is_ui_junk(sub_line):
                    normalized = normalize_line(sub_line)
                    if normalized not in seen_exact:
                        seen_exact.add(normalized)
                        section_content.append(sub_line.strip())
            continue

        # Skip images and non-content elements
        if is_image_line(line) or is_ui_junk(line):
            continue

        # Deduplication with fuzzy matching
        normalized = normalize_line(line)
        if normalized in seen_exact:
            continue
            
        duplicate_found = False
        for seen_norm in seen_normalized:
            if textdistance.jaro_winkler.normalized_similarity(seen_norm, normalized) > 0.92:
                duplicate_found = True
                break
        if duplicate_found:
            continue

        seen_exact.add(normalized)
        seen_normalized[normalized] = line

        # Restructure Content
        if re.search(r'^#+\s+', line):
            if current_section:
                cleaned_lines.append(format_section(current_section, section_content))
            current_section = line.strip("# ").strip()
            section_content = []
            continue

        section_content.append(original_line)

    if current_section:
        cleaned_lines.append(format_section(current_section, section_content))

    # Process lines to add newlines where needed
    final_output = []
    for i in range(len(cleaned_lines)):
        line = cleaned_lines[i]
        final_output.append(line)
        
        # Check if we need a newline after this line
        if i < len(cleaned_lines) - 1:
            next_line = cleaned_lines[i+1]
            if needs_newline_after(line, next_line):
                final_output.append('""')  # Empty quoted line for newline

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_output))
    except IOError:
        print(f"Error: Unable to write to file '{file_path}'.")
        return

    print(f"[✔] Cleaned and restructured file: {file_path} | Lines kept: {len(final_output)}")

def format_section(section_title, section_content):
    """Formats a section with proper structure and quotes."""
    formatted = [f'"# {section_title}"']
    for i, item in enumerate(section_content):
        # Skip if it's UI junk that slipped through
        if is_ui_junk(item):
            continue
            
        bullet = "- " if not item.startswith('- ') else ""
        formatted_line = f'"{bullet}{item}"'
        formatted.append(formatted_line)
        
        # Add newline after image or before contact info
        if i < len(section_content) - 1:
            next_item = section_content[i+1]
            if (is_image_line(item) or 
                ('address' in item.lower() and 
                 any(x in next_item.lower() for x in ['phone', 'mobile', 'email']))):
                formatted.append('""')
    
    return '\n'.join(formatted)

engine_path = os.path.abspath(os.path.join("engine", "xengine"))
sys.path.insert(0, engine_path)

from Cengine import xengine

async def main(link):
    await xengine(link)
    clean_and_restructure_file("output/llm.txt")


# import os
# import tiktoken
# import time
# import requests

# # Constants
# USD_COST_PER_1K_TOKENS = 0.01        # GPT-4-turbo input pricing
# INR_CACHE_DURATION = 60 * 60         # Cache INR for 1 hour
# INR_FALLBACK_RATE = 83.0             # Default INR rate if fetch fails
# CURRENCY_API_TIMEOUT = 0.3           # Max 300ms wait for API

# # Global cache for tokenizer + INR rate
# _encoding = tiktoken.get_encoding("cl100k_base")
# _cached_inr_rate = INR_FALLBACK_RATE
# _last_inr_fetch = 0

# def get_cached_inr_rate():
#     global _cached_inr_rate, _last_inr_fetch
#     now = time.time()

#     if now - _last_inr_fetch < INR_CACHE_DURATION:
#         return _cached_inr_rate

#     try:
#         response = requests.get(
#             "https://api.exchangerate.host/convert?from=USD&to=INR",
#             timeout=CURRENCY_API_TIMEOUT
#         )
#         data = response.json()
#         _cached_inr_rate = data.get("result", INR_FALLBACK_RATE)
#         _last_inr_fetch = now
#     except:
#         _cached_inr_rate = INR_FALLBACK_RATE

#     return _cached_inr_rate

# def analyze_llm_file(file_path: str) -> dict:
#     start = time.time()

#     # Read file once
#     with open(file_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     # Tokenize once
#     token_count = len(_encoding.encode(content))

#     # File size
#     file_size_bytes = os.path.getsize(file_path)
#     file_size_kb = file_size_bytes / 1024
#     file_size_mb = file_size_kb / 1024

#     # Cost
#     usd_cost = (token_count / 1000) * USD_COST_PER_1K_TOKENS
#     inr_cost = usd_cost * get_cached_inr_rate()

#     # Final stats
#     return {
#         "tokens": token_count,
#         "inr_cost": round(inr_cost, 2),
#         "file_size_mb": round(file_size_mb, 2),
#     }

# # === Example usage ===
# if __name__ == "__main__":
#     path = "output/llm.txt"
#     stats = analyze_llm_file(path)

#     print(f"🧠 Tokens: {stats['tokens']}")
#     print(f"💰 Cost: ${stats['usd_cost']} (~₹{stats['inr_cost']})")
#     print(f"📦 File size: {stats['file_size_kb']} KB ({stats['file_size_mb']} MB)")
#     print(f"⚡ Processing time: {stats['processing_time_ms']} ms")
