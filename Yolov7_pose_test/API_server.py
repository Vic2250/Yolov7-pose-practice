import requests
import threading
import json
import streamlit_authenticator as stauth
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing_extensions import Annotated
import datetime

from RTSP_server import RtspServer, load_all_device_info


# initial FastAPI settings
app = FastAPI()

# create RTSP and setting
device_info = load_all_device_info()
rtsp = RtspServer(device_info, '8554')
rtsp_thread = threading.Thread(target=rtsp.initial_create, args=(), daemon=True)
rtsp_thread.name = 'rtsp_thread'
rtsp_thread.start()


# 設置允許的來源 (origin) 列表，這裡允許所有來源
origins = ["*"]

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detect_id = {}
get = False


# API type
class SendDetectionID(BaseModel):   # Detection ID
    data: dict


class ModelName(BaseModel):       # Model
    data: str
    
    
class UpdateMemberList(BaseModel):   # WhiteList
    member: list
    

class UpdateMailTOList(BaseModel):  # MailTOList
    email: list
    remove: list


class UpdateMailCCList(BaseModel):  # MailCCList
    email: list
    remove: list
    
    
class UpdateAlarmSwitch(BaseModel): # AlarmSwitch
    switch: bool

    
class UpdateDetectionSwitch(BaseModel): # GroupDetectionSwitch
    data: list
    

class DataSendAlarm(BaseModel):     # Alarm-Device
    MID: str
    time: str
    Place: str
    Floor: str
    Area: str
    Monitor: str
    Human_ID: str
    Eligible: int


class EmailSend(BaseModel):         # Alarm-Email
    To: str
    CC: str
    Wrongdoer: str
    ImageToBase64String: str


class AccoundData(BaseModel):       # Account config data
    Data: dict
    

class AccountName(BaseModel):       # Account Name
    Username: str


# 用來將新的資料合併到舊的資料中
def merge_data(old_data, new_data):
    for key, value in new_data.items():
        if isinstance(value, dict):
            if key in old_data:
                merge_data(old_data[key], value)
            else:
                old_data[key] = value
        else:
            old_data[key] = value


# remove empty dicts (device_info)
def remove_empty_dicts(data):
    keys_to_remove = []
    for key, value in data.items():
        if isinstance(value, dict):
            remove_empty_dicts(value)
            if not value:
                keys_to_remove.append(key)
            elif len(value) == 1 and "全" in value and value["全"] == "":
                keys_to_remove.append(key)
    for key in keys_to_remove:
        del data[key]


# remove data (video_info)
def remove_subdict(main_dict, sub_dict):
    keys_to_remove = []
    for key, sub_value in sub_dict.items():
        if key in main_dict:
            if isinstance(sub_value, dict) and isinstance(main_dict[key], dict):
                if not sub_value:  # If sub_dict is empty, remove the whole key
                    keys_to_remove.append(key)
                else:
                    remove_subdict(main_dict[key], sub_value)
            elif main_dict[key] == sub_value:
                keys_to_remove.append(key)
    for key in keys_to_remove:
        del main_dict[key]


# sort the data (video_info) #2
def sort_nested_dict(d):
    if isinstance(d, dict):
        if "監視器" in d:
            if isinstance(d["監視器"], dict):
                # 分離除了'全'以外的項目
                all_item = ('全', d["監視器"].get('全', ''))
                sorted_items = []
                for monitor_name, monitor_items in d["監視器"].items():
                    if isinstance(monitor_items, dict):
                        sorted_items.append((monitor_name, monitor_items))
                # 按照 "Group" 大小和 "ID" 值進行排序
                sorted_items = sorted(sorted_items, key=lambda item: (
                item[1]["Group"], item[1]["ID"]))
                # 將'全'放在已排好的最前面
                sorted_dict = dict([all_item] + sorted_items)
                d["監視器"] = sorted_dict
            return d
        else:
            return {k: sort_nested_dict(v) for k, v in sorted(d.items()) if
                    isinstance(v, dict)}
    else:
        return d


