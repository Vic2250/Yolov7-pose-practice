import argparse
import base64
import copy
import logging
import time
import threading
import uuid
import cv2
import gi
import json
import requests
import yaml
from datetime import datetime

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')

from gi.repository import Gst, GstRtspServer, GObject
from detection_fun import load_model, detection_image, restore_image


# log setting
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    handlers=[logging.FileHandler('info.log', 'w', 'utf-8'), ])


# RTSP item
class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, device_info):
        super(SensorFactory, self).__init__()
        self.device_link = device_info['device_link']
        self.cap = cv2.VideoCapture(self.device_link)
        self.number_frames = 0
        self.fps = device_info['fps']
        self.image_width = device_info['image_width']
        self.image_height = device_info['image_height']
        self.duration = 1 / self.fps * Gst.SECOND
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96' \
            .format(self.image_width, self.image_height, self.fps)
        self.factory = device_info['device_place']
        self.floor = device_info['device_floor']
        self.site = device_info['device_area']
        self.name = device_info['device_name']
        self.group = device_info['device_group']
        self.model = device_info['model']
        self.switch = device_info['Switch']
        self.start_x = device_info['Start_X']
        self.start_y = device_info['Start_Y']
        self.crop_height = device_info['Height']
        self.crop_width = device_info['Width']
        self.analyze_image = []
        self.status = False
        self.Frame = []
        self.analyze = None
        self.last_x = 0
        self.last_y = 0
        self.last_confidence = 0
        self.last_text = ''
        self.alarm = False
        self.time_count = None                  # 紀錄過了多久(更新剪裁的圖片用)
        self.save_frame = False
        self.stop_factory = False
        self.start()

    # start process the factory's rtsp
    def start(self):
        start_time = datetime.now()
        self.time_count = start_time
        self.save_frame = True
        self.analyze = threading.Thread(target=self.analyzeframe, args=(),
                                        daemon=True)
        self.analyze.name = f'{self.name}-analyze'
        self.analyze.start()

    # the function to process factory's rtsp (thread's function)
    def analyzeframe(self):
        start = time.time()
        while not self.stop_factory:
            try:
                if not self.cap.isOpened():
                    self.analyze_image = []
                    raise Exception("Failed to connect to RTSP stream. Please check the RTSP URL.")
                current_date = datetime.now()
                days_difference = (current_date - self.time_count).days
                temp_status, temp_Frame = self.cap.read()
                start_time = time.time()
                if temp_Frame is not None:
                    self.status, self.analyze_image = temp_status, temp_Frame
                    # save pictures every 30 days
                    if days_difference >= 30:
                        self.time_count = copy.deepcopy(current_date)
                        self.save_frame = True
                    if self.save_frame is True:
                        picture_path = f'Image/{self.name}.jpg'
                        # frame = cv2.cvtColor(temp_Frame, cv2.COLOR_RGB2BGR)
                        cv2.imwrite(picture_path, temp_Frame)
                        self.save_frame = False
                    end_time = time.time()
                    time.sleep(max(0, 0.0625-(end_time-start_time)))
                    # time.sleep(0.048)
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            except Exception as e:
                print("Error: ", str(e))  # 顯示其他異常
                break
            if self.stop_factory:
                break

    # get the latest frame to detection
    def detectframe(self):
        frame = self.analyze_image
        self.alarm = False
        if len(frame) != 0:
            if self.switch is True:
                # crop the image to detected
                x1, y1 = self.start_x, self.start_y
                x2, y2 = self.start_x + self.crop_width, self.start_y + self.crop_height
                detect_image = frame[y1:y2, x1:x2]
                result = detection_image(detect_image, self.last_x, self.last_y, self.last_confidence, self.last_text, self.model)
                detect_image = result[0]
                number = result[1]
                self.last_x = result[2]
                self.last_y = result[3]
                self.last_confidence = result[4]
                filling = result[5]
                # restore the original picture
                detect_image = restore_image(detect_image, filling,
                                             self.crop_height, self.crop_width)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                frame[y1:y2, x1:x2] = detect_image
                # if different from previous result -> alarm
                if self.last_text != number:
                    self.alarm = True
                self.last_text = number
            else:
                self.last_text = ''
                self.last_x = 0
                self.last_y = 0
                self.last_confidence = 0
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            # print(f'height:{frame.shape[0]}, width:{frame.shape[1]}')
        else:
            number = '-1'
        self.Frame = copy.deepcopy(frame)

    # "on_need_data"方法處理影片串流的實際處理，並將frame編碼成RTSP串流所需的格式，然後推送到RTSP伺服器
    def on_need_data(self, src, length):
        if self.Frame != []:
            frame = cv2.resize(self.Frame,
                               (self.image_width, self.image_height),
                               interpolation=cv2.INTER_LINEAR)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            data = frame.tostring()
            buf = Gst.Buffer.new_allocate(None, len(data), None)
            buf.fill(0, data)
            buf.duration = self.duration
            timestamp = self.number_frames * self.duration
            buf.pts = buf.dts = int(timestamp)
            buf.offset = timestamp
            self.number_frames += 1
            retval = src.emit('push-buffer', buf)
            if retval != Gst.FlowReturn.OK:
                print(retval)

    # 建立Gstreamer的element，並且使用先前建立的launch_string
    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    # 將on_need_data方法連接到影片串流的appsrc元件上，以便實現影片串流
    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)


