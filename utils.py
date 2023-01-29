import httpx


def get_http_method_name(d: dict) -> str:
    return next(iter(d))


def get_sub_dict(d: dict,
                 http_method: str) -> dict:
    return d[http_method]


def get_tag_name(sub_dict: dict) -> str:
    if "tags" not in sub_dict:
        return
    return sub_dict["tags"][0].lower()


def get_name_function(sub_dict: dict) -> str:
    return sub_dict["operationId"].split('_api')[0]


def get_dict_of_parameter(sub_dict: dict):
    if not "parameters" in sub_dict:
        return {}
    param = sub_dict["parameters"][0]
    return {"name": param["name"], "type": param["schema"]["type"]}


def all_needed_info_on_endpoint(all_paths,
                                endpoint: str):
    path = all_paths[endpoint]
    http_method = get_http_method_name(path)
    sub_dict = get_sub_dict(path, http_method=http_method)
    tag_name = get_tag_name(sub_dict)
    function_name = get_name_function(sub_dict)
    dict_of_params = get_dict_of_parameter(sub_dict)
    if dict_of_params:
        endpoint = endpoint.split('{')[0]
    return {
        "endpoint": endpoint,
        "http_method": http_method,
        "tag_name": tag_name,
        "function_name": function_name,
        "params": dict_of_params
    }


def get_all_info_from_json(json_url: str):
    apis = httpx.get(json_url).json()
    all_paths = apis["paths"]
    list_info = []
    for path in all_paths.keys():
        info = all_needed_info_on_endpoint(all_paths, path)
        if info["tag_name"] is None:
            continue
        list_info.append(info)
    return list_info


def create_stringified_function_name(info_endpoint: dict,
                                     async_client: bool):
    if info_endpoint["params"]:
        parameters_string = info_endpoint["params"]["name"] + ": " + info_endpoint["params"]["type"][0:3]
    else:
        parameters_string = ''
    if (info_endpoint["http_method"] == "post") or (info_endpoint["http_method"] == "put"):
        parameters_string += "data: dict"
    if parameters_string != '':
        parameters_string += ", "
    if async_client:
        name = "async def "
    else:
        name = "def "
    func_name = name + info_endpoint[
        "function_name"] + "(" + parameters_string + "cookies: dict = None, base_url: str = base_url, " \
                                                     "endpoint: str = '" + info_endpoint["endpoint"] + "'):"

    return func_name


def create_stringified_function_request(info_endpoint: dict,
                                        async_client: bool):
    if async_client:
        client = "await client."
    else:
        client = "httpx."
    base = f"\ttry: \n\t\tres = {client}" + info_endpoint["http_method"] + "(url=base_url+endpoint"
    if (info_endpoint["http_method"] == "post") or (info_endpoint["http_method"] == "put"):
        body_stringified = ", json=jsonable_encoder(data)"
    else:
        if info_endpoint["params"]:
            body_stringified = f"+{info_endpoint['params']['name']}"
        else:
            body_stringified = ""
    base += body_stringified
    base += ", cookies=cookies)\n\t\tif res.status_code >= 300:\n\t\t\traise HTTPException(" \
            "status_code=res.status_code, detail=res.json()['detail']) \n"
    base += "\texcept httpx.HTTPError as err: \n\t\traise SystemExit(err)"
    base += "\n\treturn res.json()"
    return base


def build_whole_python_function(func_header: str,
                                func_body: str):
    return func_header + "\n" + func_body


def build_all_functions_from_info(all_info: list,
                                  async_client: bool) -> dict:
    dict_tags_functions = {}
    for info in all_info:
        entire_function = build_whole_python_function(create_stringified_function_name(info, async_client=async_client),
                                                      create_stringified_function_request(info,
                                                                                          async_client=async_client))
        if info["tag_name"] in dict_tags_functions:
            dict_tags_functions[info["tag_name"]] += [entire_function]
        else:
            dict_tags_functions[info["tag_name"]] = [entire_function]
    return dict_tags_functions


def from_json_to_functions(json_url: str,
                           async_client: bool) -> dict:
    all_info = get_all_info_from_json(json_url=json_url)
    return build_all_functions_from_info(all_info=all_info, async_client=async_client)
