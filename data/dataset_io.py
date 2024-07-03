import argparse
import os
import zipfile
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
import requests

class GraphQLClient:
    def __init__(self):
        self.auth_token = None
        self.url = os.getenv('GRAPHQL_URL', 'https://www.imean.ai/graphql')
        self.username = os.getenv('GRAPHQL_USERNAME')
        self.password = os.getenv('GRAPHQL_PASSWORD')
        self.headers = {}
        self._validate_credentials()

    def _validate_credentials(self):
        if not self.username or not self.password:
            raise ValueError("Username or password is not set.")
        if len(self.username.strip()) < 1 or len(self.password.strip()) < 6:
            raise ValueError("Username or password is not valid.")

    def login(self):
        headers = self.headers

        payload = {
            "query": "mutation PwdLogin($password: String!, $username: String!) {\n  pwdLogin(password: $password, username: $username)\n}",
            "variables": {
                "password": self.password,
                "username": self.username
            },
            "operationName": "PwdLogin"
        }

        response = requests.post(self.url, headers=headers, json=payload)

        if response.status_code == 200:
            response_json = response.json()
            print(response_json)
            if 'data' in response_json and 'pwdLogin' in response_json['data']:
                self.auth_token = response_json['data']['pwdLogin']
                print(f"Auth token: {self.auth_token}")
            else:
                raise Exception(f"Unexpected response format: {response_json}")
        else:
            raise Exception(f"Failed to login and retrieve auth token: {response.status_code} {response.text}")

    def get_file_url(self, file_path):
        self._validate_file_path(file_path)

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

        response = requests.post(self.url, headers=headers, data=multipart_data)

        if response.status_code == 200:
            file_url = response.json()['data']['upload']
            print('file_url:', file_url)
            return file_url
        else:
            raise Exception(f"Failed to upload file: {response.status_code} {response.text}")

    def upload_file(self, name, base_model, file_path, challenge_id):
        if not self.auth_token:
            raise Exception("Authorization token not available. Please login first.")

        self._validate_file_path(file_path)
        self._validate_other_params(name, base_model, challenge_id)

        file_url = self.get_file_url(file_path)

        headers = {
            'accept': '*/*',
            'authorization': self.auth_token,
            'content-type': 'application/json'
        }

        data = {
            "query": """
            mutation CreateAgent($input: CreateAgentInput!) {
              createAgent(input: $input) {
                id
                name
                resultUrl
                baseModel
              }
            }
            """,
            "variables": {
                "input": {
                    "name": name,
                    "baseModel": base_model,
                    "resultUrl": file_url,
                    "challengeId": challenge_id
                }
            }
        }

        response = requests.post(self.url, headers=headers, json=data)

        if response.status_code == 200:
            print('Upload successful:', response.json())
        else:
            print('Upload failed:', response.status_code, response.text)

    def export_atom_flows(self, challenge_id, save_path):
        self.headers['authorization'] = self.auth_token
        self._validate_other_params(None, None, challenge_id)
        self._validate_save_path(save_path)

        data = {
            "query": "mutation AdminExportAtomFlowsOfChallenge($challengeId: String!) { "
                     "adminExportAtomFlowsOfChallenge(challengeId: $challengeId) }",
            "variables": {"challengeId": challenge_id},
            "operationName": "AdminExportAtomFlowsOfChallenge"
        }
        response = requests.post(self.url, headers=self.headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            print(response_data)
            if 'data' in response_data and 'adminExportAtomFlowsOfChallenge' in response_data['data']:
                zip_file_url = response_data['data']['adminExportAtomFlowsOfChallenge']
                self.download_and_extract_zip_file(zip_file_url, save_path)
        else:
            raise Exception(f"Failed to export atom flows: {response.status_code} {response.text}")

    @staticmethod
    def download_and_extract_zip_file(url, save_path):
        response = requests.get(url)
        if response.status_code == 200:
            zip_path = save_path + ".zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            # Unzip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(save_path)
            # Delete zip file
            os.remove(zip_path)
            print(f"File downloaded and extracted to {save_path}")
        else:
            raise Exception(f"Failed to download ZIP file: {response.status_code} {response.text}")

    @staticmethod
    def _validate_file_path(file_path):
        if not os.path.isfile(file_path):
            raise ValueError(f"The file path {file_path} does not exist or is not a file.")

    @staticmethod
    def _validate_save_path(save_path):
        if not os.path.isdir(save_path):
            raise ValueError(f"The save path {save_path} does not exist or is not a directory.")

    @staticmethod
    def _validate_other_params(name, base_model, challenge_id):
        if name and (len(name) < 3 or len(name) > 100):
            raise ValueError("Name must be between 3 and 100 characters long.")
        if base_model and (len(base_model) < 3 or len(base_model) > 100):
            raise ValueError("Base model must be between 3 and 100 characters long.")
        if not challenge_id or len(challenge_id) < 3:
            raise ValueError("Challenge ID must be at least 3 characters long.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GraphQL Client for iMean.ai")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")

    # Subparser for the upload command
    parser_upload = subparsers.add_parser("upload", help="Upload a file")
    parser_upload.add_argument("--file-path", required=True, help="Path to the file to be uploaded")
    parser_upload.add_argument("--challenge-id", required=True, help="Challenge ID for the upload")
    parser_upload.add_argument("--name", required=True, help="Name for the upload")
    parser_upload.add_argument("--base-model", required=True, help="Base model information for the upload")

    # Subparser for the download command
    parser_download = subparsers.add_parser("download", help="Download atom flows")
    parser_download.add_argument("--challenge-id", required=True, help="Challenge ID for the download")
    parser_download.add_argument("--save-path", required=True, help="Path to save the downloaded file")

    args = parser.parse_args()

    client = GraphQLClient()
    client.login()

    if args.command == "upload":
        client.upload_file(args.name, args.base_model, args.file_path, args.challenge_id)
    elif args.command == "download":
        client.export_atom_flows(args.challenge_id, args.save_path)


