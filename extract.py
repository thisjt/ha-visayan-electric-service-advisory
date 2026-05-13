import json, re

def extract_data():
    with open('service_advisory.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    match = re.search(r'<script[^>]*id="wix-warmup-data"[^>]*>(.*?)</script>', html, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        with open('parsed_data.json', 'w', encoding='utf-8') as out:
            json.dump(data, out, indent=2)
        print("Data extracted.")
    else:
        print("No match found.")

if __name__ == '__main__':
    extract_data()
