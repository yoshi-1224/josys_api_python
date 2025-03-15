import sys
import yaml
import josys_controller

from constants import *

def main():
    actions = [
        COMMAND_GET_JOSYS_MEMBERS,
        COMMAND_GET_SOURCE_MEMBERS,
        COMMAND_SYNC_MEMBERS_FROM_FILE,
        COMMAND_SYNC_MEMBERS_FROM_API,
        COMMAND_COMPARE_MEMBERS,
        COMMAND_GET_JOSYS_DEVICES,
        COMMAND_GET_SOURCE_DEVICES,
        COMMAND_COMPARE_DEVICES,
        COMMAND_SYNC_DEVICES
    ]
    if len(sys.argv) < 2:
        print(f"Error: 実行したいアクション名を入力してください。次のいずれかが可能です: [{', '.join(actions)}]")
        return
    else:
        user_input = sys.argv[1]
        if user_input not in actions:
            print(f"Error: '{user_input}'は正しいアクション名ではありません。次のうち、いずれかを入力してください: [{', '.join(actions)}]")
            return
    with open(CONFIG_FILENAME, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file) 

    if user_input == COMMAND_GET_JOSYS_DEVICES:
        josys_controller.setup_api_client(config)
        fetch_josys_devices(config)
        return
    elif user_input == COMMAND_GET_SOURCE_DEVICES:
        fetch_source_devices(config)
        return
    elif user_input == COMMAND_COMPARE_DEVICES:
        pass
    elif user_input == COMMAND_SYNC_DEVICES:
        pass
    elif user_input == COMMAND_GET_JOSYS_MEMBERS:
        josys_controller.setup_api_client(config)
        fetch_josys_members(config)
        fetch_josys_departments()
        return
    elif user_input == COMMAND_GET_SOURCE_MEMBERS:
        fetch_source_members(config)
        return
    elif user_input == COMMAND_COMPARE_MEMBERS:
        josys_members = load_csv_as_objects(JOSYS_MEMBERS_FILENAME)
        source_members = load_csv_as_objects(SOURCE_MEMBERS_FILENAME)
        new_members, updated_members = compute_member_diffs(josys_members, source_members, config)
        save_objects_to_csv(new_members, NEW_MEMBERS_FILENAME)
        save_objects_to_csv(updated_members, UPDATED_MEMBERS_FILENAME)
        return
    elif user_input == COMMAND_SYNC_MEMBERS_FROM_FILE or user_input == COMMAND_SYNC_MEMBERS_FROM_API:
        josys_controller.setup_api_client(config)
        if user_input == COMMAND_SYNC_MEMBERS_FROM_API:
            fetch_josys_members(config)
            fetch_josys_departments()
            fetch_source_members(config)
        josys_members = load_csv_as_objects(JOSYS_MEMBERS_FILENAME)
        source_members = load_csv_as_objects(SOURCE_MEMBERS_FILENAME)
        new_members, updated_members = compute_member_diffs(josys_members, source_members, config)
        save_objects_to_csv(new_members, NEW_MEMBERS_FILENAME)
        save_objects_to_csv(updated_members, UPDATED_MEMBERS_FILENAME)
        new_members = load_csv_as_objects(NEW_MEMBERS_FILENAME)
        updated_members = load_csv_as_objects(UPDATED_MEMBERS_FILENAME)
        if "部署" in config["members"]["column_mappings"]:
            print(f"部署情報を{JOSYS_DEPARTMENTS_FILENAME}から読み込んでいます")
            department_lookup = load_departments(JOSYS_DEPARTMENTS_FILENAME)
            change_department_names_to_uuids(new_members, department_lookup)
            change_department_names_to_uuids(updated_members, department_lookup)
        upload_new_members(new_members)
        update_members(updated_members)
        return
    
def load_departments(filename):
    department_lookup = {}
    with open(filename, mode='r', encoding='utf-8') as file:
        import csv
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                department_lookup[row[0]] = row[1]
    return department_lookup

def change_department_names_to_uuids(members, department_lookup):
    if not department_lookup:
        return
    for m in members:
        uuid = department_lookup.get(m['department'], None)
        m['department_uuids'] = [uuid]
        del m['department']
    return

def fetch_josys_devices(config):
    josys_devices = josys_controller.get_josys_devices(config)
    save_objects_to_csv(josys_devices, JOSYS_DEVICES_FILENAME)
    return josys_devices

