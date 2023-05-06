import logging
import re
from datetime import datetime
from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image

from emoji2pic import Emoji2Pic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Painter(object):
    def __init__(self):
        self.avatar_size = (180, 180)
        self.font_size = 20
        self.img_size = (1080, 720)
        self.scale = 2
        self.enter_scale = 65

    def add_text(self, image, text, left, top, text_color=(0, 255, 0), text_size=20):
        # 判断是否为OpenCV图片类型
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # 创建一个可以在给定图像上绘图的对象
        instance = Emoji2Pic(text=text,
                             font="./font/SourceHanSansCN/SourceHanSansCN-Regular.ttf",
                             emoji_folder="AppleEmoji",
                             font_size=text_size,
                             line_space=text_size // 2.4,
                             font_color=text_color,
                             emoji_offset=text_size // 3,
                             width=int(640 * self.scale),
                             progress_bar=False)

        paste_img = instance.make_img()
        image.paste(paste_img, (left, top))

        return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def get_avatar(num):
        response = requests.get("http://q1.qlogo.cn/g?b=qq&nk=" + num + "&s=640")
        image = Image.open(BytesIO(response.content))
        img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        return img

    def get_circle_avatar(self, num, size=(128, 128)):
        avatar = Painter.get_avatar(num)
        avatar = cv2.resize(avatar, dsize=(int(size[0] * self.scale), int(size[1] * self.scale)))
        rows, cols, channel = avatar.shape
        circle_avatar = np.zeros((rows, cols, 1), np.uint8)
        circle_avatar[:, :, :] = 255  # 设置为全透明
        circle_avatar= cv2.circle(circle_avatar, (cols // 2, rows // 2), min(rows, cols) // 2, 0, -1)

        for i in range(rows):
            for j in range(cols):
                if circle_avatar[i][j] == 255:
                    avatar[i][j][0] = 255
                    avatar[i][j][1] = 255
                    avatar[i][j][2] = 255

        return avatar

    @staticmethod
    def get_qrcode_img(size=(288, 288)):
        qrcode = cv2.imread("./qrcode.png")
        qrcode = cv2.resize(qrcode, dsize=size)
        return qrcode

    @staticmethod
    def draw_dash_line(img, pointx, pointy, decay=10):
        xb, xe, y = pointx[0], pointy[0], pointx[1]
        decay2 = decay / 2
        points = list(range(xb, xe, 40))
        points.append(xe)
        for i in range(len(points)):
            if i != len(points) - 1:
                cv2.line(img, (round(points[i] + decay2), y), (round(points[i + 1] - decay2), y), (0, 0, 0), 1)
        return img

    def draw(self, post_data):
        keys = post_data.keys()

        english_re = re.compile(r'[\x00-\xff]', re.S)

        # Add detail text
        post_text = post_data["postContent"]
        post_text_space = ""
        len_a = 0
        enter_nums = 1
        for i in range(len(post_text)):
            post_text_space += post_text[i]
            if post_text[i] == '\n':
                len_a = 0
                enter_nums += 1
                continue
            if len(re.findall(english_re, post_text[i])) != 0:
                len_a += 1
            else:
                len_a += 2

            if len_a > 28:
                len_a = 0
                post_text_space += "\n"
                enter_nums += 1

        if enter_nums > 8:
            enter_nums = enter_nums - 8
        else:
            enter_nums = 0

        img = np.zeros((int(self.img_size[0] * self.scale) + int(enter_nums * self.scale * self.enter_scale),
                        int(self.img_size[1] * self.scale), 3),
                       np.uint8)
        img.fill(255)

        # Add avatar
        if ("contactQQ" in keys) and len(post_data["contactQQ"]) != 0:
            avatar_img = self.get_circle_avatar(post_data["contactQQ"], size=self.avatar_size)
        else:
            avatar_img = self.get_circle_avatar("2825467691", size=self.avatar_size)
        img[int(60 * self.scale):int(60 * self.scale) + int(self.avatar_size[0] * self.scale),
        int(270 * self.scale):int(270 * self.scale) + int(self.avatar_size[1] * self.scale), :] = avatar_img

        # Add time
        date_str = post_data["createTime"]
        # 2023-05-06T02:13:44" 格式转成 2023-05-06 02:13:44
        datetime_object = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        formatted_date_string = datetime_object.strftime("%Y-%m-%d %H:%M:%S")

        time_len = len(formatted_date_string) * 10
        img = self.add_text(img, formatted_date_string, int((self.img_size[1] - time_len) * self.scale // 2),
                            int(250 * self.scale),
                            (128, 128, 128),
                            text_size=int(20 * self.scale))

        post_type = "[" + post_data["postType"] + "]" + post_data["postTitle"]

        res = re.findall(english_re, post_type)
        logger.info('english character num')

        type_len = len(res) * 25 + (len(post_type) - len(res)) * 50
        img = self.add_text(img, post_type, int((self.img_size[1] - type_len) * self.scale // 2), int(280 * self.scale),
                            (0, 0, 255),
                            text_size=int(50 * self.scale))

        # Add split line
        cv2.line(img, (int(40 * self.scale), int(370 * self.scale)), (int(680 * self.scale), int(370 * self.scale)),
                 (0, 0, 0),
                 thickness=int(2 * self.scale))

        img = self.add_text(img, post_text, int(42 * self.scale), int(380 * self.scale), (0, 0, 0),
                            text_size=int(42 * self.scale))

        cv2.line(img, (int(40 * self.scale), int(860 * self.scale) + int(enter_nums * self.enter_scale * self.scale)),
                 (int(680 * self.scale), int(860 * self.scale) + int(enter_nums * self.enter_scale * self.scale)),
                 (0, 0, 0),
                 thickness=int(2 * self.scale))

        # Add contacts
        if ("contactQQ" in keys) and len(post_data["contactQQ"]) != 0:
            contact_qq = "Q Q ：" + post_data["contactQQ"]
        else:
            contact_qq = "Q Q ：" + "未填写"
        img = self.add_text(img, contact_qq, int(100 * self.scale),
                            int(895 * self.scale) + int(enter_nums * self.enter_scale * self.scale),
                            (0, 0, 255), int(22 * self.scale))
        if ("contactWechat" in keys) and len(post_data["contactWechat"]) != 0:
            contact_wechat = "微信：" + post_data["contactWechat"]
        else:
            contact_wechat = "微信：" + "未填写"
        img = self.add_text(img, contact_wechat, int(100 * self.scale),
                            int(945 * self.scale) + int(enter_nums * self.enter_scale * self.scale),
                            (0, 0, 255), int(22 * self.scale))
        if ("contactTelephone" in keys) and len(post_data["contactTelephone"]) != 0:
            contact_tel = "联系电话：" + post_data["contactTelephone"]
        else:
            contact_tel = "联系电话：" + "未填写"
        img = self.add_text(img, contact_tel, int(100 * self.scale),
                            int(995 * self.scale) + int(enter_nums * self.enter_scale * self.scale),
                            (0, 0, 255), int(22 * self.scale))

        qr_img = self.get_qrcode_img(size=(int(192 * self.scale), int(192 * self.scale)))
        img[
        int(865 * self.scale) + int(enter_nums * self.enter_scale * self.scale):int(1057 * self.scale) + int(
            enter_nums * self.enter_scale * self.scale),
        int(440 * self.scale):int(632 * self.scale), :] = qr_img

        return img
