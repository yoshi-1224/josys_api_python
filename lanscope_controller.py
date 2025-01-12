from lanscope_api_client import LanscopeApiClient

def get_lanscope_devices(config):
    api_token = config["devices"]["source_credentials"]["api_token"]
    print(api_token)
    if not api_token:
        raise ValueError(f"LanscopeのAPIトークンが見つかりません")
    results = LanscopeApiClient(api_token).get_devices()
    if not results:
        return
    
    column_names, output_column_names = _get_lanscope_columns(config)
    results = [
        {output_column_names[column_names.index(key)]: value for key, value in member.items() if key in column_names}
        for member in results
    ]
    return results
    
def _get_lanscope_columns(config):
    keys = list(config["devices"]['source_columns'].keys())
    values = [config["devices"]['source_columns'][key] for key in keys]
    return keys, values