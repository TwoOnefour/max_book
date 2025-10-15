import datetime
import os.path
import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import yaml
from user import User


class MaxDoc:
    def __init__(self, url):
        self.image_path = None
        self.url = url
        self.session = requests.session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68"
        })
        self.user = None

        if not os.path.exists("config.yml"):
            return
        with open("config.yml", 'r') as f:
            cfg = yaml.load(f, Loader=yaml.Loader)
            user_cfg = cfg.get("user")
            username = user_cfg.get("username")
            password = user_cfg.get("password")
            if username and password:
                self.user = User(username, password, self.session)



    def images_to_pdf(self, image_folder="img", output_pdf_path="docs.pdf"):
        """
        将指定文件夹中的所有图片合并成一个PDF文件。
        
        :param image_folder: 存放图片的文件夹路径。
        :param output_pdf_path: 输出的PDF文件路径。
        """
        # 1. 获取所有图片文件的路径，并进行排序
        try:
            image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            # 按文件名进行自然排序（例如 '1.jpg', '2.jpg', '10.jpg'）
            image_files.sort(key=lambda f: int(''.join(filter(str.isdigit, f)) or 0))
            
            if not image_files:
                self.print_msg(f"错误：在文件夹 '{image_folder}' 中未找到任何图片文件。")
                return
                
            self.print_msg(f"找到 {len(image_files)} 张图片，将按以下顺序合并：")
            for f in image_files:
                print(f" - {f}")

        except FileNotFoundError:
            self.print_msg(f"错误：找不到文件夹 '{image_folder}'。请检查路径是否正确。")
            return

        # 2. 创建一个PDF文档
        # 使用第一张图片的尺寸作为PDF的页面尺寸
        first_image_path = os.path.join(image_folder, image_files[0])
        with Image.open(first_image_path) as img:
            width, height = img.size
            
        c = canvas.Canvas(output_pdf_path, pagesize=(width, height))

        # 3. 遍历所有图片并添加到PDF中
        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)
            try:
                with Image.open(image_path) as img:
                    img_width, img_height = img.size
                    # 设置当前页面的尺寸为当前图片的尺寸
                    c.setPageSize((img_width, img_height))
                    # 将图片绘制到PDF上
                    c.drawImage(ImageReader(img), 0, 0, width=img_width, height=img_height)
                    # 添加新的一页，为下一张图片做准备
                    c.showPage()
                    self.print_msg(f"已处理: {image_file}")
            except Exception as e:
                self.print_msg(f"处理文件 {image_file} 时出错: {e}")

        # 4. 保存PDF文件
        c.save()
        self.print_msg(f"成功！PDF已保存至: {output_pdf_path}")
    
    def print_msg(self, msg):
        print(f"{str(datetime.datetime.now())[0:-7]}\t{msg}")

    def check_img_path_exists(self):
        path = os.path.split(os.path.realpath(__file__))[0] + "\\img"
        if os.path.exists(path) and os.listdir(path + "\\") != []:
            self.print_msg("已存在文档，若想继续，请删除或者移动img目录")
            sys.exit()
        elif not os.path.exists(path):
            # print("检测到无img文件夹，创建文件")
            self.print_msg("检测到无img文件夹，创建文件")
            os.mkdir(path)
        self.image_path = path

    def get_and_parse_html(self):
        doc_url = self.url
        html = self.session.get(doc_url).text
        soup = BeautifulSoup(html, "html.parser")
        t = re.search(re.compile("(?:senddate:)(.*),"), str(soup.select("script"))).groups()[0].replace("'", "").strip(" ")
        view_token = re.search(re.compile("(?:view_token:)(.*)//预览的token"), str(soup.select("script"))).groups()[0].replace("'", "").strip(" ")
        project_id = 1
        aid = re.findall(re.compile("(?:aid:)(.*),"), str(soup.select("script")).strip(" "))[-1]
        actual_page = re.search(re.compile("(?:actual_page:)(.*),"), str(soup.select("script"))).groups()[0].strip(" ")
        preview_page = re.search(re.compile("(?:preview_page:)(.*),"), str(soup.select("script"))).groups()[0].strip(" ")
        format = re.search(re.compile("(?:format:)(.*),"), str(soup.select("script"))).groups()[0].strip(" ").strip("'")
        if format == "ppt":
            self.print_msg(f"格式为ppt，无法下载，请访问此链接查看\nhttps:{view_token}")
            sys.exit(-1)
        return t, view_token, project_id, aid, actual_page, preview_page

    def read_file_info(self):
        t, view_token, project_id, aid, actual_page, preview_page = self.get_and_parse_html()
        if actual_page != preview_page:
            self.print_msg(f"检测到 {actual_page} 页, 实际能阅读 {preview_page} 页，之后的内容需要登陆, 请填写config.yml并登录，若已填写请忽略此消息")
        interval = 2
        doc_url_dict = {}
        offset = 1
        c_aid = self.url.split("/").pop().strip(".shtm").strip("html")
        self.session.get(f"https://max.book118.com/user_center_v1/detail/View/limitReadGetView.html?aid={c_aid}")

        while offset < int(preview_page):
            url_list = self.session.get("https://openapi.book118.com/getPreview.html", params={
                "t": t,
                "view_token": view_token,
                "project_id": project_id,
                "aid": aid,
                "page": offset
            }).text
            time.sleep(interval)
            if url_list[0] != "j":
                self.print_msg(json.loads(url_list)["message"])
                return
            now = json.loads(url_list.strip("jsonpReturn(").strip(")")[:-2])
            if now['pages']['preview'] != preview_page:
                preview_page = now['pages']['preview']
            if now["status"] != 200:
                self.print_msg("未知错误")
                os.rmdir(self.image_path)
                return
            if now['data'].get(str(offset)) == '':
                self.print_msg(f"速率过快，重试api...")
                interval += 0.5
                continue

            for j in now["data"]:
                if now["data"][j] != "" and j not in doc_url_dict:
                    doc_url_dict[j] = now["data"][j]
                    offset += 1
                    if offset % 5 == 0:
                        self.print_msg(f"目前读取图片进度为: {offset / int(preview_page) * 100:.2f}%")

        return doc_url_dict

    def download_file(self, doc_url_dict):
        for i in doc_url_dict:
            resp = self.session.get(f"https:{doc_url_dict[i]}", headers={
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            }, stream=True)
            with open(f"{self.image_path}\\{i}.gif", "wb") as f:
                print(f"{str(datetime.datetime.now())[0:-7]}\t正在下载第{i}张图片...", end="")
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                print("下载完成")

    def login(self):
        if not self.user.login():
            return
        if not self.user.getUserInfo():
            return
        self.user.loginStatus = True

    def run(self):
        self.check_img_path_exists()
        if self.user:
            self.login()

        self.download_file(self.read_file_info())
        self.print_msg("爬取完成，存放于脚本img目录下")
        self.images_to_pdf()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("用法：\npython3 get_doc.py url")
        sys.exit()

    get_doc = MaxDoc(sys.argv[1])  # 可以把url换成你要爬的文档url
    get_doc.run()
