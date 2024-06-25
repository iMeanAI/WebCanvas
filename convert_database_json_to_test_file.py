import re
from urllib.parse import unquote
from urllib.parse import parse_qs, urlparse
import json5
import ujson as json


def is_url(string):
    parsed = urlparse(string)
    print(parsed)
    return bool(parsed.scheme) and bool(parsed.netloc)

f = open("output_group1_20240228.json", "r", encoding="utf-8")
json_file = json.load(f)

print("json load")

output = []

for index, task in enumerate(json_file):
    task_name = task["title"]
    evaluation = []
    print("task_name:", task_name)
    steps = task["steps"]
    reference_steps = len(steps)
    print("reference_steps:", reference_steps)
    for step in steps:
        if "rewardFunction" in step.keys() and len(step["rewardFunction"]) > 0:

            #! Hack: Update description to href
            if "description" in step.keys() and is_url(step["description"]):
                step["href"] = step["description"]

            #! hack: Merge element value and element path
            flag_value = False
            flag_path = False
            for func in step["rewardFunction"]:
                if "element_value" in func["name"]:
                    flag_value = True
                if "element_path" in func["name"]:
                    flag_path = True
            if flag_value and flag_path:
                for idx, func in enumerate(step["rewardFunction"]):
                    if "element_value" in func["name"]:
                        func["name"] = f'{func["name"]}_path'
                    if "element_path" in func["name"]:
                        del_idx = idx
                del step["rewardFunction"][del_idx]
            for func in step["rewardFunction"]:
                if len(func) == 0:
                    break
                temp = {}
                temp["match_function_name"] = func["name"]
                # print("function:", func)

                # *element match
                if "element" in temp["match_function_name"]:

                    # extract the domain name, such as extracting "zhihu" from zhihu.com, and "google" from www.google.com.hk
                    url = urlparse(step["href"])
                    if url.netloc.startswith("www"):
                        netloc = re.findall(".*?\.(.*?)\..*?", url.netloc)[0]
                    else:
                        netloc = re.findall("(.*?)\..*?", url.netloc)[0]

                    # *element path match
                    if "element_path_exact" in temp["match_function_name"]:
                        temp["method"] = "selector"
                        temp["content"] = {
                            "reference_answer": step["selector"], "netloc": netloc,"url":step["href"]}

                    # *element value match
                    elif "element_value_exact" in temp["match_function_name"]:
                        if "path" in temp["match_function_name"]:
                            temp["match_function_name"] = temp["match_function_name"].replace(
                                "_path", "")
                            temp["content"] = {
                                "reference_answer": step["value"], "netloc": netloc, "path": step["selector"],"url":step["href"]}
                        else:
                            temp["content"] = {
                                "reference_answer": step["value"], "netloc": netloc,"url":step["href"]}
                    elif "element_value_include" in temp["match_function_name"]:
                        if "path" in temp["match_function_name"]:
                            temp["match_function_name"] = temp["match_function_name"].replace(
                                "_path", "")
                            temp["content"] = {
                                "reference_answer": func["required"], "netloc": netloc, "path": step["selector"],"url":step["href"]}
                        else:
                            temp["content"] = {
                                "reference_answer": func["required"], "netloc": netloc,"url":step["href"]}
                    elif "element_value_semantic" in temp["match_function_name"]:
                        if "path" in temp["match_function_name"]:
                            temp["match_function_name"] = temp["match_function_name"].replace(
                                "_path", "")
                            temp["content"] = {
                                "reference_answer": func["optional"], "netloc": netloc, "path": step["selector"],"url":step["href"]}
                        else:
                            temp["content"] = {
                                "reference_answer": func["optional"], "netloc": netloc,"url":step["href"]}

                # *url match
                elif "url_include" in temp["match_function_name"]:
                    key = func["key"] if "key" in func.keys() else ""
                    temp["content"] = {"key": unquote(key),
                                       "reference_answer": unquote(func["required"]),
                                       "url":step["href"]}
                elif "url_exact" in temp["match_function_name"]:
                    key = func["key"] if "key" in func.keys() else ""
                    if "optional" in func.keys():
                        reference_answer = func["optional"]
                    elif len(key) > 0:
                        try:
                            parsed_url = urlparse(step["href"])
                            # print(key)
                            url_params = parse_qs(parsed_url.query)
                            # print(url_params)
                            reference_answer = url_params[unquote(key)][0]
                        except:
                            print("Error in parsing URL!")
                            input()
                    else:
                        reference_answer = step["href"]
                        # print(reference_answer)
                    key = unquote(key)
                    reference_answer = unquote(reference_answer)

                    # reference_answer = func["optional"] if "optional" in func.keys() else step["href"]
                    temp["content"] = {"key": key,
                                       "reference_answer": reference_answer,
                                       "url":step["href"]}
                elif "url_semantic" in temp["match_function_name"]:
                    key = func["key"] if "key" in func.keys() else ""
                    temp["content"] = {"key": key,
                                       "reference_answer": func["optional"],
                                       "url":step["href"]}
                    key = unquote(key)
                else:
                    print("*"*50, "\n", "other match function, coming soon!")
                # print(temp)
                evaluation.append(temp)
    # print(evaluation)
    # input()
    output.append({"index": index, "task": task_name,
                  "reference_task_length": reference_steps, "evaluation": evaluation})
# print(output)

f_out = open("group1_20240228.json", "w")
json5.dump(output, fp=f_out, ensure_ascii=False, indent=4,
           quote_keys=True, trailing_commas=False)
