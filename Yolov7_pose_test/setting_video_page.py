import time
import requests
import json
import pandas as pd
import streamlit as st
import streamlit_toggle as tog
from PIL import Image
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_cropper import st_cropper
from aggrid_vision import Video_BtnCellRenderer


# load all video_data (for cropped image)
def load_data():
    data = requests.get("http://[IP位置]:8000/get_video_data/").json()
    data = remove_all(data)
    return data

def remove_all(node):
    if isinstance(node, dict):
        if '全' in node:
            del node['全']
        for key, value in node.items():
            node[key] = remove_all(value)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            node[i] = remove_all(item)
    return node


# create dataframe for video_data list
def make_data():
    data = requests.get("http://[IP位置]:8000/get_video_data/").json()
    rows = []
    for factory, factory_data in data.items():
        for factory_name, factory_item in factory_data.items():
            for floor, floor_data in factory_item.items():
                for floor_name, floor_item in floor_data.items():
                    for site, site_data in floor_item.items():
                        for site_name, site_items in site_data.items():
                            for monitor, monitor_data in site_items.items():
                                for monitor_name, monitor_items in monitor_data.items():
                                    if monitor_name != "全":
                                        rows.append({
                                            "Rtsp串流位置": monitor_items["URL"],
                                            "地點": factory_name,
                                            "樓層": floor_name,
                                            "範圍": site_name,
                                            "監視器": monitor_name,
                                            "群組": monitor_items["Group"],
                                            "ID": monitor_items["ID"]
                                        })
    df = pd.DataFrame(rows)
    return df


# get all group
def group_data():
    # load all video_data
    data = requests.get("http://[IP位置]:8000/get_video_data/").json()

    # get the not repeating group
    unique_groups = []
    seen_groups = set()
    for factory, factory_data in data.items():
        for factory_name, factory_item in factory_data.items():
            for floor, floor_data in factory_item.items():
                for floor_name, floor_item in floor_data.items():
                    for site, site_data in floor_item.items():
                        for site_name, site_items in site_data.items():
                            for monitor, monitor_data in site_items.items():
                                for monitor_name, monitor_items in monitor_data.items():
                                    if monitor_name != "全":
                                        group = monitor_items["Group"]
                                        detected = monitor_items["Detect"]
                                        if group not in seen_groups:
                                            seen_groups.add(group)
                                            unique_groups.append({'群組': group,
                                                                  '偵測辨識': detected})
    df = pd.DataFrame(unique_groups)
    return unique_groups, df


# update the group detection
def detected_update(different_list):
    # update all data group detection
    detection_response = requests.post("http://[IP位置]:8000/update_video_detect/", json={"data": different_list})
    
    # to notify RTSP server should update the all video information
    response = requests.get("http://[IP位置]:8000/rebuild_rtsp/")


# get the max_id (for add video)
def find_max_id(node):
    max_id = 0
    if isinstance(node, dict):
        if "ID" in node:
            max_id = node["ID"]
        for key, value in node.items():
            max_id = max(max_id, find_max_id(value))
    elif isinstance(node, list):
        for item in node:
            max_id = max(max_id, find_max_id(item))
    return max_id


# update the detection area
def update_detection_area(camera_name, rectangle_info):
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
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
                                    if monitor_name == camera_name:
                                        monitor_items["Start_X"] = \
                                        rectangle_info[0]
                                        monitor_items["Start_Y"] = \
                                        rectangle_info[1]
                                        monitor_items["Width"] = rectangle_info[
                                            2]
                                        monitor_items["Height"] = \
                                        rectangle_info[3]
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    response = requests.get("http://[IP位置]:8000/rebuild_rtsp/")


