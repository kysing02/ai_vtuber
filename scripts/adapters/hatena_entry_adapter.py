from requests.auth import HTTPBasicAuth
from xml.etree.ElementTree import Element, SubElement, tostring
import requests
import dotenv
import os
import logging

dotenv.load_dotenv()

class HatenaEntryAdapter:
    def __init__(self):
        self.hatena_id = os.getenv("HATENA_ID")
        self.blog_id = os.getenv("HATENA_BLOG_ID")
        self.url = f"https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_id}.hatenablog.com/atom"
        self.key = os.getenv("HATENA_KEY")
        # /entryエンドポイントを使用してデータを取得するための変数を設定
        endpoint = "/entry"
        self.req_endpoint = f"{self.url}{endpoint}"

    def post(self, title: str, content: str):
        xml_data = self.__to_xml(title, content)
        response = requests.post(self.req_endpoint, 
                         auth=HTTPBasicAuth(username=self.hatena_id, password=self.key),
                         headers={'Content-Type':'application/xml'}, data=xml_data)
        if response.status_code == 201:
            logging.info(f'Success to post: {response.status_code}')
            return True
        else:
            logging.info(f'Failed to post: {response.status_code}')
            print(response.text)

    def __to_xml(self, title: str, content: str):
        entry = Element("entry", xmlns="http://www.w3.org/2005/Atom")
        title_elm = SubElement(entry, "title")
        title_elm.text = title
        content_elm = SubElement(entry, "content", type="text/plain")
        content_elm.text = content
        return tostring(entry, encoding="utf-8", method='xml').decode('utf-8')

if __name__ == "__main__":
    adapter = HatenaEntryAdapter()
    print(adapter.post("test", "test"))