"""
WhatsApp Chat Parser
====================
Handles .txt and .zip files, supports multiple date/time formats.
Extracts: messages, system events, media, member introductions, URLs, emojis.
"""

import re
import zipfile
import io
import pandas as pd
from datetime import datetime
from collections import Counter
import emoji as emoji_lib


# ── CORE PARSER ──────────────────────────────────────────────────────────────

# Multiple WhatsApp export formats
PATTERNS = [
    # DD/MM/YY, HH.MM.SS  (Indonesian / European)
    r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}\.\d{2}\.\d{2})\]\s*(.*)',
    # DD/MM/YY, HH:MM:SS
    r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2})\]\s*(.*)',
    # MM/DD/YY, HH:MM AM/PM  (US format)
    r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*[APap][Mm])\s*-\s*(.*)',
    # DD/MM/YYYY, HH:MM  (no seconds)
    r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}[:.]\d{2})\]\s*(.*)',
    # M/D/YY, HH:MM - (no brackets, 24-hour, dash separator) — Android/iOS modern export
    r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2})\s*-\s*(.*)',
]


def extract_text_from_upload(uploaded_file):
    """Extract raw text from .txt or .zip upload."""
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            txt_files = [f for f in zf.namelist() if f.endswith('.txt')]
            if not txt_files:
                raise ValueError("No .txt file found inside the ZIP archive.")
            # Pick the largest txt file
            txt_file = max(txt_files, key=lambda f: zf.getinfo(f).file_size)
            raw = zf.read(txt_file)
    elif name.endswith('.txt'):
        raw = file_bytes
    else:
        raise ValueError("Unsupported file format. Please upload .txt or .zip")

    # Try multiple encodings
    for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, AttributeError):
            continue
    return raw.decode('utf-8', errors='replace')


def detect_pattern(text):
    """Auto-detect which WhatsApp format is used."""
    lines = text.split('\n')[:100]
    for pattern in PATTERNS:
        matches = sum(1 for line in lines if re.match(pattern, line.strip()))
        if matches > 5:
            return pattern
    # Fallback to most common
    return PATTERNS[0]


def parse_datetime(date_str, time_str):
    """Parse date and time strings into datetime object."""
    # Normalize separators
    time_str = time_str.replace('.', ':')

    # Handle AM/PM
    has_ampm = any(x in time_str.upper() for x in ['AM', 'PM'])

    # Try multiple date formats
    date_formats = ['%d/%m/%y', '%m/%d/%y', '%d/%m/%Y', '%m/%d/%Y']
    time_formats = ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p']

    for dfmt in date_formats:
        for tfmt in time_formats:
            try:
                fmt = f"{dfmt} {tfmt}"
                return datetime.strptime(f"{date_str} {time_str.strip()}", fmt)
            except ValueError:
                continue

    # Last resort
    return None


def parse_chat(text):
    """
    Parse WhatsApp chat text into structured DataFrame.

    Returns:
        pd.DataFrame with columns:
        [datetime, date, time, hour, day_of_week, user, message,
         msg_type, is_media, is_system, word_count, char_count]
    """
    pattern = detect_pattern(text)
    lines = text.split('\n')

    records = []
    current_date = None
    current_time = None
    current_content = None

    for line in lines:
        line = line.strip('\r\n\ufeff\u200e\u200f\u202f')
        match = re.match(pattern, line)

        if match:
            # Save previous message
            if current_content is not None:
                records.append((current_date, current_time, current_content))

            current_date = match.group(1)
            current_time = match.group(2)
            current_content = match.group(3)
        elif current_content is not None:
            # Multiline continuation
            current_content += '\n' + line

    # Don't forget the last message
    if current_content is not None:
        records.append((current_date, current_time, current_content))

    # Build DataFrame
    parsed = []
    for date_str, time_str, content in records:
        dt = parse_datetime(date_str, time_str)
        if dt is None:
            continue

        # Separate user from message
        user_match = re.match(r'(.*?):\s(.*)', content, re.DOTALL)
        if user_match:
            user = user_match.group(1).strip()
            message = user_match.group(2).strip()
            is_system = False
        else:
            user = 'system'
            message = content.strip()
            is_system = True

        # Classify message type
        msg_type = classify_message(message, is_system)

        # Media detection
        is_media = any(m in message for m in [
            'image omitted', 'video omitted', 'sticker omitted',
            'audio omitted', 'document omitted', 'GIF omitted',
            '<Media omitted>'
        ])

        parsed.append({
            'datetime': dt,
            'date': dt.date(),
            'time': dt.time(),
            'hour': dt.hour,
            'day_of_week': dt.strftime('%A'),
            'user': user,
            'message': message,
            'msg_type': msg_type,
            'is_media': is_media,
            'is_system': is_system,
            'word_count': len(message.split()) if not is_media else 0,
            'char_count': len(message) if not is_media else 0,
        })

    df = pd.DataFrame(parsed)
    if not df.empty:
        df = df.sort_values('datetime').reset_index(drop=True)
    return df


