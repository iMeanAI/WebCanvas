from lxml.html import etree
from io import StringIO
from collections import deque
import requests
import copy
from .utils import (
    ElementNode,
    TagNameList,
    DelTagNameList
)


class HTMLTree:
    def __init__(self):
        self.elementNodes = [ElementNode] * 100000
        self.rawNode2id: dict = {}
        self.element2id: dict = {}
        self.id2rawNode: dict = {}
        self.valid: list[bool] = [False] * 100000
        self.nodeCounts: int

    def fetch_html_content(self, html_content) -> None:
        parser = etree.HTMLParser()
        self.tree = etree.parse(StringIO(html_content), parser)
        root = self.tree.getroot()
        print("type",type(root))
        self.init_tree(root)
        self.build_tree(root)

    @staticmethod
    def build_node(node, idx) -> ElementNode:
        elementNode = ElementNode()
        elementNode["nodeId"] = idx
        elementNode["tagName"] = node.tag
        elementNode["text"] = node.text
        elementNode["attributes"] = node.attrib
        elementNode["childIds"] = []
        elementNode["parentId"] = ""
        elementNode["siblingId"] = ""
        elementNode["depth"] = 1
        elementNode["htmlContents"] = etree.tostring(
            node, pretty_print=True).decode()
        return elementNode

    def init_tree(self, root) -> None:
        queue = deque([root])
        i = 0
        while queue:
            vertex = queue.popleft()
            self.elementNodes[i] = HTMLTree().build_node(vertex, i)
            self.rawNode2id[vertex] = i
            i += 1
            for child in vertex.getchildren():
                queue.append(child)
        self.build_map()
        self.nodeCounts = i
        self.valid = self.valid[:self.nodeCounts + 1]

    def build_map(self) -> None:
        self.element2id = {value["nodeId"]: index for index,
                           value in enumerate(self.elementNodes)}
        self.id2rawNode = {str(index): value for value,
                           index in self.rawNode2id.items()}

    def get_elementId(self, node: ElementNode):
        return self.element2id[node["nodeId"]]

    def build_tree(self, root) -> None:
        queue = deque([root])
        rootId = self.rawNode2id[root]
        self.elementNodes[rootId]["parentId"] = -1
        while queue:
            vertex = queue.popleft()
            parentId = self.rawNode2id[vertex]
            for idx, child in enumerate(vertex.getchildren(), 1):
                childId = self.rawNode2id[child]
                self.elementNodes[parentId]["childIds"].append(childId)
                self.elementNodes[childId]["parentId"] = parentId
                self.elementNodes[childId]["siblingId"] = idx
                self.elementNodes[childId]["depth"] = self.elementNodes[parentId]["depth"] + 1
                queue.append(child)
        self.pruningTreeNode = copy.deepcopy(self.elementNodes)

    def bfs_tree(self) -> None:
        root = self.elementNodes[0]
        queue = deque([root])
        while queue:
            vertex = queue.popleft()
            for child_id in vertex["childIds"]:
                element = self.elementNodes[child_id]
                print(element["tagName"])
                queue.append(self.elementNodes[child_id])

    def pre_trav_tree(self) -> None:
        root = self.elementNodes[0]
        stack = [root]
        while stack:
            node = stack.pop()
            idx = self.get_elementId(node)
            self.get_node_info(idx)
            children = []
            for child_id in node["childIds"]:
                children.append(self.elementNodes[child_id])
            stack.extend(reversed(children))

    def get_node_info(self, idx: str, pruning: bool = True) -> None:
        if pruning is True:
            elementNode = self.pruningTreeNode[idx]
        else:
            elementNode = self.elementNodes[idx]
        print("*" * 10)
        print("nodeId: ", elementNode["nodeId"])
        print("childIds: ", elementNode["childIds"])
        print("parentId:", elementNode["parentId"])
        print("siblingId:", elementNode["siblingId"])
        print("depth:", elementNode["depth"])
        print("tagName: ", elementNode["tagName"])
        print("text: ", elementNode["text"])
        print("attributes: ", elementNode["attributes"])
        print("htmlContents:", elementNode["htmlContents"])
        print("*" * 10)
        print(" " * 10)

    def get_locator_path(self, idx: str) -> str:
        locator_str = ""
        current_node = self.elementNodes[idx]
        tag_name = current_node["tagName"]
        siblingId = str(current_node["siblingId"])
        # text = current_node["text"]
        # locator_str = "/" + tag_name + f"[text()=\"{text}\"]"
        locator_str = "/" + tag_name + "[" + siblingId + "]"
        while current_node["parentId"] != -1:
            parentid = current_node["parentId"]
            current_node = self.elementNodes[parentid]
            current_tag_name = current_node["tagName"]
            locator_str = "/" + current_tag_name + locator_str
        return locator_str

    def xpath_element(self, locator_str: str) -> str:
        try:
            elements = self.tree.xpath(locator_str)
            element = elements[0]
            return self.rawNode2id[element]
        except Exception as e:
            print(f"can't locate element, error {e}")
            return ""

    # 通过后续遍历判断，然后剪枝
    def pruning_tree(self) -> str:
        self.post_traver_judge_is_valid()
        result_list = []
        root = self.pruningTreeNode[0]
        stack = [root]
        while stack:
            node = stack.pop()
            nodeId = node["nodeId"]
            result_list.append(nodeId)
            children = []
            for childId in node["childIds"]:
                childNode = self.pruningTreeNode[childId]
                children.append(childNode)
            stack.extend(children)
        result = result_list[::-1]
        for nodeId in result:
            if self.valid[nodeId] is False:
                rawNode = self.id2rawNode[str(nodeId)]
                rawNode.getparent().remove(rawNode)
                current_node = self.pruningTreeNode[nodeId]
                current_node["htmlContents"] = ""
                parentid = current_node["parentId"]
                self.pruningTreeNode[parentid]["childIds"].remove(nodeId)
            else:
                rawNode = self.id2rawNode[str(nodeId)]
                html_contents = etree.tostring(
                    rawNode, pretty_print=True).decode()
                self.pruningTreeNode[nodeId]["htmlContents"] = html_contents
        return self.pruningTreeNode[0]["htmlContents"]

    def is_valid(self, idx) -> bool:
        if self.pruningTreeNode[idx]["tagName"] in TagNameList:
            return True

    # 通过后序遍历判断是否是有效tag
    def post_traver_judge_is_valid(self):
        result_list = []
        root = self.pruningTreeNode[0]
        if root is None:
            result_list = []
        stack = [root]
        while stack:
            node = stack.pop()
            nodeId = node["nodeId"]
            result_list.append(nodeId)
            children = []
            for childId in node["childIds"]:
                childNode = self.pruningTreeNode[childId]
                children.append(childNode)
            stack.extend(children)
        result = result_list[::-1]
        for nodeId in result:
            if self.is_valid(nodeId) or self.valid[nodeId] is True:
                self.valid[nodeId] = True
                current_id = nodeId
                while self.pruningTreeNode[current_id]["parentId"] != -1:
                    parent_id = self.pruningTreeNode[current_id]["parentId"]
                    self.valid[parent_id] = True
                    current_id = parent_id
            else:
                self.valid[nodeId] = False

    def get_html_contents(self, idx) -> str:
        node = self.elementNodes[idx]
        html_content = node["htmlContents"]
        return html_content

    def generate_contents(self) -> str:
        root = self.pruningTreeNode[0]
        stack = [root]
        contents = ""
        while stack:
            node = stack.pop()
            # if len(node["childIds"]) == 0 and self.valid[node["nodeId"]] is True:
            if self.valid[node["nodeId"]] is True:
                # TODO 添加可交互元素，主要是由该节点的tag和属性来判断
                content_text = HTMLTree().process_contents(node["text"])
                if content_text != "":
                    contents += " " * (node["depth"]-1) + "[" + str(node["nodeId"]) + "]" + \
                        " " + content_text + "\n"
            children = []
            for child_id in node["childIds"]:
                children.append(self.elementNodes[child_id])
            stack.extend(reversed(children))
        return contents

    def get_parents_id(self, idx) -> (str, str):
        parentid_str = ""
        parent_tag_str = ""
        current_node = self.elementNodes[idx]
        nodeId = current_node["nodeId"]
        tagName = current_node["tagName"]
        parent_tag_str += tagName + "->"
        parentid_str += str(nodeId) + "->"
        while current_node["parentId"] != -1:
            nodeId = current_node["parentId"]
            current_node = self.elementNodes[nodeId]
            tagName = current_node["tagName"]
            parent_tag_str += tagName + "->"
            parentid_str += str(nodeId) + "->"
        parentid_str += "-1"
        return parentid_str, parent_tag_str

    @staticmethod
    def process_contents(html_contents: str) -> str:
        if html_contents is None:
            return ""
        return html_contents.replace("\n", "").replace("\t", "")
