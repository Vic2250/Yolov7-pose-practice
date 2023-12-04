import requests
import time
import json
import streamlit as st
from monitor_vision import vision


# load all video data
def load_data():
    data = requests.get("http://[IP位置]:8000/get_video_data/").json()
    return data


# chose the different selection will use the different data to show
def monitor_interface(authenticator):
    authenticator.check_cookie_time_limit()
    st.text('')
    st.text('')
    col1, col2, col3, col4 = st.columns(4)
    monitor_url = []
    monitor_names = []
    data = load_data()
    with col1:
        selected_factory = st.selectbox('地點',
                                        ['-', *list(data['地點'].keys())], index=0)
        show_option_2 = False
        show_option_3 = False
        show_option_4 = False
        if selected_factory != '-':
            show_option_2 = True
        else:
            col2.empty()
            col3.empty()
            col4.empty()

        if show_option_2:
            with col2:
                selected_floor = st.selectbox('樓層', ['-', *list(
                    data['地點'][selected_factory]['樓層'].keys())], index=0)
                if selected_floor != '-':
                    show_option_3 = True
                else:
                    col3.empty()
                    col4.empty()

        if show_option_3:
            with col3:
                selected_site = st.selectbox('範圍', ['-', *list(
                    data['地點'][selected_factory]['樓層'][selected_floor][
                        '範圍'].keys())], index=0)
                if selected_site != '-':
                    show_option_4 = True
                else:
                    col4.empty()

        if show_option_4:
            with col4:
                selected_monitor = st.selectbox('監視器', list(
                    data['地點'][selected_factory]['樓層'][selected_floor][
                        '範圍'][
                        selected_site]['監視器'].keys()))
                monitor_url.clear()
                monitor_names.clear()
                if selected_monitor == '全':
                    # 獲取除了'全'以外的所有監視器的URL
                    monitor_info = \
                    data['地點'][selected_factory]['樓層'][selected_floor][
                        '範圍'][selected_site]['監視器']
                    urls = [v['RTSP'] for k, v in monitor_info.items() if k != '全']
                    groups = [v['Group'] for k, v in monitor_info.items() if
                              k != '全']
                    names = [k for k, v in monitor_info.items() if k != '全']
                    for url, name, group in zip(urls, names, groups):
                        monitor_url.append(url)
                        monitor_names.append((selected_factory, selected_floor, selected_site, name, group))
                else:
                    # 獲取選定的監視器的URL
                    url = data['地點'][selected_factory]['樓層'][
                        selected_floor]['範圍'][selected_site]['監視器'][
                        selected_monitor]['RTSP']
                    group = data['地點'][selected_factory]['樓層'][
                        selected_floor]['範圍'][selected_site]['監視器'][
                        selected_monitor]['Group']
                    monitor_url.append(url)
                    monitor_names.append((selected_factory, selected_floor, selected_site, selected_monitor, group))
    st.text('')
    monitor_info_list = [(name[3], name[4], url, name[0], name[1], name[2]) for name, url in
                         zip(monitor_names, monitor_url)]
    # monitor_info_list = ['name', 'group', 'url', 'factory', 'floor', 'site']
    video_display = st.empty()
    check_list = []
    if monitor_info_list:
        if check_list != monitor_info_list:
            video_display.empty()
            vision(authenticator, monitor_info_list)

