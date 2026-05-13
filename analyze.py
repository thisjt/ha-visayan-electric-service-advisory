import json

def analyze():
    with open('parsed_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    warmup_data = data.get('appsWarmupData', {})
    for key1, val1 in warmup_data.items():
        for key2, val2 in val1.items():
            if isinstance(val2, str) and val2.startswith('{'):
                try:
                    inner_json = json.loads(val2)
                    posts = inner_json.get('response', {}).get('data', {}).get('postFeedPage', {}).get('posts', {}).get('posts', [])
                    with open('posts.json', 'w', encoding='utf-8') as out:
                        json.dump(posts, out, indent=2)
                    print(f"Dumped {len(posts)} posts to posts.json")
                    return
                except:
                    pass

if __name__ == '__main__':
    analyze()
