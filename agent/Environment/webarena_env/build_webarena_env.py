import json
import json5
import re

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from beartype import beartype
from beartype.door import is_bearable
from playwright.sync_api import (
    CDPSession,
    Page,
    Playwright,
    ViewportSize,
    expect,
    sync_playwright,
)

from typing import Dict, TypedDict
from gymnasium import spaces
from .utils import (
    AccessibilityTree,
    AccessibilityTreeNode,
    BrowserConfig,
    BrowserInfo,
    Observation,
)

ASCII_CHARSET = "".join(chr(x) for x in range(32, 128))
FREQ_UNICODE_CHARSET = "".join(chr(x) for x in range(129, 1000))
UTTERANCE_MAX_LENGTH = 8192
IN_VIEWPORT_RATIO_THRESHOLD = 0.6
IGNORED_ACTREE_PROPERTIES = (
    "focusable",
    "editable",
    "readonly",
    "level",
    "settable",
    "multiline",
    "invalid",
)


class ObservationProcessor:
    def process(self, page: Page, client: CDPSession) -> str:
        raise NotImplementedError


class ObservationMetadata(TypedDict):
    obs_nodes_info: dict[str, Any]


def create_empty_metadata() -> ObservationMetadata:
    return {
        "obs_nodes_info": {},
    }


