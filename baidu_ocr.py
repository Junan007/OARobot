import requests
import base64


class BaiduOcrParser(object):
    __api_host__ = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"

    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        
    def get_token(self):
        url = self.__api_host__ % (self.client_id, self.client_secret)
        resp = requests.post(url)
        if resp.status_code == 200:
            ret = resp.json()
            return ret["access_token"]
        else:
            return None

    @staticmethod
    def file_to_base64(image_file):
        with open(image_file, 'rb') as reader:
            base64_str = base64.b64encode(reader.read())
            return base64_str.decode('utf-8')

    def get_image_text(self, image_file):
        # TOFIX: You can cache you token from here.
        self.token = self.get_token()
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=%s" % (self.token)
        
        image_base64 = self.file_to_base64(image_file)
        params = {
            "image": image_base64
        }

        resp = requests.post(url, params=params)
        if resp.status_code == 200:
            ret = resp.json()
            words_result = ret['words_result']
            if len(words_result) > 0:
                return words_result[0]['words']        
        
        return None
   