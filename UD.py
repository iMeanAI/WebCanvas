import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


class FileUploader:
    def __init__(self, login_url, upload_url, file_upload_url, username, password):
        self.login_url = login_url
        self.upload_url = upload_url
        self.file_upload_url = file_upload_url
        self.username = username
        self.password = password
        self.auth_token = None

    def login(self):
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'authorization': None,
            'content-type': 'application/json',
            'origin': 'https://studio.apollographql.com',
            'priority': 'u=1, i',
            'referer': 'https://studio.apollographql.com/sandbox/explorer',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

        payload = {
            "query": "mutation PwdLogin($password: String!, $username: String!) {\n  pwdLogin(password: $password, username: $username)\n}",
            "variables": {
                "password": self.password,
                "username": self.username
            },
            "operationName": "PwdLogin"
        }

        response = requests.post(self.login_url, headers=headers, json=payload)

        if response.status_code == 200:
            self.auth_token = response.json()['data']['pwdLogin']
            print(f"Auth token: {self.auth_token}")
        else:
            raise Exception(f"Failed to login and retrieve auth token: {response.status_code} {response.text}")

    def get_file_url(self, file_path):
        headers = {
            'authorization': self.auth_token,
            'origin': 'https://studio.apollographql.com',
            'referer': 'https://studio.apollographql.com/sandbox/explorer',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

        multipart_data = MultipartEncoder(
            fields={
                'operations': '{"query":"mutation Upload($file: Upload!) {\\n  upload(file: $file)\\n}","operationName":"Upload","variables":{"file":null}}',
                'map': '{"0":["variables.file"]}',
                '0': ('file', open(file_path, 'rb'), 'application/zip')
            }
        )

        headers['Content-Type'] = multipart_data.content_type

        response = requests.post(self.file_upload_url, headers=headers, data=multipart_data)

        if response.status_code == 200:
            file_url = response.json()['data']['upload']
            print(file_url)
            return file_url
        else:
            raise Exception(f"Failed to upload file: {response.status_code} {response.text}")

    def upload_file(self, name, base_model, file_path):
        if not self.auth_token:
            raise Exception("Authorization token not available. Please login first.")

        file_url = self.get_file_url(file_path)

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'authorization': self.auth_token,
            'content-type': 'application/json',
            'origin': 'https://studio.apollographql.com',
            'priority': 'u=1, i',
            'referer': 'https://studio.apollographql.com/sandbox/explorer',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

        payload = {
            "query": "mutation CreateAgent($input: CreateAgentInput!) {\n  createAgent(input: $input) {\n    id\n    name\n    resultUrl\n    baseModel\n  }\n}",
            "variables": {
                "input": {
                    "name": name,
                    "baseModel": base_model,
                    "resultUrl": file_url
                }
            }
        }

        response = requests.post(self.upload_url, headers=headers, json=payload)

        if response.status_code == 200:
            print('Upload successful:', response.json())
        else:
            print('Upload failed:', response.status_code, response.text)

# 使用
if __name__ == "__main__":
    login_url = 'https://dev-testing.imean.tech/graphql'
    upload_url = 'https://dev-testing.imean.tech/graphql'
    file_upload_url = 'https://dev-testing.imean.tech/graphql'
    # username = 'jackjin1997@gmail.com'
    # password = 'fatherjack'
    username = "icuicheng@foxmail.com"
    password = "4444#%cc"

    uploader = FileUploader(login_url, upload_url, file_upload_url, username, password)
    uploader.login()
    uploader.upload_file("TestModel", "BaseModelInfo", f"D:/KYXK/imean-agents/data/test.json")
