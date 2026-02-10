import requests
import re
import datetime
import logging
import time

logger = logging.getLogger(__name__)

ADXO_URL = "https://www.ng3k.com/Misc/adxo.html"

def parse_adxo_date(date_str):
    """Parse NG3K date format like '2026 Jan01' or '2026 Jan31'"""
    try:
        # Some dates might be range-like or missing year in some contexts, 
        # but the sample showed '2026 Jan01'
        dt = datetime.datetime.strptime(date_str.strip(), "%Y %b%d")
        return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
    except Exception as e:
        logger.debug(f"Error parsing date {date_str}: {e}")
        return 0

def fetch_dxpeditions():
    """Fetch and parse NG3K DXPeditions"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(ADXO_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
        
        # Regex to find rows: <tr class="adxoitem".*?</tr>
        # Need to handle newlines
        rows = re.findall(r'<tr class="adxoitem".*?>(.*?)</tr>', html, re.DOTALL)
        
        results = []
        for row in rows:
            try:
                # Columns: Date1, Date2, Entity, Call, QSL, Rep, Info
                cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                if len(cols) < 4:
                    continue
                
                start_date = re.sub(r'<.*?>', '', cols[0]).strip()
                end_date = re.sub(r'<.*?>', '', cols[1]).strip()
                entity = re.sub(r'<.*?>', '', cols[2]).strip()
                
                # Call is in the 4th column, inside <span class="call">
                call_match = re.search(r'<span class="call">(.*?)</span>', cols[3])
                call = call_match.group(1) if call_match else cols[3]
                call = re.sub(r'<.*?>', '', call).strip()
                
                start_uts = parse_adxo_date(start_date)
                end_uts = parse_adxo_date(end_date)
                
                # Link is often in the 6th column (Reported by) or 7th (Info)
                # DXPeditions.txt likes a URL.
                url_match = re.search(r'href="(.*?)"', row)
                url = url_match.group(1) if url_match else "https://www.ng3k.com/Misc/adxo.html"
                if url.startswith("/"):
                    url = "https://www.ng3k.com" + url
                
                if start_uts and end_uts:
                    results.append(f"{start_uts},{end_uts},{entity},{call},{url}")
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
        
        return results
    except Exception as e:
        logger.error(f"Error fetching ADXO: {e}")
        return []

def get_dxped_data():
    """Aggregate DXPeditions in HamClock format"""
    peds = fetch_dxpeditions()
    # Header: count of sources (usually 2 in original, but we'll put 1 or just match)
    # Original header:
    # 2
    # DXNews
    # https://dxnews.com
    # NG3K
    # https://www.ng3k.com/Misc/adxo.html
    header = [
        "1",
        "NG3K",
        "https://www.ng3k.com/Misc/adxo.html"
    ]
    return "\n".join(header + peds)

if __name__ == "__main__":
    print(get_dxped_data())
