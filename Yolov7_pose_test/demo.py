import streamlit as st
import streamlit_authenticator as stauth
import yaml
from streamlit_option_menu import option_menu
from yaml.loader import SafeLoader

from streamlit_authenticator.authenticate import Authenticate
from monitor_page import monitor_interface
from AI_Tool_page import model_interface
from setting_video_page import video_interface
from setting_account_page import account_interface
from setting_other_page import other_interface
from revise_pwd import change_pwd


# Define the main function to run the app
def index():
    st.set_page_config(layout='wide')
    # st.write('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)
    with open('account.yml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    placeholder = st.empty()
    with placeholder:
        if not st.session_state["authentication_status"]:
            placeholder.empty()
            login(authenticator)
        if st.session_state["authentication_status"]:
            placeholder.empty()
            dashboard(authenticator, config)


# Login interface
def login(authenticator):
    login_contain = st.container()
    with login_contain:
        title_cols = st.columns([0.2, 0.8])
        title_cols[1].title('人員AI偵測系統')
        st.text('')
        st.text('')
        login_cols = st.columns([0.25, 0.5, 0.25])
        with login_cols[1]:
            authenticator.login('登入', 'main')
            if st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')

            elif st.session_state["authentication_status"] is None:
                st.warning('Please enter your username and password')


# Main interface
def dashboard(authenticator, config):
    main_contain = st.container()
    # Display dashboard content
    with main_contain:
        main_cols = st.columns([0.8, 0.2])
        with main_cols[0]:
            st.title('人員AI偵測系統')
        with main_cols[1]:
            user_cols = st.columns([0.7, 0.3])
            with user_cols[0]:
                st.text('')
                st.write(f'Welcome *{st.session_state["name"]}*')
            with user_cols[1]:
                authenticator.logout('登出', 'main', key='unique_key')

        # Create sidebar menu. By clicking on different options, show the different view
        with st.sidebar:
            if st.session_state["name"] == 'admin':
                selected = option_menu("主選單",
                                       ["監控畫面", "AI模型管理", "影像設定",
                                        "帳號設定", "系統設定", "更改登入密碼"],
                                       icons=['cast', 'list-task', 'webcam', 'person-fill-gear', 'gear',
                                              'key'], menu_icon="house",
                                       default_index=0)
            else:
                selected = option_menu("主選單", ["監控畫面", "更改登入密碼"],
                                       icons=['cast', 'key'], menu_icon="house",
                                       default_index=0)

        if selected == '監控畫面':
            monitor_interface(authenticator)

        if selected == 'AI模型管理':
            model_interface(authenticator)
            
        if selected == '影像設定':
           video_interface(authenticator)

        if selected == '帳號設定':
           account_interface(authenticator, config)
           
        if selected == '系統設定':
           other_interface(authenticator)
        
        if selected == '更改登入密碼':
           change_pwd(authenticator, config)


if __name__ == '__main__':
    index()
