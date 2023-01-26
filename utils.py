import requests


def get_http_method_name(d: dict) -> str:
    return next(iter(d))


def get_sub_dict(d: dict, http_method: str) -> dict:
    return d[http_method]


def get_tag_name(sub_dict: dict) -> str:
    if not "tags" in sub_dict:
        return
    return sub_dict["tags"][0].lower()


def get_name_function(sub_dict: dict) -> str:
    return sub_dict["operationId"].split('_api')[0]


def get_dict_of_parameter(sub_dict: dict):
    if not "parameters" in sub_dict:
        return {}
    param = sub_dict["parameters"][0]
    return {"name": param["name"], "type": param["schema"]["type"]}


def all_needed_info_on_endpoint(all_paths, endpoint):
    path = all_paths[endpoint]
    http_method = get_http_method_name(path)
    sub_dict = get_sub_dict(path, http_method=http_method)
    tag_name = get_tag_name(sub_dict)
    function_name = get_name_function(sub_dict)
    dict_of_params = get_dict_of_parameter(sub_dict)
    return {
        "endpoint": endpoint,
        "http_method": http_method,
        "tag_name": tag_name,
        "function_name": function_name,
        "params": dict_of_params
    }


def get_all_info_from_json(json_url: str):
    apis = requests.get(json_url).json()
    all_paths = apis["paths"]
    list_info = []
    for path in all_paths.keys():
        info = all_needed_info_on_endpoint(all_paths, path)
        if info["tag_name"] == None:
            continue
        list_info.append(info)
    return list_info


def create_stringified_function_name(info_endpoint: dict):
    if info_endpoint["params"]:
        parameters_string = info_endpoint["params"]["name"] + ": " + info_endpoint["params"]["type"][0:3]
    else:
        parameters_string = ''
    if (info_endpoint["http_method"] == "post") or (info_endpoint["http_method"] == "put"):
        parameters_string += "data: dict"
    if parameters_string != '':
        parameters_string += ", "
    func_name = "def " + info_endpoint[
        "function_name"] + "(" + parameters_string + "base_url: str = base_url, endpoint: str = '" + info_endpoint[
                    "endpoint"] + "'):"
    return func_name


def create_stringified_function_request(info_endpoint: dict):
    base = "\ttry: \n\t\tres = requests." + info_endpoint["http_method"] + "(url=base_url+endpoint"
    if (info_endpoint["http_method"] == "post") or (info_endpoint["http_method"] == "put"):
        body_stringified = ", data=data) \n"
    else:
        if info_endpoint["params"]:
            body_stringified = "+ '/'" + f"+{info_endpoint['params']['name']}) \n"
        else:
            body_stringified = ").json() \n"
    base += body_stringified
    base += "\texcept requests.exceptions.HTTPError as err: \n\t\traise SystemExit(err)"
    base += "\n\treturn res"
    return base


def build_whole_python_function(func_header: str, func_body: str):
    return func_header + "\n" + func_body


def build_all_functions_from_info(all_info: list) -> dict:
    dict_tags_functions = {}
    for info in all_info:
        entire_function = build_whole_python_function(create_stringified_function_name(info),
                                                      create_stringified_function_request(info))
        if info["tag_name"] in dict_tags_functions:
            dict_tags_functions[info["tag_name"]] += [entire_function]
        else:
            dict_tags_functions[info["tag_name"]] = [entire_function]
    return dict_tags_functions


def from_json_to_functions(json_url: str) -> dict:
    all_info = get_all_info_from_json(json_url=json_url)
    return build_all_functions_from_info(all_info=all_info)


def write_functions_to_python_file_with_path(path_to_write_in: str, func_dict: dict, base_imports: str):
    for key in func_dict.keys():
        final_path = path_to_write_in + "/" + key + "_req.py"
        to_write = "\n\n\n".join(func_dict[key])
        with open(final_path, 'w') as f:
            f.write(base_imports + "\n\n\n")
            f.write(to_write)
            f.close
