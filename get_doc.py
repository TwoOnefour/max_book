import datetime
import os.path
import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from lxml import etree
import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

class MaxDoc:
    def __init__(self, url):
        self.url = url

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
        # session.verify = False
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68"
        })
        html = session.get(doc_url).text
        soup = BeautifulSoup(html, "html.parser")
        t = re.search(re.compile("(?:senddate:)(.*),"), str(soup.select("script"))).groups()[0].replace("'", "").strip(" ")
        view_token = re.search(re.compile("(?:view_token:)(.*)//预览的token"), str(soup.select("script"))).groups()[0].replace("'", "").strip(" ")
        project_id = 1
        aid = re.findall(re.compile("(?:aid:)(.*),"), str(soup.select("script")).strip(" "))[-1]
        actual_page = re.search(re.compile("(?:actual_page:)(.*),"), str(soup.select("script"))).groups()[0].strip(" ")
        format = re.search(re.compile("(?:format:)(.*),"), str(soup.select("script"))).groups()[0].strip(" ").strip("'")
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
                resp = session.get(f"https:{doc_url_dict[i]}", headers={
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                }, stream=True)
                with open(f"{path}\\{i}.gif", "wb") as f:
                    print(f"{str(datetime.datetime.now())[0:-7]}\t正在下载第{i}张图片...", end="")
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                    print("下载完成")
            self.print_msg("爬取完成，存放于脚本img目录下")
        self.images_to_pdf()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("用法：\npython3 get_doc.py url")
        sys.exit()
    get_doc = MaxDoc(sys.argv[1])  # 可以把url换成你要爬的文档url
    get_doc.run()
