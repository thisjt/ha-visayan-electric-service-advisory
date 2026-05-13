import json
import re

def parse_posts():
    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
        
    advisories = []
    
    for post in posts:
        excerpt = post.get('excerpt', '')
        title = post.get('title', '')
        
        # Try to find the date at the beginning of the excerpt
        date_match = re.match(r'^([A-Z][a-z]+ \d{1,2}, \d{4})', excerpt)
        date_str = date_match.group(1) if date_match else title.replace('Service Interruption: ', '')
        
        map_url = post.get('media', {}).get('wixMedia', {}).get('image', {}).get('url', '')
        
        # Find all interruption blocks
        # Time: ... Purpose: ... Areas Affected: ...
        pattern = r'Time:\s*(.*?)\s*(?:\((.*?)\))?\s*Purpose:\s*(.*?)\s*Areas Affected:\s*(.*?)(?=\s*Map:|\s*Time:|(?:\.\.\.)$|$)'
        
        matches = re.finditer(pattern, excerpt, re.IGNORECASE | re.DOTALL)
        for m in matches:
            time_str = m.group(1).strip()
            duration_str = m.group(2).strip() if m.group(2) else ""
            purpose_str = m.group(3).strip()
            areas_str = m.group(4).strip()
            
            advisories.append({
                'Date': date_str,
                'Time': time_str,
                'Duration': duration_str,
                'Cancelled': 'No',
                'Purpose': purpose_str,
                'Areas Affected': areas_str,
                'Map': map_url
            })
            
    with open('parsed_advisories.json', 'w', encoding='utf-8') as f:
        json.dump(advisories, f, indent=2)
        
if __name__ == '__main__':
    parse_posts()