def classify_message(message, is_system):
    """Classify message into categories."""
    msg_lower = message.lower()

    if is_system:
        if any(w in msg_lower for w in ['joined', 'added']):
            return 'join'
        elif any(w in msg_lower for w in ['left', 'removed']):
            return 'leave'
        elif 'created' in msg_lower:
            return 'group_created'
        elif 'changed' in msg_lower:
            return 'setting_change'
        return 'system'

    if any(m in message for m in ['image omitted', 'video omitted', 'sticker omitted',
                                   'audio omitted', 'document omitted', 'GIF omitted',
                                   '<Media omitted>']):
        return 'media'
    elif 'This message was deleted' in message:
        return 'deleted'
    elif '<This message was edited>' in message:
        return 'edited'

    return 'text'


# ── MEMBER DIRECTORY EXTRACTION ──────────────────────────────────────────────

def extract_member_directory(df):
    """
    Extract structured member introductions (Nama, Alamat/Domisili, LinkedIn).
    Returns DataFrame with member profiles.
    """
    members = []
    text_msgs = df[~df['is_system'] & (df['msg_type'] == 'text')]

    for _, row in text_msgs.iterrows():
        msg = row['message']
        msg_lower = msg.lower()

        # Must contain at least nama + one other field
        has_nama = 'nama' in msg_lower
        has_address = any(w in msg_lower for w in ['alamat', 'domisili', 'kota'])
        has_linkedin = 'linkedin' in msg_lower

        if has_nama and (has_address or has_linkedin):
            member = {
                'wa_name': row['user'],
                'date': row['date'],
                'nama': extract_field(msg, ['nama']),
                'alamat': extract_field(msg, ['alamat', 'domisili', 'kota', 'lokasi']),
                'linkedin': extract_linkedin(msg),
            }
            # Only add if we got a real name
            if member['nama'] and len(member['nama']) > 1:
                members.append(member)

    mdf = pd.DataFrame(members)
    if not mdf.empty:
        # Deduplicate - keep latest intro per wa_name
        mdf = mdf.sort_values('date').drop_duplicates(subset='wa_name', keep='last')
    return mdf