def fetch_josys_members(config):
    print(f"ジョーシスからメンバーを取得します")
    josys_members = josys_controller.get_josys_members(config)
    save_objects_to_csv(josys_members, JOSYS_MEMBERS_FILENAME)
    return josys_members

def fetch_josys_departments():
    print(f"ジョーシスから部署一覧を取得します")
    josys_departments = josys_controller.get_josys_departments()
    save_dic_as_csv(josys_departments, JOSYS_DEPARTMENTS_FILENAME)

def fetch_source_devices(config):
    supported_sources = ["lanscope"]
    source = config['devices']['source']
    source_devices = []
    if source not in supported_sources:
        print(f"Error: '{source}'はデバイスソースとして対応していません")
        return
    else:
        print(f"{source}からデバイスを取得します")
    if source == "lanscope":
        import lanscope_controller
        lanscope_controller.get_lanscope_devices(config)

    save_objects_to_csv(source_devices, SOURCE_DEVICES_FILENAME)
    return source_devices

def fetch_source_members(config):
    supported_sources = ["hennge"]
    source = config['members']['source']
    if source not in supported_sources:
        print(f"Error: '{source}'はメンバーソースとして対応していません")
        return
    else:
        print(f"{source}からメンバーを取得します")
    if source == "hennge":
        import hennge_controller
        source_members = hennge_controller.get_hennge_members(config)

    save_objects_to_csv(source_members, SOURCE_MEMBERS_FILENAME)
    return source_members

def upload_new_members(new_members):
    if len(new_members) == 0:
        return
    print(f"{len(new_members)}名のメンバーを作成中...")
    results = josys_controller.upload_members(new_members)
    for i in range(len(new_members)):
        new_members[i]["api_result"] = results[i]
    save_objects_to_csv(new_members, NEW_MEMBERS_API_RESULT_FILENAME)
    print(f"結果は{NEW_MEMBERS_API_RESULT_FILENAME}で確認可能です")

def update_members(members):
    if len(members) == 0:
        return
    print(f"{len(members)}名のメンバーを更新中...")
    results = josys_controller.update_members(members)
    for i in range(len(members)):
        members[i]["api_result"] = results[i]
    save_objects_to_csv(members, UPDATED_MEMBERS_API_RESULT_FILENAME)
    print(f"結果は{UPDATED_MEMBERS_API_RESULT_FILENAME}で確認可能です")

def upload_new_devices(new_devices):
    pass

def update_devices(devices):
    pass

def compute_member_diffs(josys_members, source_members, config):
    josys_columns, source_columns, match_key_index = get_member_mapping_config(config)
    import compute_member_diffs
    new_members, updated_members = compute_member_diffs.compute_member_diffs(josys_members, source_members, josys_columns, source_columns, match_key_index)

    return new_members, updated_members

def load_csv_as_objects(filename):
    import csv
    objects = []
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                objects.append(row)
    except FileNotFoundError:
        return []
    return objects

def save_objects_to_csv(objects, filename):
    import csv
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        if not objects:
            csvfile.write('')
            print(f"->{filename}に結果を保存しました")
            return
        all_fieldnames = set()
        for obj in objects:
            all_fieldnames.update(obj.keys())
        writer = csv.DictWriter(csvfile, fieldnames=sorted(all_fieldnames))
        writer.writeheader()
        for obj in objects:
            row = {field: obj.get(field, '') for field in all_fieldnames}
            writer.writerow(row)
    print(f"->{filename}に結果を保存しました")

def save_dic_as_csv(input, filename):
    import csv
    if not input:
        return
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["department_names", "department_uuids"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for key, value in input.items():
            writer.writerow({"department_names": value, "department_uuids": key})

    print(f"->{filename}に部署一覧を保存しました")

def get_member_mapping_config(config):
    match_key = config["members"]["match_key"]
    column_mappings = config["members"]["column_mappings"]
    josys_columns = list(column_mappings.keys())
    source_columns = list(column_mappings.values())
    print("===ジョーシスの項目===")
    print(josys_columns)
    print("===ソースの項目===")
    print(source_columns)
    print(f"===マッチキー===\n{match_key}")
    match_key_index = josys_columns.index(match_key) if match_key in josys_columns else -1
    return josys_columns, source_columns, match_key_index


if __name__ == "__main__":
    main()