# sort id in data (video_info) #1
def sort_id_dict(d):
    if isinstance(d, dict):
        if "監視器" in d:
            if isinstance(d["監視器"], dict):
                # 分離除了'全'以外的項目
                all_item = ('全', d["監視器"].get('全', ''))
                sorted_items = []
                for monitor_name, monitor_items in d["監視器"].items():
                    if isinstance(monitor_items, dict):
                        sorted_items.append((monitor_name, monitor_items))
                # 按照 "Group" 大小和 "ID" 值進行排序
                sorted_items = sorted(sorted_items, key=lambda item: (
                item[1]["Group"], item[1]["ID"]))
                # 將'全'放在已排好的最前面
                sorted_dict = dict([all_item] + sorted_items)
                d["監視器"] = sorted_dict
            return d
        else:
            return {key: sort_id_dict(value) for key, value in d.items()}
    else:
        return d


# the complete sort function
def order_dict(data):
    sorted_id = sort_id_dict(data)
    ordered_data = sort_nested_dict(sorted_id)
    return ordered_data


# all API in here
# 欲傳遞辨識背號結果
@app.post("/send_detect_id/")
def get_data(payload: SendDetectionID):
    global detect_id, get
    detect_id = payload.data
    get = True
    print(f'現在時間是: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    return {"success": True}

# UI 取得輪循播放設定
@app.get("/get_polling_result/")
def get_polling():
    with open('config.yml', 'r', encoding='utf-8') as f:
        polling_info = yaml.safe_load(f)
    if polling_info['polling']['enabled'] is True:
        return {'loading': polling_info['polling']['interval']}
    else:
        return {'loading': 0}

# UI取得辨識背號結果
@app.get("/get_detect_id/")
def send_data():
    return {"get_data": detect_id}


# get the video_info
@app.get("/get_video_data/")
def get_data():
    file_path = 'data.json'
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


# get white_list member
@app.get("/get_white_list/")
def get_data():
    with open('trust_list.json', 'r') as f:
        data = json.load(f)
    return data


# get all model name
@app.get("/get_all_model_name/")
def get_data():
    folder = Path('Model')
    file_names = [file.name for file in folder.iterdir() if file.is_file()]
    return {"all_model_name": file_names}


# get config model
@app.get("/get_model/")
def get_config_model():
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    model_name = config['model']['name']
    return {"now_model": model_name}


# use model
@app.post("/use_model/")
def use_model(payload: ModelName):
    file_name = payload.data
    # change the default model name
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    config['model']['name'] = file_name
    with open('config.yml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f)
    
    # to notify RTSP server should update the whole RTSP
    process_data()
    return {"message": f"成功掛載 {file_name} 模型"}


# delete model
@app.post("/delete_model/")
def delete_model(payload: ModelName):
    folder_path = Path('Model')
    file_name = payload.data
    # check the folder is true
    if not folder_path.is_dir():
        print(f"資料夾 {folder_path} 不存在。")
        return {"message": "刪除失敗(因為資料夾不存在)"}

    # the path of the file
    file_to_delete = folder_path / file_name
    # check the file path is true
    if file_to_delete.is_file():
        # delete the file
        file_to_delete.unlink()
        return {"message": f"檔案 {file_name} 已被刪除"}
    else:
        return {"message": f"找不到檔案 {file_name} 於資料夾 {folder_path}"}


# added new member
@app.post("/added_member/")
def added_white_list(payload: UpdateMemberList):
    with open('trust_list.json', 'r') as f:
        data = json.load(f)
    data['white_list'].extend(payload.member)
    with open('trust_list.json', 'w') as file:
        json.dump(data, file)
    return {"message": "update ok"}


# delete white_list
@app.post("/deleted_member/")
def deleted_white_list(payload: UpdateMemberList):
    with open('trust_list.json', 'r') as f:
        data = json.load(f)
    for item in payload.member:
        data['white_list'].remove(item)
    with open('trust_list.json', 'w') as file:
        json.dump(data, file)
    return {"message": "update ok"}


# get default alarm-switch
@app.get("/get_config_alarm_switch/")
def get_data():
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return {"data": config['alerting']['enabled']}


# Update alarm switch
@app.post("/update_alarm_switch/")
def update_alarm_switch(payload: UpdateAlarmSwitch):
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    config['alerting']['enabled'] = payload.switch
    with open('config.yml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f)
    return {"message": "update alarm switch ok"}


# update new group detection switch
@app.post("/update_video_detect/")
def update_video_detect(payload: UpdateDetectionSwitch):
    # load all data
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    # if the group match, change the detection_switch
    for factory, factory_data in data.items():
        for factory_name, factory_item in factory_data.items():
            for floor, floor_data in factory_item.items():
                for floor_name, floor_item in floor_data.items():
                    for site, site_data in floor_item.items():
                        for site_name, site_items in site_data.items():
                            for monitor, monitor_data in site_items.items():
                                for monitor_name, monitor_items in monitor_data.items():
                                    if monitor_name == "全":
                                        continue
                                    if monitor_items["Group"] == \
                                            payload.data[0]["群組"]:
                                        monitor_items["Detect"] = \
                                        payload.data[0]["偵測辨識"]
    # update the data.json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return {"message": "Update group detection ok"}

# Alarm-Device
@app.post("/alarm_api/")
def alarm_api(payload: DataSendAlarm):
    # res = random.choice([True, False])
    res = True
    # 現在可以安全地使用payload.data，因為資料已通過檢驗
    return {"message": f"{res}"}


# add monitor
@app.post("/add_monitor_info/")
def add_monitor_info(payload: dict):
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    merge_data(data, payload)
    ordered_data = order_dict(data)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(ordered_data, f, indent=4)
    process_data()
    return {"message": "Data add successfully"}


# modify the monitor_info (delete first and then add)
@app.post("/change_monitor_info/")
def change_monitor_info(payload: dict):
    row_data = payload.get('data')
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    remove_data = {}
    for factory, factory_data in data.items():
        for factory_name, factory_item in factory_data.items():
            for floor, floor_data in factory_item.items():
                for floor_name, floor_item in floor_data.items():
                    for site, site_data in floor_item.items():
                        for site_name, site_items in site_data.items():
                            for monitor, monitor_data in site_items.items():
                                for monitor_name, monitor_items in monitor_data.items():
                                    if monitor_name == "全":
                                        continue
                                    if monitor_items["ID"] == row_data["ID"]:
                                        remove_data = {"廠區": {factory_name: {
                                            "樓層": {floor_name: {
                                                "站點": {site_name: {
                                                    "監視器": {monitor_name: {
                                                        "ID": monitor_items[
                                                            "ID"],
                                                        "URL": monitor_items[
                                                            "URL"],
                                                        "Group": monitor_items[
                                                            "Group"],
                                                        "Detect": monitor_items[
                                                            "Detect"],
                                                        "Start_X":
                                                            monitor_items[
                                                                "Start_X"],
                                                        "Start_Y":
                                                            monitor_items[
                                                                "Start_Y"],
                                                        "Width": monitor_items[
                                                            "Width"],
                                                        "Height": monitor_items[
                                                            "Height"],
                                                        "RTSP": f'[IP位置]:8554/{monitor_name}'}}}}}}}}}
    remove_subdict(data, remove_data)
    remove_empty_dicts(data)
    edit_dict = {"廠區": {row_data["廠區"]: {"樓層": {row_data["樓層"]: {
        "站點": {row_data["站點"]: {"監視器": {
            "全": "",
            row_data["監視器"]: {"ID": row_data["ID"],
                                 "URL": row_data["Rtsp串流位置"],
                                 "Group": row_data["群組"], "Detect": True,
                                 "Start_X": 0, "Start_Y": 0, "Width": 1920,
                                 "Height": 1080,
                                 "RTSP": f'rtsp://[IP位置]:8554/{row_data["監視器"]}'}}}}}}}}}
    merge_data(data, edit_dict)
    ordered_data = order_dict(data)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(ordered_data, f, indent=4)
    process_data()
    return {"message": "Data change successfully"}  # 回傳成功訊息


# delete monitor
@app.post("/delete_monitor_info/")
def delete_monitor_info(payload: dict):
    row_data = payload.get('data')
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    remove_data = {}
    for factory, factory_data in data.items():
        for factory_name, factory_item in factory_data.items():
            for floor, floor_data in factory_item.items():
                for floor_name, floor_item in floor_data.items():
                    for site, site_data in floor_item.items():
                        for site_name, site_items in site_data.items():
                            for monitor, monitor_data in site_items.items():
                                for monitor_name, monitor_items in monitor_data.items():
                                    if monitor_name == "全":
                                        continue
                                    if monitor_items["ID"] == row_data["ID"]:
                                        remove_data = {"廠區": {factory_name: {
                                            "樓層": {floor_name: {
                                                "站點": {site_name: {
                                                    "監視器": {monitor_name: {
                                                        "ID": monitor_items[
                                                            "ID"],
                                                        "URL": monitor_items[
                                                            "URL"],
                                                        "Group": monitor_items[
                                                            "Group"],
                                                        "Detect": monitor_items[
                                                            "Detect"],
                                                        "Start_X":
                                                            monitor_items[
                                                                "Start_X"],
                                                        "Start_Y":
                                                            monitor_items[
                                                                "Start_Y"],
                                                        "Width": monitor_items[
                                                            "Width"],
                                                        "Height": monitor_items[
                                                            "Height"],
                                                        "RTSP": f'rtsp://[IP位置]:8554/{monitor_name}'}}}}}}}}}
    remove_subdict(data, remove_data)
    remove_empty_dicts(data)
    ordered_data = order_dict(data)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(ordered_data, f, indent=4)
    process_data()
    return {"message": "Data deleted successfully"}


# build account
@app.post("/add_account/")
def add_account(payload: AccoundData):
    with open('account.yml', 'w') as file:
        yaml.dump(payload.Data, file, default_flow_style=False)
    return {"Message": "add account OK"}
        

# set new password
@app.post("/set_pwd/")
def set_password(payload: AccoundData):
    with open('account.yml', 'w') as file:
        yaml.dump(payload.Data, file, default_flow_style=False)
    return {"Message": "set new pwd OK"}

    
# rebuild all rtsp
@app.get("/rebuild_rtsp/")
def process_data():
    global rtsp
    rtsp.rebuild_rtsp()
    return True


# update white_list
@app.get("/update/white_list/")
def update_white_list():
    global rtsp
    rtsp.update_eligible_member()
    return True


# update alarm
@app.get("/update/alarm_switch/")
def update_alarm_switch():
    global rtsp
    rtsp.update_alarm_awitch()
    return True


# reset the account's password (initial is '{account}@init')
@app.post("/reset_account/")
def reset_account(payload: AccountName):
    with open('account.yml', 'r') as file:
        data = yaml.safe_load(file)
    credentials = data.get('credentials', {})
    usernames = credentials.get('usernames', {})
    for username, info in usernames.items():
        if username == payload.Username:
            new_password = f'{payload.Username}@init'
            if payload.Username == 'admin':
                new_password = 'admin'
            new_password = stauth.Hasher([new_password]).generate()
            new_password = new_password[0]
            info['password'] = new_password
    with open('account.yml', 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    return {"message": f"帳號:{payload.Username} 已恢復預設密碼"}


# delete account
@app.post("/delete_account/")
def delete_account(payload: AccountName):
    with open('account.yml', 'r') as file:
        data = yaml.safe_load(file)
    # 刪除帳號的資訊
    if 'admin' in data.get('credentials', {}).get('usernames', {}):
        del data['credentials']['usernames'][payload.Username]
    with open('account.yml', 'w') as file:
        yaml.dump(data, file, default_flow_style=False)
    print(payload)
    return {"message": f"帳號:{payload.Username} 已被刪除"}


# get config timeout & round robin
@app.get("/get_other_info/")
def get_other_setting_info():
    timeout_switch = True
    with open('account.yml', 'r', encoding='utf-8') as f:
        login_info = yaml.safe_load(f)
    if login_info['cookie']['expiry_days'] == 0:
        timeout_switch = False
    with open('config.yml', 'r', encoding='utf-8') as f:
        other_info = yaml.safe_load(f)
    info = {'timeout_switch': timeout_switch, 'timeout': other_info['timeout'], 
            'polling': other_info['polling']['enabled'], 'interval': other_info['polling']['interval']}
    return info