def extract_field(text, keywords):
    """Extract value after a keyword label."""
    for kw in keywords:
        # Pattern: keyword : value  OR  keyword value (on same line or next)
        patterns = [
            rf'(?i){kw}\s*[:：]\s*(.+?)(?:\n|$)',
            rf'(?i){kw}\s*[:：]\s*(.+?)(?:\n|LinkedIn|Linkedin|linkedin)',
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                val = match.group(1).strip()
                val = re.sub(r'[\r\n]', '', val)
                val = val.strip(' :-')
                if val and len(val) > 1:
                    return val
    return ''


def extract_linkedin(text):
    """Extract LinkedIn URL from text."""
    match = re.search(r'https?://(?:www\.)?linkedin\.com/in/[^\s\r\n<>\"\']+', text)
    if match:
        url = match.group(0).rstrip('.,;:!?)\'\"')
        return url
    return ''


# ── URL & LINK EXTRACTION ────────────────────────────────────────────────────

def extract_urls(df):
    """Extract all shared URLs with metadata."""
    url_records = []
    text_msgs = df[~df['is_system']]

    for _, row in text_msgs.iterrows():
        urls = re.findall(r'https?://[^\s\r\n<>\"\']+', row['message'])
        for url in urls:
            url = url.rstrip('.,;:!?)\'\"')
            domain = re.search(r'https?://([^\s/]+)', url)
            url_records.append({
                'date': row['date'],
                'user': row['user'],
                'url': url,
                'domain': domain.group(1) if domain else '',
            })

    return pd.DataFrame(url_records)


# ── EMOJI EXTRACTION ─────────────────────────────────────────────────────────

def extract_emojis_from_text(text):
    """Extract all emojis from a text string."""
    return [c for c in text if c in emoji_lib.EMOJI_DATA]


def get_emoji_stats(df):
    """Get emoji usage statistics."""
    user_msgs = df[~df['is_system'] & (df['user'] != 'system')]
    emoji_counter = Counter()
    user_emoji = {}

    for _, row in user_msgs.iterrows():
        emojis = extract_emojis_from_text(row['message'])
        emoji_counter.update(emojis)
        if row['user'] not in user_emoji:
            user_emoji[row['user']] = Counter()
        user_emoji[row['user']].update(emojis)

    return emoji_counter, user_emoji


# ── TOPIC & KEYWORD ANALYSIS ─────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    'Data & Analytics': ['data', 'dataset', 'analytics', 'analisis', 'insight'],
    'SQL & Database': ['sql', 'query', 'database', 'duckdb', 'postgresql', 'mysql'],
    'Python': ['python', 'pandas', 'numpy', 'jupyter', 'flask', 'django'],
    'Visualization': ['dashboard', 'tableau', 'power bi', 'powerbi', 'looker', 'metabase', 'plotly'],
    'Machine Learning': ['machine learning', 'ml', 'deep learning', 'model', 'training'],
    'AI': ['ai', 'artificial intelligence', 'gpt', 'chatgpt', 'gemini', 'claude', 'llm'],
    'Career': ['loker', 'lowongan', 'job', 'interview', 'hiring', 'karir', 'career', 'salary', 'gaji'],
    'Learning': ['bootcamp', 'course', 'belajar', 'tutorial', 'webinar', 'sertifikat', 'certificate'],
    'Tools': ['excel', 'spreadsheet', 'github', 'git', 'docker', 'vscode'],
    'LinkedIn': ['linkedin', 'profil', 'portfolio', 'cv', 'resume'],
}


def analyze_topics(df):
    """Analyze topic frequency over time."""
    user_msgs = df[~df['is_system'] & (df['msg_type'] == 'text')].copy()
    topic_counts = {}

    for topic, keywords in TOPIC_KEYWORDS.items():
        mask = user_msgs['message'].str.lower().apply(
            lambda m: any(kw in m for kw in keywords)
        )
        topic_counts[topic] = mask.sum()

    return dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))


def get_topic_trend(df, topic_name):
    """Get daily trend for a specific topic."""
    keywords = TOPIC_KEYWORDS.get(topic_name, [])
    user_msgs = df[~df['is_system'] & (df['msg_type'] == 'text')].copy()

    mask = user_msgs['message'].str.lower().apply(
        lambda m: any(kw in m for kw in keywords)
    )
    topic_msgs = user_msgs[mask].copy()

    if topic_msgs.empty:
        return pd.DataFrame()

    return topic_msgs.groupby('date').size().reset_index(name='count')


# ── NETWORK ANALYSIS ─────────────────────────────────────────────────────────

def build_interaction_network(df, window_minutes=3):
    """
    Build interaction network based on sequential messages.
    If user B messages within `window_minutes` of user A, assume interaction.
    """
    user_msgs = df[~df['is_system'] & (df['user'] != 'system')].copy()
    user_msgs = user_msgs.sort_values('datetime').reset_index(drop=True)

    edges = Counter()

    for i in range(1, len(user_msgs)):
        prev = user_msgs.iloc[i - 1]
        curr = user_msgs.iloc[i]

        if prev['user'] == curr['user']:
            continue

        time_diff = (curr['datetime'] - prev['datetime']).total_seconds() / 60
        if time_diff <= window_minutes:
            edge = tuple(sorted([prev['user'], curr['user']]))
            edges[edge] += 1

    return edges


# ── SEARCH FUNCTION ──────────────────────────────────────────────────────────

def search_messages(df, query, user_filter=None, date_range=None):
    """Search messages with optional filters."""
    mask = df['message'].str.contains(query, case=False, na=False)

    if user_filter:
        mask &= df['user'].isin(user_filter)

    if date_range:
        start, end = date_range
        mask &= (df['date'] >= start) & (df['date'] <= end)

    return df[mask]