class TextObervationProcessor(ObservationProcessor):
    def __init__(
        self,
        observation_type: str,
        current_viewport_only: bool,
        viewport_size: ViewportSize,
    ):
        self.observation_type = observation_type
        self.current_viewport_only = current_viewport_only
        self.viewport_size = viewport_size
        self.observation_tag = "text"
        self.meta_data = (
            create_empty_metadata()
        )  # use the store meta data of this observation type

    def fetch_browser_info(
        self,
        page: Page,
        client: CDPSession,
    ) -> BrowserInfo:
        # extract domtree
        tree = client.send(
            "DOMSnapshot.captureSnapshot",
            {
                "computedStyles": [],
                "includeDOMRects": True,
                "includePaintOrder": True,
            },
        )
        # calibrate the bounds, in some cases, the bounds are scaled somehow
        bounds = tree["documents"][0]["layout"]["bounds"]
        b = bounds[0]
        n = b[2] / self.viewport_size["width"]
        bounds = [[x / n for x in bound] for bound in bounds]
        tree["documents"][0]["layout"]["bounds"] = bounds

        # extract browser info
        win_top_bound = page.evaluate("window.pageYOffset")
        win_left_bound = page.evaluate("window.pageXOffset")
        win_width = page.evaluate("window.screen.width")
        win_height = page.evaluate("window.screen.height")
        win_right_bound = win_left_bound + win_width
        win_lower_bound = win_top_bound + win_height
        device_pixel_ratio = page.evaluate("window.devicePixelRatio")
        assert device_pixel_ratio == 1.0, "devicePixelRatio is not 1.0"
        config: BrowserConfig = {
            "win_top_bound": win_top_bound,
            "win_left_bound": win_left_bound,
            "win_width": win_width,
            "win_height": win_height,
            "win_right_bound": win_right_bound,
            "win_lower_bound": win_lower_bound,
            "device_pixel_ratio": device_pixel_ratio,
        }

        # assert len(tree['documents']) == 1, "More than one document in the DOM tree"
        info: BrowserInfo = {"DOMTree": tree, "config": config}

        return info

    @staticmethod
    def get_bounding_client_rect(
        client: CDPSession, backend_node_id: str
    ) -> dict[str, Any]:
        try:
            remote_object = client.send(
                "DOM.resolveNode", {"backendNodeId": int(backend_node_id)}
            )
            remote_object_id = remote_object["object"]["objectId"]
            response = client.send(
                "Runtime.callFunctionOn",
                {
                    "objectId": remote_object_id,
                    "functionDeclaration": """
                        function() {
                            if (this.nodeType == 3) {
                                var range = document.createRange();
                                range.selectNode(this);
                                var rect = range.getBoundingClientRect().toJSON();
                                range.detach();
                                return rect;
                            } else {
                                return this.getBoundingClientRect().toJSON();
                            }
                        }
                    """,
                    "returnByValue": True,
                },
            )
            return response
        except Exception as e:
            return {"result": {"subtype": "error"}}

    @staticmethod
    def get_element_in_viewport_ratio(
        elem_left_bound: float,
        elem_top_bound: float,
        width: float,
        height: float,
        config: BrowserConfig,
    ) -> float:
        elem_right_bound = elem_left_bound + width
        elem_lower_bound = elem_top_bound + height

        win_left_bound = 0
        win_right_bound = config["win_width"]
        win_top_bound = 0
        win_lower_bound = config["win_height"]

        # Compute the overlap in x and y axes
        overlap_width = max(
            0,
            min(elem_right_bound, win_right_bound)
            - max(elem_left_bound, win_left_bound),
        )
        overlap_height = max(
            0,
            min(elem_lower_bound, win_lower_bound)
            - max(elem_top_bound, win_top_bound),
        )

        # Compute the overlap area
        ratio = overlap_width * overlap_height / width * height
        return ratio

    def fetch_page_accessibility_tree(
        self,
        info: BrowserInfo,
        client: CDPSession,
        current_viewport_only: bool,
    ) -> AccessibilityTree:
        accessibility_tree: AccessibilityTree = client.send(
            "Accessibility.getFullAXTree", {}
        )["nodes"]
        # a few nodes are repeated in the accessibility tree
        seen_ids = set()
        _accessibility_tree = []
        for node in accessibility_tree:
            if node["nodeId"] not in seen_ids:
                _accessibility_tree.append(node)
                seen_ids.add(node["nodeId"])
        accessibility_tree = _accessibility_tree
        nodeid_to_cursor = {}
        for cursor, node in enumerate(accessibility_tree):
            nodeid_to_cursor[node["nodeId"]] = cursor
            # usually because the node is not visible etc
            if "backendDOMNodeId" not in node:
                node["union_bound"] = None
                continue
            backend_node_id = str(node["backendDOMNodeId"])
            if node["role"]["value"] == "RootWebArea":
                # always inside the viewport
                node["union_bound"] = [0.0, 0.0, 10.0, 10.0]
            else:
                response = self.get_bounding_client_rect(
                    client, backend_node_id
                )
                if response.get("result", {}).get("subtype", "") == "error":
                    node["union_bound"] = None
                else:
                    x = response["result"]["value"]["x"]
                    y = response["result"]["value"]["y"]
                    width = response["result"]["value"]["width"]
                    height = response["result"]["value"]["height"]
                    node["union_bound"] = [x, y, width, height]

        # filter nodes that are not in the current viewport
        if current_viewport_only:

            def remove_node_in_graph(node: AccessibilityTreeNode) -> None:
                # update the node information in the accessibility tree
                nodeid = node["nodeId"]
                node_cursor = nodeid_to_cursor[nodeid]
                parent_nodeid = node["parentId"]
                children_nodeids = node["childIds"]
                parent_cursor = nodeid_to_cursor[parent_nodeid]
                # update the children of the parent node
                assert (
                    accessibility_tree[parent_cursor].get("parentId", "Root")
                    is not None
                )
                # remove the nodeid from parent's childIds
                index = accessibility_tree[parent_cursor]["childIds"].index(
                    nodeid
                )
                accessibility_tree[parent_cursor]["childIds"].pop(index)
                # Insert children_nodeids in the same location
                for child_nodeid in children_nodeids:
                    accessibility_tree[parent_cursor]["childIds"].insert(
                        index, child_nodeid
                    )
                    index += 1
                # update children node's parent
                for child_nodeid in children_nodeids:
                    child_cursor = nodeid_to_cursor[child_nodeid]
                    accessibility_tree[child_cursor][
                        "parentId"
                    ] = parent_nodeid
                # mark as removed
                accessibility_tree[node_cursor]["parentId"] = "[REMOVED]"

            config = info["config"]
            for node in accessibility_tree:
                if not node["union_bound"]:
                    remove_node_in_graph(node)
                    continue

                [x, y, width, height] = node["union_bound"]

                # invisible node
                if width == 0 or height == 0:
                    remove_node_in_graph(node)
                    continue

                in_viewport_ratio = self.get_element_in_viewport_ratio(
                    elem_left_bound=float(x),
                    elem_top_bound=float(y),
                    width=float(width),
                    height=float(height),
                    config=config,
                )

                if in_viewport_ratio < IN_VIEWPORT_RATIO_THRESHOLD:
                    remove_node_in_graph(node)

            accessibility_tree = [
                node
                for node in accessibility_tree
                if node.get("parentId", "Root") != "[REMOVED]"
            ]
        return accessibility_tree

    @staticmethod
    def parse_accessibility_tree(
        accessibility_tree: AccessibilityTree,
    ) -> tuple[str, dict[str, Any]]:
        """Parse the accessibility tree into a string text"""
        node_id_to_idx = {}
        for idx, node in enumerate(accessibility_tree):
            node_id_to_idx[node["nodeId"]] = idx

        obs_nodes_info = {}

        def dfs(idx: int, obs_node_id: str, depth: int) -> str:
            tree_str = ""
            node = accessibility_tree[idx]
            indent = "\t" * depth
            valid_node = True
            try:
                role = node["role"]["value"]
                name = node["name"]["value"]
                node_str = f"[{obs_node_id}] {role} {repr(name)}"
                properties = []
                for property in node.get("properties", []):
                    try:
                        if property["name"] in IGNORED_ACTREE_PROPERTIES:
                            continue
                        properties.append(
                            f'{property["name"]}: {property["value"]["value"]}'
                        )
                    except KeyError:
                        pass

                if properties:
                    node_str += " " + " ".join(properties)

                # check valid
                if not node_str.strip():
                    valid_node = False

                # empty generic node
                if not name.strip():
                    if not properties:
                        if role in [
                            "generic",
                            "img",
                            "list",
                            "strong",
                            "paragraph",
                            "banner",
                            "navigation",
                            "Section",
                            "LabelText",
                            "Legend",
                            "listitem",
                        ]:
                            valid_node = False
                    elif role in ["listitem"]:
                        valid_node = False

                if valid_node:
                    tree_str += f"{indent}{node_str}"
                    obs_nodes_info[obs_node_id] = {
                        "backend_id": node["backendDOMNodeId"],
                        "union_bound": node["union_bound"],
                        "text": node_str,
                    }

            except Exception as e:
                valid_node = False

            for _, child_node_id in enumerate(node["childIds"]):
                if child_node_id not in node_id_to_idx:
                    continue
                # mark this to save some tokens
                child_depth = depth + 1 if valid_node else depth
                child_str = dfs(
                    node_id_to_idx[child_node_id], child_node_id, child_depth
                )
                if child_str.strip():
                    if tree_str.strip():
                        tree_str += "\n"
                    tree_str += child_str

            return tree_str

        tree_str = dfs(0, accessibility_tree[0]["nodeId"], 0)

        return tree_str, obs_nodes_info

    @staticmethod
    def clean_accesibility_tree(tree_str: str) -> str:
        """further clean accesibility tree"""
        clean_lines: list[str] = []
        for line in tree_str.split("\n"):
            if "statictext" in line.lower():
                prev_lines = clean_lines[-3:]
                pattern = r"\[\d+\] StaticText '([^']+)'"

                match = re.search(pattern, line)
                if match:
                    static_text = match.group(1)
                    if all(
                        static_text not in prev_line
                        for prev_line in prev_lines
                    ):
                        clean_lines.append(line)
            else:
                clean_lines.append(line)

        return "\n".join(clean_lines)

    def process(self, page: Page, client: CDPSession) -> str:
        # get the tab info
        open_tabs = page.context.pages
        try:
            tab_titles = [tab.title() for tab in open_tabs]
            current_tab_idx = open_tabs.index(page)
            for idx in range(len(open_tabs)):
                if idx == current_tab_idx:
                    tab_titles[
                        idx
                    ] = f"Tab {idx} (current): {open_tabs[idx].title()}"
                else:
                    tab_titles[idx] = f"Tab {idx}: {open_tabs[idx].title()}"
            tab_title_str = " | ".join(tab_titles)
        except Exception:
            tab_title_str = " | ".join(
                ["Tab {idx}" for idx in range(len(open_tabs))]
            )
        try:
            browser_info = self.fetch_browser_info(page, client)
        except Exception:
            page.wait_for_load_state("load", timeout=500)
            browser_info = self.fetch_browser_info(page, client)

        if self.observation_type == "accessibility_tree":
            accessibility_tree = self.fetch_page_accessibility_tree(
                browser_info,
                client,
                current_viewport_only=self.current_viewport_only,
            )
            content, obs_nodes_info = self.parse_accessibility_tree(
                accessibility_tree
            )
            # print("content: \n",content)
            # print("\n\nobs_nodes_info",obs_nodes_info)
            content = self.clean_accesibility_tree(content)
            # print("after clean_accesibility_tree",content)
            self.obs_nodes_info = obs_nodes_info
            self.meta_data["obs_nodes_info"] = obs_nodes_info
        else:
            raise ValueError(
                f"Invalid observatrion type: {self.observation_type}"
            )

        self.browser_config = browser_info["config"]
        content = f"{tab_title_str}\n\n{content}"

        return content

    def get_element_center(self, element_id: str) -> tuple[float, float]:
        node_info = self.obs_nodes_info[element_id]
        node_bound = node_info["union_bound"]
        x, y, width, height = node_bound
        center_x = x + width / 2
        center_y = y + height / 2
        return (
            center_x / self.viewport_size["width"],
            center_y / self.viewport_size["height"],
        )


