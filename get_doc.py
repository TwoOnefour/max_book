import os.path
import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import json


class MaxDoc:
    def __init__(self, url):
        self.url = url

    def run(self):
        path = os.path.split(os.path.realpath(__file__))[0] + "\\img"
        if os.path.exists(path):
            print("已存在pdf，退出")
            sys.exit()
        else:
            os.mkdir(path)
        doc_url = self.url  # 要爬的文档
        session = requests.session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68"
        })
        html = session.get(doc_url).text
        soup = BeautifulSoup(html, "html.parser")
        t = re.search(re.compile("(?:senddate:)(.*)"), str(soup.select("script")[5].next)).groups()[0][2:-2]
        view_token = re.search(re.compile("(?:view_token:)(.*)"), str(soup.select("script")[5].next)).groups()[0].strip("//预览的token")[2:-2]
        project_id = 1
        aid = doc_url.split("/")[-1].split(".")[0]
        actual_page = re.search(re.compile("(?:actual_page:)(.*)"), str(soup.select("script")[5].next)).groups()[0].split(",")[0].strip(" ")
        doc_url_dict = {}
        for i in range(int(actual_page)):
            url_list = session.get("https://openapi.book118.com/getPreview.html", params={
                "t": t,
                "view_token": view_token,
                "project_id": project_id,
                "aid": aid,
                "page": i + 1
            }).text
            time.sleep(1)
            now = json.loads(url_list.strip("jsonpReturn(").strip(")")[:-2])["data"]
            for j in now:
                if doc_url_dict.get(j) is None and now[j] != "":
                    doc_url_dict[j] = now[j]
            # print(json.loads(url_list.strip("jsonpReturn(").strip(")")[:-2])["data"])
        # re.search(re.compile("(?:senddate:)(.*)") ,str(soup.select("script")[5].next)).groups() view_token
        # print(doc_url_dict)
        for i in doc_url_dict:
            with open(f"{path}\\{i}.png", "wb") as f:
                f.write(session.get(f"https:{doc_url_dict[i]}").content)
        print("爬取完成，存放于脚本img目录下")


if __name__ == "__main__":
    get_doc = MaxDoc("https://max.book118.com/html/2017/0122/86192397.shtm")  # 可以把url换成你要爬的文档url
    get_doc.run()
