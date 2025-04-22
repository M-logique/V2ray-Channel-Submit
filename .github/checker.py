from os import environ
import re
from requests import get
from bs4 import BeautifulSoup

BODY = environ.get("BODY", "")
PATTERN = r"(?:https?://)?(?:t\.me/)?@?([a-zA-Z0-9_]{4,})"

channel_ids = []
valid_channel_ids = []
invalid_channel_ids = []

def tg_channel_messages(channel_id):
    try:
        response = get(f"https://t.me/s/{channel_id}", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        div_messages = soup.find_all("div", class_="tgme_widget_message")
        return div_messages
    except Exception:
        return []

def extract_config_from_message(div_message):
    div_text = div_message.find("div", class_="tgme_widget_message_text")
    if not div_text:
        return ""
    text = div_text.prettify()
    text = re.sub(r"<code>([^<>]+)</code>", r"\1",
            re.sub(r"<a[^<>]+>([^<>]+)</a>", r"\1",
            re.sub(r"\s*", "", text)))
    return text

v2ray_pattern = re.compile(r'(?:vless|vmess|ss|trojan):\/\/[^\n#]+(?:#[^\n]*)?')

for line in BODY.splitlines():
    line = line.strip()
    if line.startswith("CHANNEL_ID="):
        raw_id = line.replace("CHANNEL_ID=", "").strip()
        matched = re.search(PATTERN, raw_id)
        if matched:
            channel_ids.append(matched.group(1))

for channel_id in channel_ids:
    messages = tg_channel_messages(channel_id)
    if not messages:
        invalid_channel_ids.append(channel_id)
        continue

    configs = [extract_config_from_message(msg) for msg in messages]
    if any(v2ray_pattern.search(cfg) for cfg in configs):
        valid_channel_ids.append(channel_id)
    else:
        invalid_channel_ids.append(channel_id)

output = "## ✅ Channel Check Result\n\n"

if valid_channel_ids:
    output += "**✅ Valid Channels:**\n"
    for ch in valid_channel_ids:
        output += f"- @{ch}\n"
    output += "\n"

if invalid_channel_ids:
    output += "**❌ Invalid Channels (No config found):**\n"
    for ch in invalid_channel_ids:
        output += f"- @{ch}\n"
    output += "\n"

with open(environ['GITHUB_ENV'], 'a') as f:
    f.write(f"body<<EOF\n{output}\nEOF\n")



with open("channels.txt", "a") as fp:
    fp.write("\n".join(valid_channel_ids))