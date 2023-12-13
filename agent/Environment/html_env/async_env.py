from playwright.async_api import async_playwright, Page
from playwright.sync_api import ViewportSize
from urllib.parse import urlparse, urljoin
from beartype import beartype


from .actions import Action, ActionTypes
from .build_tree import HTMLTree


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
                            print(
                                f"selector:{selector},label_name:{label},element_idx: {element_idx}")
                        if label == "link":
                            try:
                                element = self.tree.elementNodes[element_idx]
                                url = element["attributes"].get("href")
                                if bool(urlparse(url).netloc) is False:
                                    base_url = self.page.url()
                                    url = urljoin(base_url, url)
                                self.page = await self.context.new_page()
                                await self.page.goto(url)
                                self.html_content = await self.page.content()
                                return await self._get_obs()
                            except:
                                try:
                                    await self.page.evaluate('''() => {
                                        const element = document.querySelector('%s');
                                        if (element) {
                                            element.click();
                                        }
                                    }''' % selector)
                                    # await self.page.locator(selector).click()
                                    self.html_content = await self.page.content()
                                    return await self._get_obs()
                                except Exception as e:
                                    print(e)
                        else:
                            try:
                                await self.page.evaluate('''() => {
                                    const element = document.querySelector('%s');
                                    if (element) {
                                        element.click();
                                    }
                                }''' % selector)
                                # await self.page.locator(selector).click()
                                self.html_content = await self.page.content()
                                return await self._get_obs()
                            except Exception as e:
                                print(e)
                    except Exception as e:
                        print("can't execute click action")
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
                            print(
                                f"selector:{selector},label_name:{label},element_idx: {element_idx}")
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
                        # await self.page.locator(selector).fill(action["fill_text"])
                        # await self.page.locator(selector).press("Enter")
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
                        await self.page.evaluate('''(fill_text) => {
                            const searchBox = document.querySelector('textarea[name="q"]');
                            if (searchBox) {
                                searchBox.value = fill_text;
                                // 查找并点击提交按钮
                                const submitButton = document.querySelector('input[type="submit"]');
                                if (submitButton) {
                                    submitButton.click();
                                }
                            }
                        }''', action["fill_text"])
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