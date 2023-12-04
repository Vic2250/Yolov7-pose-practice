import copy
import gc
import time
import threading
import cv2
import json
import requests
import streamlit as st


# monitor item in this page
class IpCam:
    def __init__(self, url, name, group):
        self.name = name
        self.group = group
        self.video = cv2.VideoCapture(url)
        self.frame = []
        self.running = False
        self.thread_index = None

    def start(self):
        self.running = True
        self.thread_index = threading.Thread(target=self.show_video, args=(),
                                             daemon=True)
        self.thread_index.name = f'IpCam_{self.name}'
        self.thread_index.start()

    def stop(self):
        self.running = False
        self.thread_index.join()

    # the thread function to process the ready video
    def show_video(self):
        time.sleep(1)
        try:
            if not self.video.isOpened():
                self.frame = []
                raise Exception(
                    "Failed to connect to RTSP stream. Please check the RTSP URL.")
            while self.video.isOpened():
                if self.running is True:
                    start_time = time.time()
                    temp_status, temp_frame = self.video.read()
                    if temp_frame is not None:
                        temp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_RGB2BGR)
                        # temp_frame = temp_frame[::temp_frame.shape[0]//480, ::temp_frame.shape[1]//720]         # 1080*(3/8) & 1920*(3/8)
                        # temp_frame = cv2.resize(temp_frame, None, fx=0.6, fy=0.6)
                        self.frame = temp_frame
                        # del temp_status, temp_frame
                        end_time = time.time()
                        time.sleep(max(end_time-start_time, 0.0625-end_time+start_time))
                    else:
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    self.video.release()
                    break
        except Exception as e:
            print("Error: ", str(e))  # 顯示其他異常


css_style = """
    <style>
        .green {
            font-size: 20px;
            font-weight: bold;
            color: black;
            display: flex;
            justify-content: center;
            background-color: green;
            border-style: solid;
        }
        .red {
            font-size: 20px;
            font-weight: bold;
            color: black;
            display: flex;
            justify-content: center;
            background-color: red;
            border-style: solid;
        }
        .white {
            font-size: 20px;
            font-weight: bold;
            color: black;
            display: flex;
            justify-content: center;
            border-style: solid;
        }
        .text {
            font-size: 18px;
            font-weight: bold;
            display: flex;
            justify-content: center;
        }
    </style>
"""


# load all eligible number
def eligible_member():
    response = requests.get("http://[IP位置]:8000/get_white_list/").json()
    white_list = response["white_list"]
    return white_list


# check if the number valid
def check_member_list(member_index, member_list):
    for item in member_list:
        if item in member_index:
            return 'Green'
    return 'Red'


ipcam_device = []
rows = []


