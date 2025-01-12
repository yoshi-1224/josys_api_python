def compute_member_diffs(josys_members, source_members, josys_columns, source_columns, match_key_index):

    def validate_new_members(members_to_add):
        valid_members = []
        for member in members_to_add:
            if check_mandatory_columns_exist_for_new_member(member) and check_valid_values_for_dropdown_columns(member):
                valid_members.append(member)
        return valid_members

    def validate_updated_members(members_to_update):
        valid_members = []
        for member in members_to_update:
            if check_valid_values_for_dropdown_columns(member):
                valid_members.append(member)
        return valid_members

    def check_mandatory_columns_exist_for_new_member(member):
        return ("姓" in member and member["姓"] != "" and
                "ステータス" in member and member["ステータス"] != "" and
                (("メールアドレス" in member and member["メールアドレス"] != "") or
                 ("従業員番号" in member and member["従業員番号"] != "")))

    def check_valid_values_for_dropdown_columns(member):
        valid_statuses = ["在籍中", "退職済", "休職中", "その他", "入社前"]
        valid_member_types = ["", "役員", "正社員", "派遣社員", "業務委託", "パート・アルバイト", "契約社員", "出向社員", "外部", "システム", "その他"]
        if "ステータス" in member and member["ステータス"] not in valid_statuses:
            print(f"不正な値：{member['ステータス']}は有効なステータス値ではありません")
            return False

        if member.get("ステータス") == "退職済":
            if "退職日" not in member or member["退職日"] == "":
                print(f"不正な値：「ステータス：退職済」ですが、退職日が空です")
                return False

        if member.get("ステータス") != "退職済":
            if "退職日" in member and (member["退職日"] is not None and member["退職日"] != ""):
                print(f"不正な値：「ステータス：退職済」ではないですが、退職日が空ではないです")
                return False

        if "メンバー種別" in member and member["メンバー種別"] not in valid_member_types:
            print(f"不正な値：{member['メンバー種別']}は有効なメンバー種別の値ではありません")
            return False

        return True

    def drop_empty_columns(members):
        return [{k: v for k, v in member.items() if (v is not None and v != "")} for member in members]

    def compare_and_categorize(source_members, josys_members, josys_col2source_col, hrms_match_key, josys_match_key):
        entries_to_add = []
        entries_to_update = []

        josys_members_by_match_key_value = {obj[josys_match_key]: obj for obj in josys_members if obj.get(josys_match_key)}

        source_col2josys_col = {v: k for k, v in josys_col2source_col.items()}

        for src_obj in source_members:
            josys_obj = josys_members_by_match_key_value.get(src_obj.get(hrms_match_key))
            if not josys_obj:
                new_member = {josys_col: src_obj.get(source_col2josys_col[josys_col], None) for josys_col in josys_col2source_col}
                entries_to_add.append(new_member)
            else:
                diff_obj = {"ID": josys_obj["ID"]}
                is_different = False
                for josys_col in josys_col2source_col:
                    josys_value = josys_obj.get(josys_col)
                    source_value = src_obj.get(source_col2josys_col[josys_col])
                    if source_value != josys_value:
                        is_different = True
                        diff_obj[josys_col] = source_value
                if is_different:
                    entries_to_update.append(diff_obj)

        return entries_to_add, entries_to_update

    def rename_keys(objects, key_mapping):
        for obj in objects:
            for key in list(obj.keys()):
                if key in key_mapping:
                    obj[key_mapping[key]] = obj.pop(key)

    josys_match_key = josys_columns[match_key_index]
    source_match_key = source_columns[match_key_index]
    josys_col2source_col = {josys_columns[i]: source_columns[i] for i in range(len(josys_columns))}

    members_to_add, members_to_update = compare_and_categorize(source_members, josys_members, josys_col2source_col, source_match_key, josys_match_key)
    print(f"{len(members_to_add)}名の新規メンバーが検出されました")
    print(f"{len(members_to_update)}名の更新メンバーが検出されました")

    members_to_add = validate_new_members(members_to_add)
    members_to_add = drop_empty_columns(members_to_add)
    members_to_update = validate_updated_members(members_to_update)
    print(f"{len(members_to_add)}名の新規メンバーが追加対象です")
    print(f"{len(members_to_update)}名の更新メンバーが更新対象です")

    jp2en_mapping = {
        "ID": "uuid",
        "姓": "last_name",
        "名": "first_name",
        "従業員番号": "user_id",
        "入社日": "start_date",
        "退職日": "end_date",
        "ステータス": "status",
        "役職": "job_title",
        "メールアドレス": "email",
        "個人メールアドレス": "personal_email",
        "メンバー種別": "user_category",
        "ユーザー名": "username",
        "メモ": "additional_information",
        "部署": "department_uuids"
    }
    rename_keys(members_to_add, jp2en_mapping)
    rename_keys(members_to_update, jp2en_mapping)

    return members_to_add, members_to_update