# RTSP的server(藉由多個RTSP物件輸出多個連結)
class RtspServer:
    def __init__(self, device_info_list, rtsp_port):
        Gst.init(None)
        self.server = GstRtspServer.RTSPServer()
        self.factory = []
        self.device_info_list = device_info_list
        self.rtsp_port = rtsp_port
        self.api_alarm = load_config_api_alarm()
        self.white_list = eligible_member()
        self.last_group = {}
        self.unknow_count = {}
        self.detect_result_url = "http://[IP位置]:8000/send_detect_id/"
        self.alarm_url = "http://[IP位置]:8000/alarm_api/"
        self.stop_rtsp = False
        self.loop = None

    # create the RTSP instance and start detection
    def initial_create(self):
        count = 0
        for device_info in self.device_info_list:
            self.factory.append(SensorFactory(device_info))
            self.factory[count].set_shared(True)
            rtsp_uri = device_info['uri']
            self.server.get_mount_points().add_factory(rtsp_uri,
                                                       self.factory[count])
            count += 1

        # Detection thread (Execute each one before proceeding to the next picture.)
        detect_thread = threading.Thread(target=self.detect_output, args=(),
                                         daemon=True)
        detect_thread.name = 'detection'
        detect_thread.start()

        # setting RTSP server's port and start service
        self.server.set_service(str(self.rtsp_port))
        self.server.attach(None)

        # getting the event loop and wait for connection
        self.loop = GObject.MainLoop()
        self.loop.run()

    # thread-function -> 按照camera數量輪流進行辨識以及傳遞辨識背號
    def detect_output(self):
        time.sleep(1)
        while not self.stop_rtsp:
            group_id = {}
            start_time = time.time()
            for factory in self.factory:
                factory.detectframe()
                if factory.group in group_id:
                    group_id[factory.group].append(
                        [factory.name, factory.last_confidence,
                         factory.last_text])
                else:
                    group_id[factory.group] = [
                        [factory.name, factory.last_confidence,
                         factory.last_text]]
            end_time = time.time()
            print(f'process one frame for all cost {end_time-start_time}')
            # 計算每個Group，取信心值大者，若皆為0，則判斷辨識結果是空字串還是Unknown(空字串代表沒人)
            for key, values in group_id.items():
                if len(values) >= 2:
                    max_index = 0
                    for i in range(1, len(values)):
                        if values[i][1] > values[max_index][1]:
                            max_index = i
                        elif values[i][1] == values[max_index][1]:
                            if values[max_index][2] == "":
                                if values[i][2] != "":
                                    max_index = i
                    values[:] = [values[max_index]]
            for factory in self.factory:
                factory.last_confidence = group_id.get(factory.group)[0][1]
                factory.last_text = group_id.get(factory.group)[0][2]

            # 將辨識背號結果以Group分類後，post給fastapi，以便後續操作
            payload = {"data": group_id}
            requests.post(self.detect_result_url, json=payload)
            alarm_complete = threading.Thread(target=self.alarm, args=(group_id,),daemon=True)
            alarm_complete.name = 'alarm_complete_thread'
            alarm_complete.start()

    def alarm(self, group_id):
        send_list = []
        if self.last_group != {}:
            for key in self.last_group.keys():                              # 新舊字典比較unknown次數
                value1 = self.last_group[key]
                value2 = group_id[key]

                if value1 == value2 and 'Unknown' in value1[0]:
                    self.unknow_count[key] += 1
                else:
                    self.unknow_count[key] = 0
            
            diff_items = {key: group_id[key] for key in self.last_group.keys() & group_id.keys()    # 比較新舊字典辨識文字不同處
                          if self.last_group[key][0][2] != group_id[key][0][2]}      
            result = {}

            for key in self.last_group.keys() & group_id.keys():                                    # 取出Unknown -> 要跟相異的一併發出alarm
                if all(item[2] == 'Unknown' for item in self.last_group[key]) and all(item[2] == 'Unknown' for item in group_id[key]):
                    result[key] = [[item[0], item[1], 'Unknown'] for item in self.last_group[key]]
            # 合併+排序
            result.update(diff_items)
            sorted_dict = {k: result[k] for k in sorted(result)}
            unknow = []
            self.last_group = group_id
            for factory in self.factory:
                if factory.group in sorted_dict:
                    if factory.name == sorted_dict[factory.group][0][0]:
                        send_list.append(
                            [factory.factory, factory.floor, factory.site,
                             factory.name, sorted_dict[factory.group][0][2],
                             factory.Frame])
                        unknow.append(self.unknow_count[factory.group])
            for i in range(len(send_list)):
                if send_list[i][4] != '':                   # 有人才觸發告警
                    if self.api_alarm is True:
                        self.send_alarm(send_list[i])
        else:
            self.last_group = group_id          
            for key, value in group_id.items():             # 紀錄unknown出現次數
                count = 0
                for item in value:
                    if 'Unknown' in item:
                        count += 1
                self.unknow_count[key] = count
            self.unknow_count = {k: self.unknow_count[k] for k in sorted(self.unknow_count)}
            
            for factory in self.factory:                    # 所有需傳遞的資訊(第一次->全部)
                if factory.group in group_id:
                    if factory.name == group_id[factory.group][0][0]:
                        send_list.append(
                            [factory.factory, factory.floor, factory.site,
                             factory.name, group_id[factory.group][0][2],
                             factory.Frame])    
                        
            for i in range(len(send_list)):
                if send_list[i][4] != '':                   # 有人才觸發告警
                    if self.api_alarm is True:
                        self.send_alarm(send_list[i])

    def send_alarm(self, send_info):                                                                # 設備連動，待規劃
        MID = str(uuid.uuid4())
        time_now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        Place = send_info[0]
        Floor = send_info[1]
        Area = send_info[2]
        Monitor = send_info[3]
        Human_ID = send_info[4]
        if Human_ID == 'Unknown':
            qualify = 0
        else:
            result = check_member_list(Human_ID, self.white_list)
            if result == 'Green':
                qualify = 1
            else:
                qualify = -1
        Eligible = qualify
        payload = {"MID": MID, "time": time_now, "Place": Place,
                   "Floor": Floor,
                   "Area": Area, "Monitor": Monitor, "Human_ID": Human_ID,
                   "Eligible": Eligible}  # 正確使用 "data" 作為參數名稱
        device_alarm_thread = threading.Thread(target=alarm_api_fun, args=(
            self.alarm_url, payload, time_now, Monitor))
        device_alarm_thread.start()


    # 重構rtsp(換模型、新增刪除影像來源等)
    def rebuild_rtsp(self):
        # stop the original rtsp
        self.stop_rtsp = True
        self.loop.quit()
        # stop detection thread
        all_threads = threading.enumerate()
        target_thread_name = "detection"
        for thread in all_threads:
            if thread.name == target_thread_name:
                thread.join()
        # stop analyze thread
        analyze_stop = []
        for i in range(len(self.factory)):
            self.factory[i].stop_factory = True
            analyze_stop.append(f'{self.factory[i].name}-analyze')
        for thread in all_threads:
            if thread.name in analyze_stop:
                thread.join()
        # stop rtsp server thread
        for thread in all_threads:
            if thread.name == 'rtsp_thread':
                thread.join()

        # rebuild rtsp
        self.stop_rtsp = False
        self.device_info_list = load_all_device_info()
        self.factory = []
        count = 0
        for device_info in self.device_info_list:
            self.factory.append(SensorFactory(device_info))
            self.factory[count].set_shared(True)
            rtsp_uri = device_info['uri']
            self.server.get_mount_points().add_factory(rtsp_uri,
                                                       self.factory[count])
            count += 1
        # rebuild detection_thread
        detect_thread = threading.Thread(target=self.detect_output, args=(),
                                         daemon=True)
        detect_thread.name = 'detection'
        detect_thread.start()
        # restart rtsp_server
        rtsp_thread = threading.Thread(target=self.rerun_loop, args=(),
                                       daemon=True)
        rtsp_thread.name = 'rtsp_thread'
        rtsp_thread.start()

    # update eligible member
    def update_eligible_member(self):
        # stop detection thread
        self.stop_rtsp = True
        all_threads = threading.enumerate()
        target_thread_name = "detection"
        for thread in all_threads:
            if thread.name == target_thread_name:
                thread.join()
        # stop alarm thread
        target_thread_name = 'alarm_complete_thread'
        for thread in all_threads:
            if thread.name == target_thread_name:
                thread.join()
        # get the new eligible member
        self.white_list = eligible_member()
        # rebuild detection thread
        self.stop_rtsp = False
        detect_thread = threading.Thread(target=self.detect_output, args=(),
                                         daemon=True)
        detect_thread.name = 'detection'
        detect_thread.start()
        
    # update alarm switch
    def update_alarm_awitch(self):
        # stop detection thread
        self.stop_rtsp = True
        all_threads = threading.enumerate()
        target_thread_name = "detection"
        for thread in all_threads:
            if thread.name == target_thread_name:
                thread.join()
        # stop alarm thread
        target_thread_name = 'alarm_complete_thread'
        for thread in all_threads:
            if thread.name == target_thread_name:
                thread.join()
        # get the new eligible member
        self.api_alarm = load_config_api_alarm()
        # rebuild detection thread
        self.stop_rtsp = False
        detect_thread = threading.Thread(target=self.detect_output, args=(),
                                         daemon=True)
        detect_thread.name = 'detection'
        detect_thread.start()

    def rerun_loop(self):
        print('start_loop')
        self.loop.run()


