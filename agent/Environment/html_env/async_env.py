from playwright.async_api import async_playwright, Page
from playwright.sync_api import ViewportSize
from beartype.door import is_bearable
from urllib.parse import urlparse,urljoin
from collections import deque
from beartype import beartype
from lxml.html import etree
from io import StringIO


from .active_elements import ActiveElements
from .actions import Action, ActionTypes, create_action
from .utils import ElementNode, TagNameList, DelTagNameList
from .build_tree import HTMLTree

import requests
import copy


class AsyncHTMLEnvironment:
    @beartype
    def __init__(
        self,
        max_page_length: int = 8192,
        headless: bool = True,
        slow_mo: int = 0,
        current_viewport_only: bool = False,
        viewport_size: ViewportSize = {"width": 1280, "height": 720},
        save_trace_enabled: bool = False,
        sleep_after_execution: float = 0.0,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.current_viewport_only = current_viewport_only
        self.reset_finished = False
        self.viewport_size = viewport_size
        self.save_trace_enabled = save_trace_enabled
        self.sleep_after_execution = sleep_after_execution
        self.tree = HTMLTree()

    async def setup(self, start_url: str) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless, slow_mo=self.slow_mo
        )
        start_url = start_url
        self.context = await self.browser.new_context(
            viewport=self.viewport_size,
            device_scale_factor=1,
        )
        if start_url:
            self.page = await self.context.new_page()
            await self.page.goto(start_url)
            await self.page.wait_for_timeout(500)
            self.html_content = await self.page.content()
        else:
            self.page = await self.context.new_page()
            self.html_content = await self.page.content()

    async def _get_obs(self) -> str:
        try:
            self.tree.fetch_html_content(self.html_content)
            tab_name = await self.page.title()
            dom_tree = self.tree.build_dom_tree()
            # dom_tree = await self.get_dom_tree(self.tree,self.page)
            observation = f"current web tab name is \'{tab_name}\'\n" + dom_tree
        except:
            observation = ""
        return observation

    async def reset(self, start_url: str = "") -> str:
        await self.setup(start_url)
        observation = await self._get_obs()
        return observation

    async def execute_action(self, action: Action) -> str:
        '''找到可交互元素并执行相应的动作得到新的observation'''
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
                            print(f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                        if label == "link":
                            try:
                                element = self.tree.elementNodes[element_idx]
                                url = element["attributes"].get("href")
                                if bool(urlparse(url).netloc) is False:
                                    base_url = self.page.url()
                                    url = urljoin(base_url,url)
                                self.page = await self.context.new_page()
                                await self.page.goto(url)
                                self.html_content = await self.page.content()
                                return await self._get_obs()
                            except:
                                try:
                                    await self.page.locator(selector).click()
                                    self.html_content = await self.page.content()
                                    return await self._get_obs()
                                except Exception as e:
                                    print(e)
                        else:
                            try:
                                await self.page.locator(selector).click()
                                self.html_content = await self.page.content()
                                return await self._get_obs()
                            except Exception as e:
                                print(e)
                    except Exception as e:
                        print("can't execute click action")
                        print(e)
                        return ""
                case ActionTypes.GOTO:
                    try:
                        self.page = await self.context.new_page()
                        await self.page.goto(action["url"])
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print("can't execute goto action")
                        print(e)
                        return ""
                case ActionTypes.FILL_FORM:
                    try:
                        try:
                            label, element_idx = self.tree.get_tag_name(
                                self.tree.elementNodes[action["element_id"]])
                            action.update({"element_id": element_idx,
                                        "element_name": label})
                            selector, xpath = self.tree.get_selector_and_xpath(
                                action["element_id"])
                        except Exception as e:
                            print(f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                            print(e)
                        await self.page.locator(selector).fill(action["fill_text"])
                        await self.page.locator(selector).press("Enter")
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print("can't execute fill form action")
                        print(e)
                        return ""
                case ActionTypes.GOOGLE_SEARCH:
                    try:
                        self.page = await self.context.new_page()
                        await self.page.goto(action["url"])
                        search_box = await self.page.query_selector(
                            'textarea[name="q"]')
                        if search_box is not None:
                            await search_box.fill(action["fill_text"])
                            await self.page.click('input[type="submit"]')
                        self.html_content = await self.page.content()
                        return await self._get_obs()
                    except Exception as e:
                        print("can't execute google search action")
                        print(e)
                        return ""
                case _:
                    raise ValueError(
                        f"Unknown action type {action['action_type']}"
                    )
        except Exception as e:
            print("execute error")
            print(e)
        return ""

    async def get_page(self, element_id: int) -> (Page, str):
        try:
            selector = self.tree.get_selector(element_id)
        except:
            selector = ""
        return self.page, selector

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
    
    async def get_dom_tree(self,tree: HTMLTree,page: Page):
        root = tree.pruningTreeNode[0]
        stack = [root]
        contents = ""
        while stack:
            node = stack.pop()
            # if len(node["childIds"]) == 0 and self.valid[node["nodeId"]] is True:
            if tree.valid[node["nodeId"]] is True:
                content_text = HTMLTree.process_element_contents(node)
                if content_text != "":
                    tag_name, tag_idx = tree.get_tag_name(
                        node)
                    selector = tree.get_selector(tag_idx)
                    if tag_name.lower() != "statictext":
                        # if await self.is_valid_element(page, selector):
                        contents += "  " * (node["depth"]-1) + "[" + str(tag_idx) + "] " + tag_name + \
                            " " + f"\'{content_text}\'" + "\n"
            children = []
            for child_id in node["childIds"]:
                children.append(tree.pruningTreeNode[child_id])
            stack.extend(reversed(children))
        return contents