# show the all video
def vision(authenticator, monitor_info_list):
    global ipcam_device, rows

    # Stop the previous thread
    for ipcam_obj in ipcam_device:
        ipcam_obj.stop()
    for i in range(len(rows)):
        rows[i].empty()
    get_polling_url = "http://[IP位置]:8000/get_polling_result/"
    polling = requests.get(get_polling_url).json()
    ipcam_device = []
    rows = []
    col_index = []
    group_arrange = {}
    frame_window_text = []
    frame_window = []
    frame_window_detect = []
    member_list = eligible_member()
    st.markdown(css_style, unsafe_allow_html=True)

    # sort the monitor into groups
    for info in monitor_info_list:
        key = info[1]  # info[1]: Group
        if key in group_arrange:
            group_arrange[key].append(info)  # Append to the existing list
        else:
            group_arrange[key] = [info]  # Create a new list with the first element
    group_count = len(list(group_arrange.keys()))

    # show the loading icon until all video start processing video
    with st.spinner('Please Wait A Minute...'):
        for i, key in enumerate(group_arrange.keys()):
            for j, values in enumerate(group_arrange[key]):
                ipcam_device.append(IpCam(values[2], values[0], values[1]))
                ipcam_device[-1].start()
    if polling['loading'] == 0:
        # According different quantity to show different lay out
        if len(monitor_info_list) <= 3:
            rows.append(st.empty())
            with rows[0]:
                col_index.append(st.columns(len(monitor_info_list)))
                for j in range(len(monitor_info_list)):
                    with col_index[0][j]:
                        frame_window_text.append(st.empty())
                        frame_window.append(st.empty())
                        frame_window_detect.append(st.empty())
        else:
            if group_count % 3 == 0:
                row_index = group_count // 3
            else:
                row_index = (group_count // 3) + 1
            for i in range(row_index):
                rows.append(st.empty())
            for i in range(len(rows)):
                group_count_index = group_count - (3 * i)
                with rows[i]:
                    if group_count < 3:
                        if group_count != 1:
                            col_index.append(st.columns(group_count))
                            for j in range(group_count):
                                with col_index[0][j]:
                                    for k in range(len(group_arrange[
                                                        list(group_arrange.keys())[
                                                            j]])):
                                        frame_window_text.append(st.empty())
                                        frame_window.append(st.empty())
                                        frame_window_detect.append(st.empty())
                    else:
                        col_index.append(st.columns(3))
                        for j in range(group_count_index):
                            with col_index[i][j]:
                                for k in range(len(group_arrange[
                                                    list(group_arrange.keys())[
                                                        j]])):
                                    frame_window_text.append(st.empty())
                                    frame_window.append(st.empty())
                                    frame_window_detect.append(st.empty())
        # the api will use to get the detection id
        get_id_url = "http://[IP位置]:8000/get_detect_id/"
        grouping_id = {}

        # Main display vision code
        while True:
            authenticator.check_cookie_time_limit()
            response = requests.get(get_id_url)
            if response.json()["get_data"] is not False:
                grouping_id = copy.copy(response.json()["get_data"])
            
            for i in range(len(ipcam_device)):
                styled_index = f'<span class="text">{ipcam_device[i].name}</span>'
                frame_window_text[i].markdown(styled_index, unsafe_allow_html=True)
                start_time = time.time()
                frame_window[i].image(ipcam_device[i].frame, use_column_width=True)
                end_time = time.time()
                print(f'show one frame cost {end_time-start_time}')
                if grouping_id[ipcam_device[i].group][0][2] == '' or \
                        grouping_id[ipcam_device[i].group][0][2] == '-3':
                    grouping_id[ipcam_device[i].group][0][2] = 'Unknown'
                detect_text = '人員ID: ' + grouping_id[ipcam_device[i].group][0][2]
                if grouping_id[ipcam_device[i].group][0][2] == 'Unknown':
                    styled_text = f'<span class="white">{detect_text}</span>'
                else:
                    eligible = check_member_list(
                        grouping_id[ipcam_device[i].group][0][2], member_list)
                    if eligible == "Green":
                        styled_text = f'<span class="green">{detect_text}</span>'
                    else:
                        styled_text = f'<span class="red">{detect_text}</span>'
                frame_window_detect[i].markdown(styled_text, unsafe_allow_html=True)
                # time.sleep(0.05)
            
            gc.collect()
            st.cache_data.clear()
            st.cache_resource.clear()
    else:
        rows.append(st.empty())
        with rows[0]:
            col_index.append(st.columns(1))
            for j in range(len(col_index)):
                with col_index[0][j]:
                    frame_window_text.append(st.empty())
                    frame_window.append(st.empty())
                    frame_window_detect.append(st.empty())
        # the api will use to get the detection id
        get_id_url = "http://[IP位置]:8000/get_detect_id/"
        grouping_id = {}

        count = 0
        count_time = time.time()
        # Main display vision code
        while True:
            if count > len(ipcam_device)-1:
                count = 0
            authenticator.check_cookie_time_limit()
            response = requests.get(get_id_url)
            if response.json()["get_data"] is not False:
                grouping_id = copy.copy(response.json()["get_data"])

            styled_index = f'<span class="text">{ipcam_device[count].name}</span>'
            frame_window_text[0].markdown(styled_index, unsafe_allow_html=True)
            # frame_window_text[0].text(ipcam_device[count].name)
            
            frame_window[0].image(ipcam_device[count].frame, use_column_width=True)
            
            if grouping_id[ipcam_device[count].group][0][2] == '' or \
                    grouping_id[ipcam_device[count].group][0][2] == '-3':
                grouping_id[ipcam_device[count].group][0][2] = 'Unknown'
            detect_text = '人員ID: ' + grouping_id[ipcam_device[count].group][0][2]
            
            if grouping_id[ipcam_device[count].group][0][2] == 'Unknown':
                styled_text = f'<span class="white">{detect_text}</span>'
            else:
                eligible = check_member_list(
                    grouping_id[ipcam_device[count].group][0][2], member_list)
                if eligible == "Green":
                    styled_text = f'<span class="green">{detect_text}</span>'
                else:
                    styled_text = f'<span class="red">{detect_text}</span>'
            frame_window_detect[0].markdown(styled_text, unsafe_allow_html=True)
            # frame_window_detect[0].text(detect_text)
            end = time.time()
            if (end-count_time) > (0.0625*polling['loading']):
                count_time = end
                count += 1
            gc.collect()
            st.cache_data.clear()
            st.cache_resource.clear()

