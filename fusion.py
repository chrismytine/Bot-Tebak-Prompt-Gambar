import json
import time
import requests
import base64  # untuk decode base64 ke gambar
from config import API_KEY, SECRET_KEY

class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, pipeline, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": prompt
            }
        }

        data = {
            'pipeline_id': (None, pipeline),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/pipeline/status/' + request_id, headers=self.AUTH_HEADERS)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            attempts -= 1
            time.sleep(delay)
        return None

    def save_image(self, base64_string, filepath):
        decoded_data = base64.b64decode(base64_string[0])
        with open (filepath, "wb") as f:
            f.write(decoded_data)
        
        print("Image saved to {filepath}!")

if __name__ == '__main__':
    # Ganti dengan API key dan secret key kamu
    api = FusionBrainAPI(
        'https://api-key.fusionbrain.ai/',
        API_KEY,
        SECRET_KEY
    )

    prompt = "istana terbang"
    pipeline_id = api.get_pipeline()
    uuid = api.generate(prompt, pipeline_id, images=1)
    files = api.check_generation(uuid)
    api.save_image(files, "generated_image.jpg")


