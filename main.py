# -*- coding: utf8 -*-
import base64
import json
import os
import re
import time
from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from emoji2pic import Emoji2Pic

avatar_size = (180, 180)
font_size = 20
img_size = (1080, 720)
scale = 2
enter_scale = 65


def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    if isinstance(img, np.ndarray):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    # 创建一个可以在给定图像上绘图的对象
    instance = Emoji2Pic(text=text,
                         font="./font/SourceHanSansCN/SourceHanSansCN-Regular.ttf",
                         emoji_folder="AppleEmoji",
                         font_size=textSize,
                         line_space=textSize // 2.4,
                         font_color=textColor,
                         emoji_offset=textSize // 3,
                         width=int(640 * scale),
                         progress_bar=False)

    paste_img = instance.make_img()
    # test_img.save("example" + str(cnt) + ".jpg")
    # cnt = cnt + 1
    img.paste(paste_img, (left, top))

    # 字体的格式
    # fontStyle = ImageFont.truetype(
    #     "./font/SourceHanSansCN/SourceHanSansCN-Regular.ttf", textSize, encoding="utf-8")

    # fontStyle = ImageFont.truetype(
    #    "./font/EmojiOneColor-SVGinOT.ttf", textSize)
    # 绘制文本
    # draw.text((left, top), text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def get_avatar(qq_num):
    print(qq_num)
    print("test qq_num")
    response = requests.get("http://q1.qlogo.cn/g?b=qq&nk=" + qq_num + "&s=640")
    image = Image.open(BytesIO(response.content))
    img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    return img


def get_circle_avatar(qq_num, size=(128, 128)):
    avatar_img = get_avatar(qq_num)
    avatar_img = cv2.resize(avatar_img, dsize=(int(size[0] * scale), int(size[1] * scale)))
    rows, cols, channel = avatar_img.shape
    img_circle = np.zeros((rows, cols, 1), np.uint8)
    img_circle[:, :, :] = 255  # 设置为全透明
    img_circle = cv2.circle(img_circle, (cols // 2, rows // 2), min(rows, cols) // 2, 0, -1)

    for i in range(rows):
        for j in range(cols):
            if img_circle[i][j] == 255:
                avatar_img[i][j][0] = 255
                avatar_img[i][j][1] = 255
                avatar_img[i][j][2] = 255

    return avatar_img


def get_qrcode_img(size=(288, 288)):
    qr_img = cv2.imread("./qrcode.png")
    qr_img = cv2.resize(qr_img, dsize=size)
    return qr_img


def draw_dash_line(img, pointx, pointy, decay=10):
    xb = pointx[0]
    xe = pointy[0]
    y = pointx[1]
    decay2 = decay / 2
    points = list(range(xb, xe, 40))
    points.append(xe)
    for i in range(len(points)):
        if i != len(points) - 1:
            cv2.line(img, (round(points[i] + decay2), y), (round(points[i + 1] - decay2), y), (0, 0, 0), 1)
    return img


def get_img(post_data):
    keys = post_data.keys()

    english_re = re.compile(r'[\x00-\xff]', re.S)

    # add detail text
    post_text = post_data["post_text"]
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

    img = np.zeros((int(img_size[0] * scale) + int(enter_nums * scale * enter_scale), int(img_size[1] * scale), 3),
                   np.uint8)
    img.fill(255)

    # add avatar

    print(type(post_data))
    print(type(post_data["post_contact_qq"]))
    if ("post_contact_qq" in keys) and len(post_data["post_contact_qq"]) != 0:
        avatar_img = get_circle_avatar(post_data["post_contact_qq"], size=avatar_size)
    else:
        avatar_img = get_circle_avatar("2825467691", size=avatar_size)
    img[int(60 * scale):int(60 * scale) + int(avatar_size[0] * scale),
    int(270 * scale):int(270 * scale) + int(avatar_size[1] * scale), :] = avatar_img

    # add time
    # real_time = post_data["post_date"]
    # post_time = "投稿时间：" + real_time[0:4] + "/" + real_time[5:7] + "/" + real_time[8:10]
    # utc8
    post_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(post_data["post_time"]) + 28800))

    print(post_time)
    time_len = len(post_time) * 10
    img = cv2ImgAddText(img, post_time, int((img_size[1] - time_len) * scale // 2), int(250 * scale), (128, 128, 128),
                        textSize=int(20 * scale))

    post_type = "[" + post_data["post_type"] + "]" + post_data["post_title"]

    res = re.findall(english_re, post_type)
    print('english character num is:', res, len(res))

    type_len = len(res) * 25 + (len(post_type) - len(res)) * 50
    print(type_len)
    img = cv2ImgAddText(img, post_type, int((img_size[1] - type_len) * scale // 2), int(280 * scale), (0, 0, 255),
                        textSize=int(50 * scale))

    # post_title = post_data["post_title"]
    # img = cv2ImgAddText(img, post_title, 40 + font_size * len(post_type) + 70, 50, (0, 0, 255))
    # img = drawDashLine(img, (24, 180), (456, 180))
    # add split line
    cv2.line(img, (int(40 * scale), int(370 * scale)), (int(680 * scale), int(370 * scale)), (0, 0, 0),
             thickness=int(2 * scale))

    img = cv2ImgAddText(img, post_text, int(42 * scale), int(380 * scale), (0, 0, 0), textSize=int(42 * scale))

    cv2.line(img, (int(40 * scale), int(860 * scale) + int(enter_nums * enter_scale * scale)),
             (int(680 * scale), int(860 * scale) + int(enter_nums * enter_scale * scale)), (0, 0, 0),
             thickness=int(2 * scale))
    if ("post_contact_qq" in keys) and len(post_data["post_contact_qq"]) != 0:
        contact_qq = "Q Q ：" + post_data["post_contact_qq"]
    else:
        contact_qq = "Q Q ：" + "未填写"
    img = cv2ImgAddText(img, contact_qq, int(100 * scale), int(895 * scale) + int(enter_nums * enter_scale * scale),
                        (0, 0, 255), int(22 * scale))
    if ("post_contact_wechat" in keys) and len(post_data["post_contact_wechat"]) != 0:
        contact_wechat = "微信：" + post_data["post_contact_wechat"]
    else:
        contact_wechat = "微信：" + "未填写"
    img = cv2ImgAddText(img, contact_wechat, int(100 * scale), int(945 * scale) + int(enter_nums * enter_scale * scale),
                        (0, 0, 255), int(22 * scale))
    if ("post_contact_tel" in keys) and len(post_data["post_contact_tel"]) != 0:
        contact_tel = "联系电话：" + post_data["post_contact_tel"]
    else:
        contact_tel = "联系电话：" + "未填写"
    img = cv2ImgAddText(img, contact_tel, int(100 * scale), int(995 * scale) + int(enter_nums * enter_scale * scale),
                        (0, 0, 255), int(22 * scale))

    qr_img = get_qrcode_img(size=(int(192 * scale), int(192 * scale)))
    img[
    int(865 * scale) + int(enter_nums * enter_scale * scale):int(1057 * scale) + int(enter_nums * enter_scale * scale),
    int(440 * scale):int(632 * scale), :] = qr_img

    return img


def main():
    # print("Received raw event", event)

    with open("./test_data.json", "r") as f:
        post_data = json.load(f)

    img = get_img(post_data)

    # cv2.imshow("img", img)
    cv2.imwrite("test.png", img)

    # image = cv2.imencode('.png', img)[1]
    #
    # image_code = str(base64.b64encode(image))[2:-1]
    #
    # return image_code


if __name__ == '__main__':
    main()
