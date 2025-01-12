import requests

class LanscopeApiClient:
    def __init__(self, api_token):
        self.base_url = "https://api.lanscopean.com/v1"
        self.token = api_token

    def _make_api_request(self, endpoint, method='get', post_data=None):
        if post_data is None:
            post_data = {}
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f"Bearer {self.token}",
        }

        if method.lower() in ['post', 'put', 'patch'] and post_data:
            response = requests.request(method, url, headers=headers, json=post_data)
        else:
            response = requests.request(method, url, headers=headers)
        if response.status_code in [200, 201]:
            if 'application/json' in response.headers.get('Content-Type', ''):
                return {
                    'content': response.json(),
                    'headers': response.headers
                }
            else:
                return {
                    'content': None,
                    'headers': response.headers
                }
        elif response.status_code == 401:
            print("INVALID TOKEN")
            return None
        elif response.status_code == 404:
            print("404 Not Found")
            return None
        else:
            response.raise_for_status()

    def _paginate_through(self, endpoint, method='get', post_data=None):
        if post_data is None:
            post_data = {}
        results = []
        next_token = None
        while True:
            next_token_param = f"next_token={next_token}" if next_token else ""
            url = f"{endpoint}&{next_token_param}" if '?' in endpoint else f"{endpoint}?{next_token_param}"
            if method.lower() == 'get':
                response = self._make_api_request(url)
            else:
                response = self._make_api_request(url, 'post', post_data)
            if not response:
                break
            next_token = response['content'].get('next_token')
            computers = response['content'].get('data', [])
            results.extend(computers)
            if not next_token:
                break
        return results

    def get_devices(self):
        results = self._paginate_through('/devices', 'get')
        if not results:
            return []
        return results

    def _convert_utc_to_local_timezone(self, device, key):
        pass
