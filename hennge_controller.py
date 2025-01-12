from hennge_api_client import HenngeApiClient

def get_hennge_members(config):
    client_id = config["members"]["source_credentials"]["client_id"]
    client_secret = config["members"]["source_credentials"]["client_secret"]
    if not client_id or not client_secret:
        raise ValueError(f"HENNGEのclient_id, client_secretが見つかりませんでした")
    results = HenngeApiClient(client_id, client_secret).get_members()
    if not results:
        return
    column_names, output_column_names = _get_hennge_columns(config)
    results = [
        {output_column_names[column_names.index(key)]: value for key, value in member.items() if key in column_names}
        for member in results
    ]

    for func in _custom_functions_per_item():
        results = [func(member) for member in results]
    return results
    
def _get_hennge_columns(config):
    keys = list(config["members"]['source_columns'].keys())
    values = [config["members"]['source_columns'][key] for key in keys]
    return keys, values

def _custom_functions_per_item():
    functions = []
    def convert_to_josys_status(member):
        if member.get("ステータス") == "enabled":
            member["ステータス"] = "在籍中"
            member["退職日"] = None
        else:
            member["ステータス"] = "退職済"
            from datetime import datetime
            member["退職日"] = datetime.now().strftime("%Y-%m-%d")
        return member
    
    def ensure_date_format_in_josys_format(member):
        def format_date_to_josys_format(date):
            from datetime import datetime
            try:
                for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"):
                    try:
                        parsed_date = datetime.strptime(date, fmt)
                        return parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                raise ValueError(f"Date format for '{date}' is not supported.")
            except Exception as e:
                return str(e)
            return f'{year}-{formatted_month}-{formatted_day}'

        if member.get("入社日") is not None and member.get("入社日") != "":
            member["入社日"] = format_date_to_josys_format(member["入社日"])
        if member.get("退職日") is not None and member["退職日"] != "":
            member["退職日"] = format_date_to_josys_format(member["退職日"])

    functions.append(convert_to_josys_status)
    return functions
