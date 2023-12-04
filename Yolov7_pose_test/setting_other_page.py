import streamlit as st
import streamlit_toggle as tog
import yaml
import requests


# other_interface code
def other_interface(authenticator):
    authenticator.check_cookie_time_limit()
    other_info = requests.get("http://[IP位置]:8000/get_other_info/").json()
    print(other_info)
    st.text('')
    st.text('')
    st.subheader('系統逾時登出管理')
    # st.markdown('##### 系統逾時登出管理')
    st.text('')
    time1, time2 = st.columns((0.1, 0.5))
    with time1:
        user_timeout = tog.st_toggle_switch(label="系統逾時設定",
                                            key="user_time",
                                            default_value=other_info['timeout_switch'],
                                            label_after=False,
                                            inactive_color='#D3D3D3',
                                            active_color="#11567f",
                                            track_color="#29B5E8"
                                            )
    if user_timeout is True:
        with time2:
            time3, time4 = st.columns(2)
            with time3:
                minute_input = st.number_input('timeout', min_value=0, step=1,
                                               value=other_info['timeout'], key="key1",
                                               label_visibility='collapsed')
            with time4:
                st.text('')
                second = st.text('分鐘')

    st.text('')
    st.subheader('影像辨識輪循設定')
    # st.markdown('##### 影像辨識輪循設定')
    st.text('')
    col1, col2 = st.columns((0.1, 0.5))
    with col1:
        video_count = tog.st_toggle_switch(label="系統輪循設定",
                                           key="Key2",
                                           default_value=other_info['polling'],
                                           label_after=False,
                                           inactive_color='#D3D3D3',
                                           active_color="#FFA500",
                                           track_color="#FF8C00"
                                           )
    if video_count is True:
        with col2:
            col3, col4 = st.columns(2)
            with col3:
                frame_count = st.number_input('frame_count', min_value=0, step=1,
                                              value=other_info['interval'], key='key2',
                                              label_visibility='collapsed')
            with col4:
                st.text('')
                frame = st.text('幀')

    st.text('')
    st.text('')
    col5, col6 = st.columns((0.8, 0.3))
    with col6:
        save = st.button('Save')

    # save event
    if save:
        if user_timeout is True:
            with open('config.yml', 'r', encoding='utf-8') as f:
                other_config = yaml.safe_load(f)
            other_config['timeout'] = minute_input
            # 紀錄現在的timeout值，供之後頁面預顯示該值
            with open('config.yml', 'w', encoding='utf-8') as f:
                yaml.dump(other_config, f)
            
            with open('account.yml', 'r', encoding='utf-8') as f:
                login_config = yaml.safe_load(f)
            authenticator.cookie_expiry_days = minute_input / 1440
            login_config['cookie']['expiry_days'] = minute_input / 1440
            # 將修改後的內容寫回到account.yml檔案
            with open('account.yml', 'w', encoding='utf-8') as f:
                yaml.dump(login_config, f)
            st.toast('設定已更改，下次登入後生效')
            
        if user_timeout is not True:
            with open('account.yml', 'r', encoding='utf-8') as f:
                login_config = yaml.safe_load(f)
            authenticator.cookie_expiry_days = 0
            login_config['cookie']['expiry_days'] = 0
            # 將修改後的內容寫回到account.yml檔案
            with open('account.yml', 'w', encoding='utf-8') as f:
                yaml.dump(login_config, f)
            st.toast('設定已更改，下次登入後生效')

        if video_count is True:
            with open('config.yml', 'r', encoding='utf-8') as f:
                loading_config = yaml.safe_load(f)
            loading_config['polling']['enabled'] = True
            if frame_count == 0:
                loading_config['polling']['enabled'] = False
            loading_config['polling']['interval'] = frame_count
            # 將修改後的內容寫回到config.yml檔案
            with open('config.yml', 'w', encoding='utf-8') as f:
                yaml.dump(loading_config, f)

        if video_count is not True:
            with open('config.yml', 'r', encoding='utf-8') as f:
                loading_config = yaml.safe_load(f)
            loading_config['polling']['enabled'] = False
            # 將修改後的內容寫回到config.yml檔案
            with open('config.yml', 'w', encoding='utf-8') as f:
                yaml.dump(loading_config, f)