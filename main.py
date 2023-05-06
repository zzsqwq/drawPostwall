# -*- coding: utf8 -*-
import logging
from io import BytesIO

import cv2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from painter import Painter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

avatar_size = (180, 180)
font_size = 20
img_size = (1080, 720)
scale = 2
enter_scale = 65


class Post(BaseModel):
    school: str
    postType: str
    postTitle: str
    postContent: str
    contactQQ: str
    contactWechat: str
    contactTelephone: str
    createTime: str
    updateTime: str


app = FastAPI()
painter = Painter()


@app.post("/api/v1/draw")
async def draw_post(post: Post):
    post_data = post.dict()
    logger.info("Post dict data: %s", post_data)
    img = painter.draw(post_data)
    image = cv2.imencode('.png', img)[1]
    # Base64 encode
    # image_code = str(base64.b64encode(image))[2:-1]
    return StreamingResponse(BytesIO(image.tobytes()), media_type="image/png")
    # img = get_img(post_data)
    # image = cv2.imencode('.png', img)[1]
    # image_code = str(base64.b64encode(image))[2:-1]
    # return image_code
