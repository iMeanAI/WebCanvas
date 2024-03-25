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

from agent.Prompt import *


class ActionExecutionError(Exception):
    """自定义动作执行异常类"""

    def __init__(self, action_type, message, selector=None):
        self.action_type = action_type
        self.message = message
        self.selector = selector
        super().__init__(message)

class SelectorExecutionError(Exception):
    def __init__(self,message,selector=None):
        super().__init__(message)

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
        if self.mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
            self.context = await self.browser.new_context(
                viewport=self.viewport_size,
                device_scale_factor=1,
                locale=self.locale
            )
        if start_url:
            self.page = await self.context.new_page()
            # await self.page.set_viewport_size({"width": 1080, "height": 720}) if not self.mode == "dom" else None
            await self.page.goto(start_url, timeout=10000)
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
            # if self.mode in ["dom", "d_v", "dom_v_desc", "vision_to_dom"]:
            print("async_env.py now in _get_obs method")
            self.tree.fetch_html_content(self.html_content)
            print(
                "async_env.py _get_obs fetch_html_content(self.html_content) finished!")
            tab_name = await self.page.title()
            dom_tree = self.tree.build_dom_tree()
            observation = f"current web tab name is \'{tab_name}\'\n" + dom_tree
            if self.mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
                observation_VforD = await self.capture()
        except Exception as e:
            print(f"Error in get_obs: {e}")
        if self.mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
            # byCarl: 仅用于判断图片是否是base64编码
            is_valid, message = is_valid_base64(
                observation_VforD)
            print("async_env.py _get_obs observation_VforD:", message)
        return (observation, observation_VforD) if self.mode in ["d_v", "dom_v_desc", "vision_to_dom"] else observation

    async def reset(self, start_url: str = ""):
        await self.setup(start_url)
        # if self.mode in ["d_v", "dom_v_desc", "vision_to_dom"]:
        #     observation, observation_VforD = await self.get_obs()
        #     return observation, observation_VforD
        # else:
        #     observation = await self.get_obs()
        #     return observation

    async def click(self, action):
        try:
            label, element_id = self.tree.get_tag_name(
                self.tree.elementNodes[action["element_id"]])
            action.update({"element_id": element_id,
                           "element_name": label})
            selector, xpath = self.tree.get_selector_and_xpath(
                action["element_id"])
        except Exception as e:
            error_message = f"selector:{selector},label_name:{label},element_id: {element_id}"
            print(error_message)
        if label == "link":
            try:
                element = self.tree.elementNodes[element_id]
                url = element["attributes"].get("href")
                if bool(urlparse(url).netloc) is False:
                    base_url = self.page.url()
                    url = urljoin(base_url, url)
                self.last_page = self.page
                self.page = await self.context.new_page()
                await self.page.goto(url, timeout=10000)
                await self.page.wait_for_load_state('load')
                self.html_content = await self.page.content()
            except:
                try:
                    self.last_page = self.page
                    await self.page.evaluate('''() => {
                        var element = document.querySelector('%s');
                        if (element) {
                            element.click();
                        }
                    }''' % selector)
                    # await self.page.locator(selector).click()
                    await self.page.wait_for_load_state('load')
                    self.html_content = await self.page.content()
                except Exception as e:
                    raise e
        else:
            try:
                self.last_page = self.page
                try:
                    await self.page.locator(selector).click()
                except:
                    await self.page.evaluate('''() => {
                        var element = document.querySelector('%s');
                        if (element) {
                            element.click();
                        }
                    }''' % selector)
                    # await self.page.locator(selector).click()
                await self.page.wait_for_load_state('load')
                self.html_content = await self.page.content()
            except Exception as e:
                raise e

    async def goto(self, action):
        self.last_page = self.page
        self.page = await self.context.new_page()
        try:
            await self.page.goto(action["url"], timeout=20000)
        except TimeoutError:
            await self.retry_load_page(action["url"])
        except Exception as e:
            raise e
        await self.page.wait_for_timeout(3000)
        await self.page.wait_for_load_state('load')
        self.html_content = await self.page.content()

    async def fill_search(self, action):
        try:
            self.last_page = self.page
            label, element_id = self.tree.get_tag_name(
                self.tree.elementNodes[action["element_id"]])
            action.update({"element_id": element_id,
                           "element_name": label})
            selector, xpath = self.tree.get_selector_and_xpath(
                action["element_id"])
        except Exception as e:
            print(
                f"selector:{selector},label_name:{label},element_id: {element_id}")
        try:
            self.last_page = self.page
            await self.page.locator(selector).fill(action["fill_text"])
            await self.page.locator(selector).press("Enter")
            await self.page.wait_for_load_state('load')
            self.html_content = await self.page.content()
        except:
            try:
                self.last_page = self.page
                # fill_and_press_enter = '''() => {
                #             var element = document.querySelector('%s');
                #             if (element) {
                #                 element.value = '%s';
                #                 element.dispatchEvent(new Event('input', { bubbles: true }));
                #                 element.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
                #             }
                #         }
                #     ''' % (selector, action['fill_text'])
                # await self.page.evaluate(fill_and_press_enter)
                await self.page.evaluate(f'''
                    () => {{
                        var element = document.querySelector('{selector}');
                        if (element) {{
                            element.value = '{action['fill_text']}';
                            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            element.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter' }}));
                        }}
                    }}
                ''')
                await self.page.wait_for_load_state('load')
                self.html_content = await self.page.content()
            except Exception as e:
                raise e

    async def fill_form(self, action):
        try:
            self.last_page = self.page
            label, element_id = self.tree.get_tag_name(
                self.tree.elementNodes[action["element_id"]])
            action.update({"element_id": element_id,
                           "element_name": label})
            selector, xpath = self.tree.get_selector_and_xpath(
                action["element_id"])
        except Exception as e:
            print(
                f"selector:{selector},label_name:{label},element_id: {element_id}")
        try:
            self.last_page = self.page
            await self.page.locator(selector).fill(action["fill_text"])
            await self.page.wait_for_load_state('load')
            self.html_content = await self.page.content()
        except:
            try:
                self.last_page = self.page
                # fill = '''() => {
                #             var element = document.querySelector('%s');
                #             if (element) {
                #                 element.value = '%s';
                #                 element.dispatchEvent(new Event('input', { bubbles: true }));
                #             }
                #         }
                #     ''' % (selector, action['fill_text'])
                # await self.page.evaluate(fill)
                await self.page.evaluate(f'''
                    () => {{
                        var element = document.querySelector('{selector}');
                        if (element) {{
                            element.value = '{action['fill_text']}';
                            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }}
                ''')
                await self.page.wait_for_load_state('load')
                self.html_content = await self.page.content()
            except Exception as e:
                raise e

    async def search(self, action):
        self.last_page = self.page
        self.page = await self.context.new_page()
        await self.page.goto("https://www.google.com/search?q="+action["fill_text"], timeout=30000)
        await self.page.wait_for_timeout(2000)
        await self.page.wait_for_load_state('load')
        self.html_content = await self.page.content()

    async def go_back_last_page(self, action):
        self.page = self.last_page
        self.last_page = self.page
        await self.page.wait_for_load_state('load')
        self.html_content = await self.page.content()

    async def select_option(self, action):
        try:
            self.last_page = self.page
            label, element_id = self.tree.get_tag_name(
                self.tree.elementNodes[action["element_id"]])
            action.update({"element_id": element_id,
                           "element_name": label})
            selector, xpath = self.tree.get_selector_and_xpath(
                action["element_id"])
        except Exception as e:
            print(
                f"selector:{selector},label_name:{label},element_id: {element_id}")
        try:
            select_str = '''() => {
                // 选择select 下面的option
                var values = [];
                var selectElement = document.querySelector('%s');
                var options = selectElement.querySelectorAll('option');
                for (var option of options) {
                    values.push(option.innerText);
                }
                // 选择select下面optgroup下面的option
                var optgroups = selectElement.querySelectorAll('optgroup');
                for (var optgroup of optgroups) {
                    var label = optgroup.getAttribute('label');
                    var options = optgroup.querySelectorAll('option');
                    for (var option of options) {
                        values.push(option.innerText);
                    }   
                }
                return values;
            }''' % (selector)
            best_option = [-1, "", -1]
            optgroup_values = await self.page.evaluate(select_str)
            # print("Optgroup values:", optgroup_values)
            for i, option in enumerate(optgroup_values):
                similarity = SequenceMatcher(
                    None, option, action['fill_text']).ratio()
                if similarity > best_option[2]:
                    best_option = [i, option, similarity]
            # print("Best option:\n", best_option)
            await self.page.evaluate(f'''() => {{
                var selectElement = document.querySelector('{selector}');
                // 先在select下面找option
                var options = selectElement.querySelectorAll('option');
                for (var option of options) {{
                    if (option.innerText === "{best_option[1]}") {{
                        option.selected = true;
                        selectElement.dispatchEvent(new Event('change'));
                        return;
                    }}
                }}
                var optgroups = selectElement.querySelectorAll('optgroup');
                for (var optgroup of optgroups) {{
                    var options = optgroup.querySelectorAll('option');
                    for (var option of options) {{
                        if (option.innerText === "{best_option[1]}") {{
                            option.selected = true;
                            selectElement.dispatchEvent(new Event('change'));
                            return;
                        }}
                    }}
                }}
            }}''')
            await self.page.wait_for_timeout(2000)
            self.html_content = await self.page.content()
        except Exception as e:
            raise e

    async def hover(self, action):
        try:
            self.last_page = self.page
            label, element_id = self.tree.get_tag_name(
                self.tree.elementNodes[action["element_id"]])
            action.update({"element_id": element_id,
                           "element_name": label})
            selector, xpath = self.tree.get_selector_and_xpath(
                action["element_id"])
        except Exception as e:
            print(
                f"selector:{selector},label_name:{label},element_id: {element_id}")
        try:
            self.last_page = self.page
            await self.page.hover(selector)
            # await self.page.wait_for_load_state('load')
            self.html_content = await self.page.content()
        except:
            self.last_page = self.page
            hover = '''() => {
                        var element = document.querySelector('%s');
                        if (element) {
                            element.dispatchEvent(new Event('mouseover', { bubbles: true }));
                        }
                    }
                ''' % selector
            await self.page.evaluate(hover)
            self.html_content = await self.page.content()

    async def scroll_down(self):
        try:
            self.last_page = self.page
            # 获取页面的总高度
            total_height = await self.page.evaluate("document.body.scrollHeight")
            # 获取视窗的高度 720
            viewport_height = await self.page.evaluate("window.innerHeight")
            # self.viewport_size['height']
            # viewport_height = self.page.viewport_size['height']
            print("total_height:", total_height)
            print("viewport_height:", viewport_height)
            if total_height < viewport_height:
                await self.page.evaluate("window.scrollBy(0, 500)")
                print("scroll_down: By(0, 500)")
                self.html_content = await self.page.content()
            # 获取当前滚动位置
            current_scroll = await self.page.evaluate("window.pageYOffset")
            # 计算剩余高度
            remaining_height = total_height - current_scroll - viewport_height
            # 如果剩余高度小于或等于视窗高度，则滚动到页面底部
            if remaining_height <= viewport_height:
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                print(f"scroll_down: scrollTo(0, {total_height})")
            else:
                # 否则，根据需要滚动一定量，比如视窗高度的一半
                scroll_amount = current_scroll + viewport_height * 0.75
                await self.page.evaluate(f"window.scrollTo(0, {scroll_amount})")
                print(f"scroll_down: scrollTo(0, {scroll_amount})")
            self.html_content = await self.page.content()
        except:
            self.last_page = self.page
            await self.page.mouse.wheel(0, 100)
            print("scroll_down: mouse.wheel(0, 100)")
            self.html_content = await self.page.content()

    async def scroll_up(self):
        try:
            self.last_page = self.page
            # 获取视窗的高度
            viewport_height = await self.page.evaluate("window.innerHeight")
            # 获取当前滚动位置
            current_scroll = await self.page.evaluate("window.pageYOffset")
            # 如果当前滚动位置大于0，则向上滚动一定量
            if current_scroll > 0:
                if current_scroll < viewport_height:
                    scroll_amount = 0
                else:
                    scroll_amount = current_scroll - viewport_height / 2
                await self.page.evaluate(f"window.scrollTo(0, {scroll_amount})")
            self.html_content = await self.page.content()
        except:
            self.last_page = self.page
            await self.page.mouse.wheel(0, -100)
            self.html_content = await self.page.content()

    async def execute_action(self, action: Action) -> Union[str, Tuple[str, str]]:
        """
        """
        if "element_id" in action and action["element_id"] != 0:
            print('action["element_id"]:', action["element_id"])
            print('tree.nodeDict[action["element_id"]]:',
                  self.tree.nodeDict[action["element_id"]])
            action["element_id"] = self.tree.nodeDict[action["element_id"]]
        # try:
        match action["action_type"]:
            case ActionTypes.CLICK:
                try:
                    await self.click(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.GOTO:
                try:
                    await self.goto(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.FILL_SEARCH:
                try:
                    await self.fill_search(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.FILL_FORM:
                try:
                    await self.fill_form(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.GOOGLE_SEARCH:
                try:
                    await self.search(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.GO_BACK:
                try:
                    await self.go_back_last_page(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.SELECT_OPTION:
                try:
                    await self.select_option(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.HOVER:
                try:
                    await self.hover(action)
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.SCROLL_DOWN:
                try:
                    await self.scroll_down()
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.SCROLL_UP:
                try:
                    await self.scroll_up()
                except Exception as e:
                    error_message = f"can't execute {action['action_type']} action: {e}"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case ActionTypes.NONE:
                try:
                    await self.page.wait_for_load_state('load')
                    self.html_content = await self.page.content()
                except:
                    error_message = f"can't execute {action['action_type']} action:"
                    print(error_message)
                    raise ActionExecutionError(action['action_type'], error_message) from e
            case _:
                raise ValueError(
                    f"Unknown action type {action['action_type']}"
                )
        # except Exception as e:
        #     print("execute action error")
        #     print(e)

    async def get_page(self, element_id: int) -> Tuple[Page, str]:
        try:
            selector = self.tree.get_selector(element_id)
        except:
            selector = ""
        return self.page, selector

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

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

        # await self.page.wait_for_load_state("load")
        # await asyncio.sleep(1)  # 不等待可能会出现 Invalid base64 image_url
        # 捕获屏幕截图
        screenshot_bytes = ""
        for i in range(6):
            try:
                screenshot_bytes = await self.page.screenshot()
                break
            except:
                print("async_env.py capture screenshot_bytes failed for", i+1, "times")
                await asyncio.sleep(1)

        print("async_env.py screenshot_bytes finished!")
        # 使用 PIL 库将截图转换为 RGB 格式的图像:
        # 使用 Python 的 BytesIO 类来处理截图的二进制数据，并使用 PIL（Python Imaging Library）库的 Image.open() 方法将其转换成一个图像对象。
        # 接着，使用 convert("RGB") 方法将图像转换为 RGB 格式。
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
        encoded_screenshot = self.encode_and_resize(screenshot)
        # byCarl: 仅用于判断图片是否是base64编码，后期程序稳定时可以考虑删除
        is_valid, message = is_valid_base64(
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

    async def retry_load_page(self, url, max_retries=3):
        retry_count = 0
        while retry_count < max_retries:
            try:
                await self.page.goto(url, timeout=20000)
                return  # 成功加载页面，退出循环
            except TimeoutError:
                print(f"页面加载超时，重试中 ({retry_count + 1}/{max_retries})")
                retry_count += 1
        print("达到最大重试次数，无法加载页面。")