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

from ...Prompt import D_VObservationPromptConstructor


# Vimium 扩展的路径，需要自定义，相对路径会有点问题，导致路径切换为C:\\...\AppData\Local\ms-playwright\chromium-1055\chrome-win\\vimium-master
# 只有vision mode需要Vimium 扩展，run in d_v mode不需要
vimium_path = "D:\KYXK\imean-agents-dev\\vimium-master"


async def select_option(page, selector, value):
    best_option = [-1, "", -1]
    for i in range(await page.locator(selector).count()):
        option = await page.locator(selector).nth(i).inner_text()
        similarity = SequenceMatcher(None, option, value).ratio()
        if similarity > best_option[2]:
            best_option = [i, option, similarity]
    await page.select_option(index=best_option[0], timeout=10000)
    return page


class AsyncHTMLEnvironment:
    @beartype
    def __init__(
        self,
        mode="dom",
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
        self.mode = mode
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
        if self.mode == "dom" or self.mode == "d_v":
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
            start_url = start_url
            self.context = await self.browser.new_context(
                viewport=self.viewport_size,
                device_scale_factor=1,
                locale=self.locale
            )
        if self.mode == "vision":
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
            await self.page.goto(start_url)
            await self.page.wait_for_timeout(500)
            self.html_content = await self.page.content()
        else:
            self.page = await self.context.new_page()
            # await self.page.set_viewport_size({"width": 1080, "height": 720}) if not self.mode == "dom" else None
            self.html_content = await self.page.content()
        self.last_page = self.page

    async def _get_obs(self) -> Union[str, Tuple[str, str]]:
        observation = ""
        observation_VforD = ""
        try:
            if self.mode in ["dom", "d_v"]:
                print("async_env.py now in _get_obs method")
                self.tree.fetch_html_content(self.html_content)
                print(
                    "async_env.py _get_obs fetch_html_content(self.html_content) finished!")
                tab_name = await self.page.title()
                dom_tree = self.tree.build_dom_tree()
                observation = f"current web tab name is \'{tab_name}\'\n" + \
                              "current accessibility tree is below:\n" + dom_tree
                if self.mode == "d_v":
                    observation_VforD = await self.capture()
            elif self.mode == "vision":
                # 视觉模式下的处理逻辑
                if self.use_vimium_effect:
                    # 获取带有 Vimium 效果的屏幕截图
                    observation = await self.capture_with_vim_effect()
                else:
                    # 获取普通屏幕截图
                    observation = await self.capture()
        except Exception as e:
            print(f"Error in _get_obs: {e}")
        if self.mode == "d_v":
            # byCarl: 仅用于判断图片是否是base64编码，后期程序稳定时可以考虑删除
            is_valid, message = D_VObservationPromptConstructor.is_valid_base64(
                observation_VforD)
            print("async_env.py _get_obs observation_VforD:", message)
        return (observation, observation_VforD) if self.mode == "d_v" else observation

    async def reset(self, start_url: str = "") -> Union[str, Tuple[str, str]]:
        await self.setup(start_url)
        if self.mode == "d_v":
            observation, observation_VforD = await self._get_obs()
            return observation, observation_VforD
        else:
            observation = await self._get_obs()
            return observation

    async def execute_action(self, action: Action) -> Union[str, Tuple[str, str]]:
        """
        找到可交互元素并执行相应的动作得到新的observation \n
        注意：本方法mode为d_v时，返回的分别observation和observation_VforD，在调用时需要分别接收 \n
        if mode == "d_v":
            observation, observation_VforD = await env.execute_action( )
        else:
            observation = await env.execute_action( )
        """
        if "element_id" in action and action["element_id"] != 0:
            print('action["element_id"]:', action["element_id"])
            print('tree.nodeDict[action["element_id"]]:',
                  self.tree.nodeDict[action["element_id"]])
            action["element_id"] = self.tree.nodeDict[action["element_id"]]
        try:
            match action["action_type"]:
                case ActionTypes.CLICK:
                    try:
                        try:
                            label, element_idx = self.tree.get_tag_name(
                                self.tree.elementNodes[action["element_id"]])
                            action.update({"element_id": element_idx,
                                           "element_name": label})
                            selector, xpath = self.tree.get_selector_and_xpath(
                                action["element_id"])
                        except Exception as e:
                            print(
                                f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                        if label == "link":
                            try:
                                element = self.tree.elementNodes[element_idx]
                                url = element["attributes"].get("href")
                                if bool(urlparse(url).netloc) is False:
                                    base_url = self.page.url()
                                    url = urljoin(base_url, url)
                                self.last_page = self.page
                                self.page = await self.context.new_page()
                                await self.page.goto(url)
                                await self.page.wait_for_load_state('load')
                                self.html_content = await self.page.content()
                                return await self._get_obs()
                            except:
                                try:
                                    self.last_page = self.page
                                    await self.page.evaluate('''() => {
                                        const element = document.querySelector('%s');
                                        if (element) {
                                            element.click();
                                        }
                                    }''' % selector)
                                    # await self.page.locator(selector).click()
                                    await self.page.wait_for_load_state('load')
                                    self.html_content = await self.page.content()
                                    return await self._get_obs()
                                except Exception as e:
                                    print(e)
                        else:
                            try:
                                self.last_page = self.page
                                await self.page.evaluate('''() => {
                                    const element = document.querySelector('%s');
                                    if (element) {
                                        element.click();
                                    }
                                }''' % selector)
                                # await self.page.locator(selector).click()
                                await self.page.wait_for_load_state('load')
                                self.html_content = await self.page.content()
                                return await self._get_obs()
                            except Exception as e:
                                print(e)
                    except Exception as e:
                        print("can't execute click action")
                        return await self._get_obs()
                case ActionTypes.GOTO:
                    try:
                        self.last_page = self.page
                        self.page = await self.context.new_page()
                        await self.page.goto(action["url"])
                        await self.page.wait_for_load_state('load', timeout=3000)
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print("can't execute goto action")
                        print(e)
                        return await self._get_obs()
                case ActionTypes.FILL_SEARCH:
                    try:
                        try:
                            self.last_page = self.page
                            label, element_idx = self.tree.get_tag_name(
                                self.tree.elementNodes[action["element_id"]])
                            action.update({"element_id": element_idx,
                                           "element_name": label})
                            selector, xpath = self.tree.get_selector_and_xpath(
                                action["element_id"])
                        except Exception as e:
                            print(
                                f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                        try:
                            self.last_page = self.page
                            await self.page.locator(selector).fill(action["fill_text"])
                            time.sleep(1)
                            print("sleep 1s")
                            await self.page.locator(selector).press("Enter")
                            await self.page.wait_for_load_state('load')
                            self.html_content = await self.page.content()
                            return await self._get_obs()
                        except:
                            print("sleep 2s")
                            self.last_page = self.page
                            fill_and_press_enter = '''() => {
                                        const element = document.querySelector('%s');
                                        if (element) {
                                            element.value = '%s';
                                            element.dispatchEvent(new Event('input', { bubbles: true }));
                                            element.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
                                        }
                                    }
                                ''' % (selector, action['fill_text'])
                            await self.page.evaluate(fill_and_press_enter)
                            await self.page.wait_for_load_state('load')
                            self.html_content = await self.page.content()
                            return await self._get_obs()
                    except Exception as e:
                        print("can't execute fill search action")
                        print(e)
                        return await self._get_obs()
                case ActionTypes.FILL_FORM:
                    try:
                        try:
                            self.last_page = self.page
                            label, element_idx = self.tree.get_tag_name(
                                self.tree.elementNodes[action["element_id"]])
                            action.update({"element_id": element_idx,
                                           "element_name": label})
                            selector, xpath = self.tree.get_selector_and_xpath(
                                action["element_id"])
                        except Exception as e:
                            print(
                                f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                        try:
                            self.last_page = self.page
                            await self.page.locator(selector).fill(action["fill_text"])
                            await self.page.wait_for_load_state('load')
                            self.html_content = await self.page.content()
                            return await self._get_obs()
                        except:
                            self.last_page = self.page
                            fill_and_press_enter = '''() => {
                                        const element = document.querySelector('%s');
                                        if (element) {
                                            element.value = '%s';
                                            element.dispatchEvent(new Event('input', { bubbles: true }));
                                        }
                                    }
                                ''' % (selector, action['fill_text'])
                            await self.page.evaluate(fill_and_press_enter)
                            await self.page.wait_for_load_state('load')
                            self.html_content = await self.page.content()
                            return await self._get_obs()
                    except Exception as e:
                        print("can't execute fill form action")
                        print(e)
                        return await self._get_obs()
                case ActionTypes.GOOGLE_SEARCH:
                    try:
                        self.last_page = self.page
                        self.page = await self.context.new_page()
                        await self.page.goto("https://www.google.com/search?q="+action["fill_text"])
                        await self.page.wait_for_load_state('load')
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print("can't execute google search action")
                        print(e)
                case ActionTypes.GO_BACK:
                    try:
                        self.page = self.last_page
                        self.last_page = self.page
                        await self.page.wait_for_load_state('load')
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print("can't execute go back action")
                        print(e)
                case ActionTypes.SELECT_OPTION:
                    try:
                        label, element_idx = self.tree.get_tag_name(
                            self.tree.elementNodes[action["element_id"]])
                        action.update({"element_id": element_idx,
                                       "element_name": label})
                        selector, xpath = self.tree.get_selector_and_xpath(
                            action["element_id"])
                    except Exception as e:
                        print(
                            f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                    try:
                        self.last_page = self.page
                        try:
                            await self.page.locator(selector).click()
                        except:
                            await self.page.evaluate('''() => {
                                const element = document.querySelector('%s');
                                if (element) {
                                    element.click();
                                }
                            }''' % selector)
                        self.page = await select_option(self.page, selector, action["fill_text"])
                        await self.page.wait_for_load_state('load')
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print(e)
                case ActionTypes.NONE:
                    try:
                        return await self._get_obs()
                    except:
                        print("can't execute none action")
                        print(e)
                case _:
                    raise ValueError(
                        f"Unknown action type {action['action_type']}"
                    )
        except Exception as e:
            print("execute error")
            print(e)
        return await self._get_obs()

    async def get_page(self, element_id: int) -> (Page, str):
        try:
            selector = self.tree.get_selector(element_id)
        except:
            selector = ""
        return self.page, selector

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

        await asyncio.sleep(1)  # 不等待可能会出现 Invalid base64 image_url
        # 捕获屏幕截图
        screenshot_bytes = await self.page.screenshot()
        print("async_env.py screenshot_bytes finished!")
        # 使用 PIL 库将截图转换为 RGB 格式的图像:
        # 使用 Python 的 BytesIO 类来处理截图的二进制数据，并使用 PIL（Python Imaging Library）库的 Image.open() 方法将其转换成一个图像对象。
        # 接着，使用 convert("RGB") 方法将图像转换为 RGB 格式。
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
        encoded_screenshot = self.encode_and_resize(screenshot)
        # byCarl: 仅用于判断图片是否是base64编码，后期程序稳定时可以考虑删除
        is_valid, message = D_VObservationPromptConstructor.is_valid_base64(
            encoded_screenshot)
        print("async_env.py encoded_screenshot:", message)
        return encoded_screenshot

    @staticmethod
    async def is_valid_element(page: Page, selector: str):
        element = await page.query_selector(selector)
        if element:
            if await element.is_visible() is False:
                return False
            elif await element.is_hidden() is True:
                return False
        else:
            return False
        return True
