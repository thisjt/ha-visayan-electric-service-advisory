import json, re

def extract_data():
    # Load posts data
    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    # Sort posts by firstPublishedDate descending to get latest
    sorted_posts = sorted(posts, key=lambda x: x.get('firstPublishedDate', ''), reverse=True)
    if not sorted_posts:
        print('No posts found.')
        return
    latest = sorted_posts[0]
    # Extract the excerpt which contains interruption details
    data = {
        'latest_post': {
            'title': latest.get('title'),
            'excerpt': latest.get('excerpt'),
            'firstPublishedDate': latest.get('firstPublishedDate'),
            'url': latest.get('url')
        }
    }
    # Save extracted data
    with open('parsed_data.json', 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2)
    print('Data extracted for latest advisory.')

if __name__ == '__main__':
    extract_data()
