import datetime
import os.path
import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from lxml import etree

class MaxDoc:
    def __init__(self, url):
        self.url = url

    def print_msg(self, msg):
        print(f"{str(datetime.datetime.now())[0:-7]}\t{msg}")

    def run(self):
        path = os.path.split(os.path.realpath(__file__))[0] + "\\img"
        if os.path.exists(path) and os.listdir(path + "\\") != []:
            self.print_msg("已存在文档，若想继续，请删除或者移动img目录")
            sys.exit()
        elif not os.path.exists(path):
            # print("检测到无img文件夹，创建文件")
            self.print_msg("检测到无img文件夹，创建文件")
            os.mkdir(path)
        doc_url = self.url  # 要爬的文档
        session = requests.session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68"
        })
        html = session.get(doc_url).text
        soup = BeautifulSoup(html, "html.parser")
        t = re.search(re.compile("(?:senddate:)(.*),"), str(soup.select("script")[5].next)).groups()[0].replace("'", "").strip(" ")
        view_token = re.search(re.compile("(?:view_token:)(.*)//预览的token"), str(soup.select("script")[5].next)).groups()[0].replace("'", "").strip(" ")
        project_id = 1
        aid = re.findall(re.compile("(?:aid:)(.*),"), str(soup.select("script")[5].next))[-1].strip(" ")
        actual_page = re.search(re.compile("(?:actual_page:)(.*),"), str(soup.select("script")[5].next)).groups()[0].strip(" ")
        format = re.search(re.compile("(?:format:)(.*),"), str(soup.select("script")[5].next)).groups()[0].strip(" ").strip("'")
        if format == "ppt":
            # res = session.get("https:" + view_token)
            # etree.HTMLParser(encoding="utf-8")
            # # tree = etree.parse(local_file_path)
            # tree = etree.HTML(res._content.decode("utf-8"))
            # session.get("https://view-cache.book118.com" + json.loads(str(tree.xpath("/html/body/div[1]/input[2]")[0].attrib).replace("'", "\""))["value"])
            self.print_msg(f"格式为ppt，无法下载，请访问此链接查看\nhttps:{view_token}")
        else:
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
                if url_list[0] != "j":
                    self.print_msg(json.loads(url_list)["message"])
                    return
                now = json.loads(url_list.strip("jsonpReturn(").strip(")")[:-2])
                if now["status"] != 200:
                    # print("未知错误")
                    self.print_msg("未知错误")
                    os.rmdir(path)
                    return
                for j in now["data"]:
                    if now["data"][j] != "" and doc_url_dict.get(j) is None:
                        doc_url_dict[j] = now["data"][j]
                # print(json.loads(url_list.strip("jsonpReturn(").strip(")")[:-2])["data"])
            # re.search(re.compile("(?:senddate:)(.*)") ,str(soup.select("script")[5].next)).groups() view_token
            # print(doc_url_dict)
            for i in doc_url_dict:
                with open(f"{path}\\{i}.png", "wb") as f:
                    print(f"{str(datetime.datetime.now())[0:-7]}\t正在下载第{i}张图片...", end="")
                    f.write(session.get(f"https:{doc_url_dict[i]}").content)
                    print("下载完成")
            self.print_msg("爬取完成，存放于脚本img目录下")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("用法：\npython3 get_doc.py url")
        sys.exit()
    get_doc = MaxDoc(sys.argv[1])  # 可以把url换成你要爬的文档url
    get_doc.run()