# video_interface code
def video_interface(authenticator):
    authenticator.check_cookie_time_limit()
    add_monitor_url = "http://[IP位置]:8000/add_monitor_info/"
    st.text('')
    st.text('')
    st.subheader('影像來源設定')
    st.text('')
    cols = st.columns([0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.1])
    with cols[0]:
        url = st.text_input('Rtsp串流位置')
    with cols[1]:
        factory = st.text_input('地點')
    with cols[2]:
        floor = st.number_input('樓層', min_value=1, max_value=15, step=1)
    with cols[3]:
        site = st.text_input('範圍')
    with cols[4]:
        camera_name = st.text_input('影像名稱')
    with cols[5]:
        camera_grouping = st.text_input('群組')
    with cols[6]:
        st.text('')
        st.text('')
        add_video = st.button('新增', use_container_width=True, key="add_video")

    df = make_data()
    # AgGrid settings
    group_origin, group_df = group_data()
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False)
    gb.configure_column('樓層',
                        cellEditor='agSelectCellEditor',
                        cellEditorParams={
                            'values': ['1F', '2F', '3F', '4F', '5F', '6F', '7F',
                                       '8F', '9F', '10F', '11F', '12F', '13F',
                                       '14F', '15F'], 'valueListGap': 100},
                        cellEditorPopup=True
                        )
    gb.configure_grid_options()
    grid_options = gb.build()
    grid_options['suppressClickEdit'] = True
    column_defs = grid_options["columnDefs"]
    columns_to_hide = ["ID"]
    columns_to_adjust = ["Rtsp串流位置"]

    # update the column definitions to hide the specified columns
    for col in column_defs:
        col["width"] = 165
        if col["headerName"] in columns_to_hide:
            col["hide"] = True
        if col["headerName"] in columns_to_adjust:
            col["width"] = 225
    grid_options['columnDefs'].append({
        "headerName": "設定",
        "cellRenderer": Video_BtnCellRenderer,
        "editable": False,
        "colId": "action"
    })
    grid_options['editType'] = "fullRow"
    grid_options['rowStyle'] = {'background-color': 'white !important',
                                'font-size': '15px !important',
                                'font-family': 'Gill Sans !important', }
    grid_options['rowHeight'] = 35
    grid_options['pagination'] = True
    grid_options['paginationPageSize'] = 10
    grid_options['defaultColDef'] = {
        "editable": True,
    }
    custom_css = {
        ".ag-root.ag-unselectable.ag-layout-normal": {
            "font-size": "18px !important",
            "font-family": "Roboto, sans-serif !important;",
        },
        ".ag-header-cell": {
            "font-size": "20px !important",
            'font-family': 'Gill Sans',
        },
        ".ag-row-hover": {"background-color": "#EEFFC9 !important"},
        ".action-button": {
            "border": None,
            "color": "white !important",
            "padding": "1px 11px !important",
            "text-align": "center !important",
            "display": "inline-block !important",
            "font-size": "16 !important",
            "opacity": "0.7 !important",
            "border-radius": "5px !important",
        },
        ".action-button:hover": {"opacity": "1 !important"},
        ".action-button.edit": {"background-color": "#008cba !important"},
        ".action-button.update": {"background-color": "#4caf50 !important"},
        ".action-button.delete": {"background-color": "#f44336 !important"},
        ".action-button.cancel": {"background-color": "black !important"},
    }
    time.sleep(0.5)
    placeholder = st.empty()
    with placeholder:
        AgGrid(df,
               theme="streamlit",
               key='table1',
               gridOptions=grid_options,
               allow_unsafe_jscode=True,
               fit_columns_on_grid_load=True,
               reload_data=True,
               try_to_convert_back_to_original_types=False,
               custom_css=custom_css)
    st.text('')
    st.text('')
    cols1 = st.columns([0.25, 0.05, 0.7])
    with cols1[0]:
        st.subheader('影像來源偵測設定')
        st.text('')
        st.text('')
        grid_options = st.data_editor(group_df, key="group_editor",
                                      use_container_width=True)
        result_dict_list = grid_options.to_dict(orient='records')
        differences = []
        for dict1, dict2 in zip(group_origin, result_dict_list):
            if dict1 != dict2:
                differences.append(dict2)
        if len(differences) != 0:
            detected_update(differences)
            st.experimental_rerun()
    with cols1[2]:
        st.subheader('影像辨識區域設定')
        st.text('')
        place1, place2, place3, place4 = st.columns(4)
        data = load_data()
        with place1:
            selected_factory = st.selectbox('地點',
                                            ['-', *list(data['地點'].keys())],
                                            key='image_info1')
            show_option_2 = False
            show_option_3 = False
            show_option_4 = False
            if selected_factory != '-':
                show_option_2 = True
            else:
                place2.empty()
                place3.empty()
                place4.empty()

        if show_option_2:
            with place2:
                selected_floor = st.selectbox('樓層', ['-', *list(
                    data['地點'][selected_factory]['樓層'].keys())],
                                              key='image_info2')
                if selected_floor != '-':
                    show_option_3 = True
                else:
                    place3.empty()
                    place4.empty()

        if show_option_3:
            with place3:
                selected_site = st.selectbox('範圍', ['-', *list(
                    data['地點'][selected_factory]['樓層'][selected_floor][
                        '範圍'].keys())], key='image_info3')
                if selected_site != '-':
                    show_option_4 = True
                else:
                    place4.empty()

        if show_option_4:
            with place4:
                selected_monitor = st.selectbox('監視器', list(
                    data['地點'][selected_factory]['樓層'][selected_floor][
                        '範圍'][selected_site]['監視器'].keys()),
                                                key='image_info4')

        show_cropper = st.empty()
        if show_option_4:
            with show_cropper:
                with st.form('frame_limit') as f:
                    st.markdown('###### 將要辨識的區域框選出來')
                    frame1, frame2, frame3 = st.columns([0.1, 0.8, 0.1])
                    with frame2:
                        img = Image.open(f'Image/{selected_monitor}.jpg')
                        selected_monitor_info = data['地點'][selected_factory] \
                                                    ['樓層'][selected_floor] \
                                                    ['範圍'][selected_site] \
                                                    ['監視器'][selected_monitor]
                        default_window = (selected_monitor_info['Start_X'], selected_monitor_info['Start_X']+selected_monitor_info['Width'], 
                                          selected_monitor_info['Start_Y'], selected_monitor_info['Start_Y']+selected_monitor_info['Height'])
                        # Get a cropped image from the frontend
                        cropped_img = st_cropper(img,
                                                 realtime_update=True,
                                                 default_coords=default_window,      # (左上x, 右下x, 左上y, 右下y)
                                                 box_color='#FF0004',
                                                 aspect_ratio=None,
                                                 return_type="box")
                    submit1, submit2 = st.columns([0.9, 0.1])
                    with submit2:
                        store_image_place = st.form_submit_button('儲存')
                    if store_image_place:
                        rectangle = []
                        for i in cropped_img:
                            rectangle.append(cropped_img[i])
                        # Assuming update_detection_area is defined and works correctly
                        update_detection_area(selected_monitor, rectangle)
    if add_video:
        if url and factory and floor and site and camera_name and camera_grouping is not None:
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            max_id = find_max_id(data) + 1
            add_data = {"地點": {factory.strip(): {"樓層": {
                f'{str(floor)}F': {"範圍": {site.strip(): {
                    "監視器": {"全": "", camera_name.strip(): {"ID": max_id,
                                                               "URL": url.strip(),
                                                               "Group": camera_grouping.strip(),
                                                               "Detect": True,
                                                               "Start_X": 0,
                                                               "Start_Y": 0,
                                                               "Width": 1920,
                                                               "Height": 1080,
                                                               "RTSP": f"rtsp://[IP位置]:8554/{camera_name.strip()}"}}}}}}}}}
            print(add_data)
            response = requests.post(add_monitor_url, json=add_data)
            print(response.text)
            st.experimental_rerun()