class ObservationHandler:
    """Main entry point to access all observation processor"""

    def __init__(
        self,
        main_observation_type: str,
        text_observation_type: str,
        image_observation_type: str,
        current_viewport_only: bool,
        viewport_size: ViewportSize,
    ) -> None:
        self.main_observation_type = main_observation_type
        self.text_processor = TextObervationProcessor(
            text_observation_type, current_viewport_only, viewport_size
        )
        self.viewport_size = viewport_size

    def get_observation_space(self) -> spaces.Dict:
        text_space = spaces.Text(
            min_length=0,
            max_length=UTTERANCE_MAX_LENGTH,
            charset=ASCII_CHARSET + FREQ_UNICODE_CHARSET,
        )
        return spaces.Dict({"text": text_space})

    def get_observation(
        self, page: Page, client: CDPSession
    ) -> dict[str, Observation]:
        text_obs = self.text_processor.process(page, client)
        return {"text": text_obs}

    def get_observation_metadata(self) -> dict[str, ObservationMetadata]:
        return {
            "text": self.text_processor.meta_data
        }

    @property
    def action_processor(self) -> ObservationProcessor:
        """Return the main processor that is associated with the action space"""
        if self.main_observation_type == "text":
            return self.text_processor
        else:
            raise ValueError("Invalid main observation type")