# load model name in config.yml
def load_config_api_alarm():
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['alerting']['enabled']


# 讀取符合名單有哪些
def eligible_member():
    with open('trust_list.json', 'r') as f:
        data = json.load(f)
    return data['white_list']


# 檢查是否符合名單
def check_member_list(member_index, member_list):
    for item in member_list:
        if item in member_index:
            return 'Green'
    return 'Red'


# Alarm_api的thread的function
def alarm_api_fun(alarm_url, send_json, time_now, monitor):
    for i in range(2):
        try:
            response = requests.post(alarm_url, json=send_json)
            if response.json()["message"] == "True":
                # print(response.text)
                break
            else:
                print(
                    f"Retry {time_now} {monitor} {i + 1} - Alarm API Got False, retrying...")
                pass
        except requests.exceptions.RequestException as e:
            logging.info(f'Connect Alarm API for {monitor} message failed')


def load_all_device_info():
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    rows = []
    model = load_model()
    for place, place_data in data.items():
        for place_name, place_item in place_data.items():
            for floor, floor_data in place_item.items():
                for floor_name, floor_item in floor_data.items():
                    for area, area_data in floor_item.items():
                        for area_name, area_items in area_data.items():
                            for monitor, monitor_data in area_items.items():
                                for monitor_name, monitor_items in monitor_data.items():
                                    if monitor_name != "全":
                                        rows.append({
                                            "device_place": place_name,
                                            "device_floor": floor_name,
                                            "device_area": area_name,
                                            "device_name": monitor_name,
                                            "device_group": monitor_items[
                                                "Group"],
                                            "device_link": monitor_items["URL"],
                                            "fps": 16,
                                            "image_width": 1920,
                                            "image_height": 1080,
                                            "uri": f"/{monitor_name}",
                                            "model": model,
                                            "Switch": monitor_items["Detect"],
                                            "Start_X": monitor_items["Start_X"],
                                            "Start_Y": monitor_items["Start_Y"],
                                            "Width": monitor_items["Width"],
                                            "Height": monitor_items["Height"]
                                        })
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--rtsp_port", default=8554,
                        help="port for RTSP server", type=int)
    args = parser.parse_args()
    model = load_model()
    # 使用者輸入多個影片資訊，每個影片有自己的device_id, fps, 影像寬度、高度和rtsp URI (最後會變成讀檔產生這個list)
    device_info_list = load_all_device_info()
    rtsp = RtspServer(device_info_list, args.rtsp_port)
    rtsp.initial_create()
