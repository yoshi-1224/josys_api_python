from josys_api_client import JosysApiClient
josys_api_client = None

def setup_api_client(config):
    global josys_api_client
    if josys_api_client is not None:
        return
    apiUserKey = config["josys_credentials"]["user_key"]
    apiUserSecret = config["josys_credentials"]["api_key"]
    if not apiUserKey or not apiUserSecret:
        raise ValueError("Josys API credentials not found")
    josys_api_client = JosysApiClient(apiUserKey, apiUserSecret)
    return josys_api_client

def get_josys_devices(config):
    global josys_api_client
    params = {
        "status": {
            "operator": "equals",
            "value": ["AVAILABLE", "IN_USE", "DECOMMISSIONED", "UNKNOWN"]
        }
    }
    results = josys_api_client.search_devices(params, 1000)
    if not results:
        return
    column_names, output_column_names = _get_josys_columns(config, "devices")
    results = [
        {output_column_names[column_names.index(key)]: value for key, value in device.items() if key in column_names}
        for device in results
    ]
    return results

def get_josys_members(config):
    global josys_api_client
    params = {
        "status": {
            "operator": "equals",
            "value": ["INITIATED", "ACTIVE"]
        }
    }
    results = josys_api_client.searchUserProfiles(params, 1000)
    if not results:
        return
    column_names, output_column_names = _get_josys_columns(config, "members")

    department_lookup = {}
    if "department_uuids" in column_names:
        print("部署一覧を作成します")
        for member in results:
            for name, uuid in zip(member.get("department_names", []), member.get("department_uuids", [])):
                department_lookup[name] = uuid

    for member in results:
        if "department_names" in member:
            member["department_names"] = member["department_names"][0] if member["department_names"] else ""
        if "department_uuids" in member:
            member["department_uuids"] = member["department_uuids"][0] if member["department_uuids"] else ""
    
    results = [
        {output_column_names[column_names.index(key)]: value for key, value in member.items() if key in column_names}
        for member in results
    ]

    return results, department_lookup

def _get_josys_columns(config, object_type):
    keys = list(config[object_type]['josys_columns'].keys())
    values = [config[object_type]['josys_columns'][key] for key in keys]
    keys.insert(0, 'uuid')
    values.insert(0, "ID")
    return keys, values

def upload_members(members):
    global josys_api_client
    results = []
    for m in members:
        m["status"] = member_status_mapping_jp2en[m["status"]]
        if "user_category" in m:
            m["user_category"] = user_category_mapping_jp2en[m["user_category"]]
        try:
            josys_api_client.create_user_profile(m)
            results.append("SUCCESSFUL")
        except Exception as error:
            results.append(str(error))
    return results

def update_members(members):
    global josys_api_client
    results = []
    for m in members:
        if "status" in m:
            m["status"] = member_status_mapping_jp2en[m["status"]]
        if "user_category" in m:
            m["user_category"] = user_category_mapping_jp2en[m["user_category"]]
        try:
            uuid = m["uuid"]
            del m["uuid"]
            res = josys_api_client.update_user_profile(uuid, m)
            if not res:
                results.append(f"UUID: {uuid} > 404 NOT FOUND")
            else:
                results.append(f"UUID: {uuid} > SUCCESSFUL")
        except Exception as error:
            results.append(f"UUID: {uuid} > {str(error)}")
    return results

member_status_mapping_jp2en = {
    "入社前": "INITIATED",
    "在籍中": "ACTIVE",
    "休職中": "SUSPENDED",
    "退職済": "TERMINATED",
    "不明": "UNKNOWN",
    "その他": "OTHERS",
}

user_category_mapping_jp2en = {
    "役員": "BOARD_MEMBER",
    "正社員": "FULL_TIME",
    "派遣社員": "TEMPORARY_EMPLOYEE",
    "業務委託": "SUBCONTRACTOR",
    "パート・アルバイト": "PART_TIME",
    "出向社員": "TRANSFEREE",
    "契約社員": "CONTRACTOR",
    "その他": "OTHERS",
    "システム": "SYSTEM",
    "外部": "EXTERNAL"
}
