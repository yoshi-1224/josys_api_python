import requests

class JosysApiClient:
    def __init__(self, apiUserKey, apiSecretKey):
        self.apiUserKey = apiUserKey
        self.apiSecretKey = apiSecretKey
        self.baseUrl = 'https://developer.josys.it/api'
        self.token = None

    def _getToken(self, forceRefresh=False):
        if not forceRefresh and self.token:
            return self.token

        url = f"{self.baseUrl}/v1/oauth/tokens"
        payload = {
            'grant_type': 'client_credentials',
            'api_user_key': self.apiUserKey,
            'api_user_secret': self.apiSecretKey
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.token = data['id_token']
            return self.token
        except requests.exceptions.RequestException:
            raise Exception("ジョーシスのトークンを取得できませんでした。認証情報が正しくない可能性があります")

    def _makeApiRequest(self, endpoint, method='get', postData=None):
        url = f"{self.baseUrl}{endpoint}"
        headers = {
            'Authorization': f"Bearer {self._getToken()}",
            'Content-Type': 'application/json'
        }

        if method.lower() not in ['get', 'delete'] and postData:
            data = postData
        else:
            data = None

        try:
            response = self._sendRequest(url, method, headers, data)
            if response.status_code == 401:
                print("Refreshing token and trying again")
                headers['Authorization'] = f"Bearer {self._getToken(forceRefresh=True)}"
                response = self._sendRequest(url, method, headers, data)

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
            elif response.status_code == 204:
                print("DELETE successful")
                return {
                    'content': None,
                    'headers': response.headers
                }
            elif response.status_code == 404:
                print("404 Not Found")
                return None
            else:
                raise Exception(f"{response.status_code} : {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(str(e))

    def _sendRequest(self, url, method, headers, data=None):
        if method.lower() == 'get':
            return requests.get(url, headers=headers)
        elif method.lower() == 'post':
            return requests.post(url, headers=headers, json=data)
        elif method.lower() == 'patch':
            return requests.patch(url, headers=headers, json=data)
        elif method.lower() == 'delete':
            return requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def _paginateThrough(self, endpoint, perPage, method='get', postData=None):
        page = 1
        totalPages = 1
        result = []

        while page <= totalPages:
            if method.lower() == 'get':
                response = self._makeApiRequest(f"{endpoint}?per_page={perPage}&page={page}")
            elif method.lower() == 'post':
                response = self._makeApiRequest(f"{endpoint}?per_page={perPage}&page={page}", 'post', postData)
            else:
                raise ValueError(f"Unsupported HTTP method for pagination: {method}")

            if response and response['content']:
                result.extend(response['content'].get('data', []))
                totalPages = int(response['headers'].get('x-total-pages', '-1'))
                totalRecords = int(response['headers'].get('x-total', '0'))
                print(f"Fetching page: {page} of {totalPages}, Total Records: {totalRecords}")
                page += 1
            else:
                break
        return result
    
    def searchUserProfiles(self, searchParams, perPage=500, returnEnumsInJapanese=True, getDepartmentNames=True):
        results = self._paginateThrough('/v2/user_profiles/search', perPage, 'post', searchParams)
        if not results:
            return []

        if returnEnumsInJapanese:
            for profile in results:
                self._convertUserProfileEnumsToJapanese(profile)

        if getDepartmentNames:
            pass
        return results

    # Device endpoints
    def search_devices(self, searchParams, perPage=100, returnCustomFields=True, returnMdmFields=True, returnEnumsInJapanese=True):
        results = self._paginateThrough('/v1/devices/search', perPage, 'post', searchParams)
        if not results:
            return []

        for device in results:
            self._flattenAssignmentFields(device)

        for device in results:
            if 'intune' in device.get('source', ''):
                device['source'] = 'intune'
            else:
                device['source'] = 'josys'

        if returnEnumsInJapanese:
            for device in results:
                self._convertDeviceEnumsToJapanese(device)

        if returnCustomFields:
            for device in results:
                self._flattenCustomFields(device)
        else:
            for device in results:
                device.pop('custom_fields', None)

        if returnMdmFields:
            for device in results:
                self._flattenMdmFields(device)
        else:
            for device in results:
                device.pop('mdm_fields', None)

        return results

    def _flattenAssignmentFields(self, device):
        assignment_detail = device.get('assignment_detail')
        if assignment_detail:
            assignee = assignment_detail.get('assignee', {})
            device['assignee.name'] = f"{assignee.get('last_name', '')} {assignee.get('first_name', '')}"
            device['assignee.uuid'] = assignee.get('uuid')
            device['assignee.email'] = assignee.get('email')
            device['assignee.user_id'] = assignee.get('user_id')
            device['assignment.start_date'] = assignment_detail.get('assignment_start_date')
        device.pop('assignment_detail', None)

    def _flattenCustomFields(self, device):
        custom_fields = device.get('custom_fields', [])
        for column in custom_fields:
            device[f"custom_fields.{column.get('name', '')}"] = column.get('value')
        device.pop('custom_fields', None)

    def _flattenMdmFields(self, device):
        mdm_fields = device.get('mdm_fields', [])
        if mdm_fields is not None:
            for column in mdm_fields:
                device[f"mdm_field.{column.get('name', '')}"] = column.get('value')
        device.pop('mdm_fields', None)

    def get_device_custom_fields(self):
        response = self._makeApiRequest('/v1/devices/custom_field_definitions')
        if response and response['content']:
            return [item['name'] for item in response['content'].get('data', [])]
        else:
            return []

    def create_new_device(self, params):
        response = self._makeApiRequest('/v1/devices', 'post', params)
        if response and response['content']:
            return response['content']['data']
        else:
            return None

    def update_device(self, device_uuid, params):
        response = self._makeApiRequest(f"/v1/devices/{device_uuid}", 'patch', params)
        if response and response['content']:
            return response['content']['data']
        else:
            return None

    def _convertDeviceEnumsToJapanese(self, device):
        device['status'] = deviceStatusMappingEn2Jp.get(device.get('status'), device.get('status'))

    def _convertUserProfileEnumsToJapanese(self, profile):
        profile["status"] = userProfileStatusMappingEn2Jp[profile["status"]]
        if profile["user_category"]:
            profile["user_category"] = userCategoryMappingEn2Jp[profile["user_category"]]
    
    def create_user_profile(self, params):
        if not params.get('last_name') or not params.get('status'):
            raise ValueError('Error: "last_name" and "status" fields are required for creating a user profile.')
        
        if not params.get('email') and not params.get('user_id'):
            raise ValueError('Error: "email" or "user_id" must be provided')
        return self._makeApiRequest('/v2/user_profiles', 'post', params)['content']['data']
    
    def update_user_profile(self, uuid, params):
        response = self._makeApiRequest(f"/v2/user_profiles/{uuid}", "patch", params)
        if response and response['content']:
            return response['content']['data']
        else:
            return None

deviceStatusMappingEn2Jp = {
    "AVAILABLE": "在庫",
    "IN_USE": "利用中",
    "DECOMMISSIONED": "廃棄/解約",
    "UNKNOWN": "不明"
}

# userProfileStatusMappingEn2Jp = {
#     "ONBOARD_INITIATED": "入社前",
#     "ONBOARDED": "在籍中",
#     "TEMPORARY_LEAVE":"休職中",
#     "OFFBOARD_INITIATED": "退職済",
#     "UNKNOWN": "不明",
#     "OTHERS": "その他",
# }

userProfileStatusMappingEn2Jp = {
    "INITIATED": "入社前",
    "ACTIVE": "在籍中",
    "SUSPENDED":"休職中",
    "TERMINATED": "退職済",
    "UNKNOWN": "不明",
    "OTHERS": "その他",
}

userCategoryMappingEn2Jp = {
    "BOARD_MEMBER": "役員",
    "FULL_TIME": "正社員",
    "TEMPORARY_EMPLOYEE":"派遣社員",
    "SUBCONTRACTOR": "業務委託",
    "PART_TIME": "パート・アルバイト",
    "TRANSFEREE": "出向社員",
    "CONTRACTOR": "契約社員",
    "OTHERS": "その他",
    "SYSTEM": "システム",
    "EXTERNAL": "外部"
}