class BrowserEnvironment:
    @beartype
    def __init__(
        self,
        max_page_length: int = 8192,
        headless: bool = True,
        slow_mo: int = 0,
        observation_type: str = "accessibility_tree",
        current_viewport_only: bool = False,
        viewport_size: ViewportSize = {"width": 1920, "height": 1080},
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

        match observation_type:
            case "html" | "accessibility_tree":
                self.text_observation_type = observation_type
                self.image_observation_type = ""
                self.main_observation_type = "text"
            case "image":
                self.image_observation_type = observation_type
                self.text_observation_type = ""  # type: ignore[assignment]
                self.main_observation_type = "image"
            case _:
                raise ValueError(
                    f"Unsupported observation type: {observation_type}"
                )

        self.observation_handler = ObservationHandler(
            self.main_observation_type,
            self.text_observation_type,
            self.image_observation_type,
            self.current_viewport_only,
            self.viewport_size,
        )

        self.observation_space = (
            self.observation_handler.get_observation_space()
        )

    def setup(self, start_url: None) -> None:
        self.context_manager = sync_playwright()
        self.playwright = self.context_manager.__enter__()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, slow_mo=self.slow_mo
        )
        start_url = start_url
        self.context = self.browser.new_context(
            viewport=self.viewport_size,
            device_scale_factor=1,
        )
        if start_url:
            start_urls = start_url.split(" |AND| ")
            for url in start_urls:
                page = self.context.new_page()
                client = page.context.new_cdp_session(
                    page
                )  # talk to chrome devtools
                if self.text_observation_type == "accessibility_tree":
                    client.send("Accessibility.enable")
                # type: ignore # TODO[shuyanzh], fix this hackey client
                page.client = client
                page.goto(url)
            self.page = self.context.pages[0]
            self.page.bring_to_front()
        else:
            self.page = self.context.new_page()
            client = self.page.context.new_cdp_session(self.page)
            if self.text_observation_type == "accessibility_tree":
                client.send("Accessibility.enable")
            self.page.client = client  # type: ignore

    def get_page_client(self, page: Page) -> CDPSession:
        return page.client  # type: ignore

    def _get_obs(self) -> dict[str, Observation]:
        obs = self.observation_handler.get_observation(
            self.page, self.get_page_client(self.page)
        )
        return obs

    def _get_obs_metadata(self) -> dict[str, ObservationMetadata]:
        metadata = self.observation_handler.get_observation_metadata()
        return metadata

    def reset(self, url):
        self.setup(url)
        observation = self._get_obs()
        observation_metadata = self._get_obs_metadata()
        return observation, observation_metadata
