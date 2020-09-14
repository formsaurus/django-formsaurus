import requests


class Pexels:
    def __init__(self, api_key):
        self.api_key = api_key

    def search_videos(self, query, page=None, per_page=None):
        headers = {
            'Authorization': self.api_key,
        }
        url = f'https://api.pexels.com/videos/search?query={query}'
        if per_page is not None:
            url = f'{url}&per_page={per_page}'
        if page is not None:
            url = f'{url}&page={page}'
        print(url)
        print(headers)
        result = requests.get(url, headers=headers)
        return result.json()
