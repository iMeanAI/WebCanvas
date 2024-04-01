from ...Utils.utils import is_valid_base64

from typing import Tuple, Any, Union

from playwright.async_api import async_playwright, Page
from playwright.sync_api import ViewportSize
from urllib.parse import urlparse, urljoin
from beartype import beartype
from difflib import SequenceMatcher

from PIL import Image
from io import BytesIO

import asyncio
import base64
import re

from .actions import Action, ActionTypes
from .build_tree import HTMLTree
import time

# Vimium 扩展的路径，需要自定义，相对路径会有点问题，导致路径切换为C:\\...\AppData\Local\ms-playwright\chromium-1055\chrome-win\\vimium-master
# 只有vision mode需要Vimium 扩展，run in d_v mode不需要
vimium_path = "D:\KYXK\imean-agents-dev\\vimium-master"

class VisionAsyncHTMLEnvironment:
    @beartype
    def __init__(
            self,
            # mode="dom",
            max_page_length: int = 8192,
            headless: bool = True,
            slow_mo: int = 0,
            current_viewport_only: bool = False,
            viewport_size: ViewportSize = {"width": 1280, "height": 720},
            save_trace_enabled: bool = False,
            sleep_after_execution: float = 0.0,
            locale: str = "en-US",
            use_vimium_effect=True
    ):
        self.use_vimium_effect = use_vimium_effect
        # self.mode = mode
        self.headless = headless
        self.slow_mo = slow_mo
        self.current_viewport_only = current_viewport_only
        self.reset_finished = False
        self.viewport_size = viewport_size
        self.save_trace_enabled = save_trace_enabled
        self.sleep_after_execution = sleep_after_execution
        self.tree = HTMLTree()
        self.locale = locale
        self.context = None
        self.browser = None

    async def setup(self, start_url: str) -> None:
        # if self.mode == "vision":
        # 暂时不考虑模式，直接使用vision模式
        if True:
            self.playwright = await async_playwright().start()
            self.context = await self.playwright.chromium.launch_persistent_context(
                "",
                headless=False,  # 设置是否为无头模式
                slow_mo=self.slow_mo,
                device_scale_factor=1,
                locale=self.locale,
                args=[
                    f"--disable-extensions-except={vimium_path}",
                    f"--load-extension={vimium_path}",  # 加载 Vimium 扩展
                ],
                ignore_https_errors=True,  # 忽略 HTTPS 错误
            )
        if start_url:
            self.page = await self.context.new_page()
            # await self.page.set_viewport_size({"width": 1080, "height": 720}) if not self.mode == "dom" else None
            await self.page.goto(start_url, timeout=6000)
            await self.page.wait_for_timeout(500)
            self.html_content = await self.page.content()
        else:
            self.page = await self.context.new_page()
            # await self.page.set_viewport_size({"width": 1080, "height": 720}) if not self.mode == "dom" else None
            self.html_content = await self.page.content()
        self.last_page = self.page

    async def get_obs(self) -> Union[str, Tuple[str, str]]:
        observation = ""
        observation_VforD = ""
        try:
            # if self.mode == "vision":
            # 视觉模式下的处理逻辑
            if self.use_vimium_effect:
                # 获取带有 Vimium 效果的屏幕截图
                observation = await self.capture_with_vim_effect()
            else:
                # 获取普通屏幕截图
                observation = await self.capture()
        except Exception as e:
            print(f"Error in _get_obs: {e}")
        return observation

    async def reset(self, start_url: str = "") -> Union[str, Tuple[str, str]]:
        await self.setup(start_url)

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def vision_execute_action(self, action: Action) -> str:
        if "done" in action:
            return True
        if "click" in action and "type" in action:
            await self.click(action["click"])
            await self.type(action["type"])
        if "navigate" in action:
            await self.navigate(action["navigate"])
        elif "type" in action:
            await self.type(action["type"])
        elif "click" in action:
            await self.click(action["click"])

    async def navigate(self, url):
        await self.page.goto(url=url if "://" in url else "https://" + url, timeout=60000)
        print("After navigate goto")

    async def type(self, text):
        time.sleep(1)
        for char in text:
            # Type each character individually
            await self.page.keyboard.type(char)
            await asyncio.sleep(0.1)  # Short delay between key presses
        # await self.page.keyboard.type(text)
        print(f"Typing text: {text}")
        await self.page.keyboard.press("Enter")

    async def click(self, text):
        await self.page.keyboard.type(text)

    async def capture_with_vim_effect(self) -> Image:
        # 确保页面已经加载
        if not self.page:
            raise ValueError("Page not initialized or loaded.")

        # 模拟 Vim 绑定键盘操作
        await self.page.keyboard.press("Escape")  # 退出可能的输入状态
        await self.page.keyboard.type("f")  # 激活 Vimium 的快捷键显示

        # 等待 Vimium 渲染快捷键
        await asyncio.sleep(1)  # 可能需要调整等待时间

        # 捕获屏幕截图
        screenshot_bytes = await self.page.screenshot()

        # 使用 PIL 库将截图转换为 RGB 格式的图像:
        # 使用 Python 的 BytesIO 类来处理截图的二进制数据，并使用 PIL（Python Imaging Library）库的 Image.open() 方法将其转换成一个图像对象。
        # 接着，使用 convert("RGB") 方法将图像转换为 RGB 格式。
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
        encoded_screenshot = self.encode_and_resize(screenshot)
        return encoded_screenshot

    @staticmethod
    def encode_and_resize(image):
        img_res = 1080
        w, h = image.size
        img_res_h = int(img_res * h / w)
        image = image.resize((img_res, img_res_h))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return encoded_image

    async def capture(self) -> Image:
        # 确保页面已经加载
        if not self.page:
            raise ValueError("Page not initialized or loaded.")

        # 捕获屏幕截图
        screenshot_bytes = ""
        for i in range(5):
            try:
                screenshot_bytes = await self.page.screenshot()
                break
            except:
                print("async_env.py capture screenshot_bytes failed for", i + 1, "times")
                await asyncio.sleep(1)

        print("async_env.py screenshot_bytes finished!")
        # 使用 PIL 库将截图转换为 RGB 格式的图像:
        # 使用 Python 的 BytesIO 类来处理截图的二进制数据，并使用 PIL（Python Imaging Library）库的 Image.open() 方法将其转换成一个图像对象。
        # 接着，使用 convert("RGB") 方法将图像转换为 RGB 格式。
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
        encoded_screenshot = self.encode_and_resize(screenshot)
        # 仅用于判断图片是否是base64编码，后期程序稳定时可以考虑删除
        is_valid, message = is_valid_base64(
            encoded_screenshot)
        print("async_env.py encoded_screenshot:", message)
        return encoded_screenshot

