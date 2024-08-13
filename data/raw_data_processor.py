import argparse
import re
from urllib.parse import unquote, parse_qs, urlparse
import json5
import ujson as json

def is_url(string):
    parsed = urlparse(string)
    return bool(parsed.scheme) and bool(parsed.netloc)

def process_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        json_file = json.load(f)

    print("JSON file loaded")

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

                # hack: put url in description in href
                if "description" in step.keys() and is_url(step["description"]):
                    step["href"] = step["description"]

                # hack: combine element value and element path
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
                    # element match
                    if "element" in temp["match_function_name"]:
                        url = urlparse(step["href"])
                        if url.netloc.startswith("www"):
                            netloc = re.findall(".*?\.(.*?)\..*?", url.netloc)[0]
                        else:
                            netloc = re.findall("(.*?)\..*?", url.netloc)[0]

                        # element path match
                        if "element_path_exact" in temp["match_function_name"]:
                            temp["method"] = "selector"
                            temp["content"] = {
                                "reference_answer": step["selector"], "netloc": netloc, "url": step["href"]
                            }

                        # element value match
                        elif "element_value_exact" in temp["match_function_name"]:
                            if "path" in temp["match_function_name"]:
                                temp["match_function_name"] = temp["match_function_name"].replace("_path", "")
                                temp["content"] = {
                                    "reference_answer": step["value"], "netloc": netloc, "path": step["selector"], "url": step["href"]
                                }
                            else:
                                temp["content"] = {
                                    "reference_answer": step["value"], "netloc": netloc, "url": step["href"]
                                }
                        elif "element_value_include" in temp["match_function_name"]:
                            if "path" in temp["match_function_name"]:
                                temp["match_function_name"] = temp["match_function_name"].replace("_path", "")
                                temp["content"] = {
                                    "reference_answer": func["required"], "netloc": netloc, "path": step["selector"], "url": step["href"]
                                }
                            else:
                                temp["content"] = {
                                    "reference_answer": func["required"], "netloc": netloc, "url": step["href"]
                                }
                        elif "element_value_semantic" in temp["match_function_name"]:
                            if "path" in temp["match_function_name"]:
                                temp["match_function_name"] = temp["match_function_name"].replace("_path", "")
                                temp["content"] = {
                                    "reference_answer": func["optional"], "netloc": netloc, "path": step["selector"], "url": step["href"]
                                }
                            else:
                                temp["content"] = {
                                    "reference_answer": func["optional"], "netloc": netloc, "url": step["href"]
                                }

                    # url match
                    elif "url_include" in temp["match_function_name"]:
                        key = func["key"] if "key" in func.keys() else ""
                        temp["content"] = {
                            "key": unquote(key),
                            "reference_answer": unquote(func["required"]),
                            "url": step["href"]
                        }
                    elif "url_exact" in temp["match_function_name"]:
                        key = func["key"] if "key" in func.keys() else ""
                        if "optional" in func.keys():
                            reference_answer = func["optional"]
                        elif len(key) > 0:
                            try:
                                parsed_url = urlparse(step["href"])
                                url_params = parse_qs(parsed_url.query)
                                reference_answer = url_params[unquote(key)][0]
                            except:
                                print("\nError in parsing URL!")
                                print("key to be parsed: ", key)
                                print("recorded url: ", step["href"])
                                input("\nPress Enter to ignore and continue processing.")
                        else:
                            reference_answer = step["href"]
                        key = unquote(key)
                        reference_answer = unquote(reference_answer)

                        temp["content"] = {
                            "key": key,
                            "reference_answer": reference_answer,
                            "url": step["href"]
                        }
                    elif "url_semantic" in temp["match_function_name"]:
                        key = func["key"] if "key" in func.keys() else ""
                        temp["content"] = {
                            "key": key,
                            "reference_answer": func["optional"],
                            "url": step["href"]
                        }
                        key = unquote(key)
                    elif "cache_data_exact" in temp["match_function_name"]:
                        temp["content"] = {
                            "reference_answer": step["value"],
                            "url": step["href"]
                        }
                    elif "cache_data_include" in temp["match_function_name"]:
                        temp["content"] = {
                            "reference_answer": unquote(func["required"]),
                            "url": step["href"]
                        }
                    elif "cache_data_semantic" in temp["match_function_name"]:
                        temp["content"] = {
                            "reference_answer": unquote(func["optional"]),
                            "url": step["href"]
                        }
                    elif "final_answer_exact" in temp["match_function_name"]:
                        temp["content"] = {
                            "reference_answer": step["value"],
                            "url": step["href"]
                        }
                    elif "final_answer_semantic" in temp["match_function_name"]:
                        temp["content"] = {
                            "reference_answer": unquote(func["optional"]),
                            "url": step["href"]
                        }
                    elif "final_answer_include" in temp["match_function_name"]:
                        temp["content"] = {
                            "reference_answer": unquote(func["required"]),
                            "url": step["href"]
                        }
                    else:
                        print("*" * 50, "\n", "other match function, coming soon!")
                    evaluation.append(temp)
        output.append({
            "index": index,
            "task": task_name,
            "reference_task_length": reference_steps,
            "evaluation": evaluation
        })

    with open(output_file, "w", encoding="utf-8") as f_out:
        json5.dump(output, fp=f_out, ensure_ascii=False, indent=4, quote_keys=True, trailing_commas=False)

def main():
    parser = argparse.ArgumentParser(description="Process JSON file and generate output.")
    parser.add_argument("--input-file", required=True, help="Input JSON file")
    parser.add_argument("--output-file", required=True, help="Output JSON file")
    args = parser.parse_args()

    process_file(args.input_file, args.output_file)

if __name__ == "__main__":
    main()

