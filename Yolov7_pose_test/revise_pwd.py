import requests
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def change_pwd(authenticator, config):
    authenticator.check_cookie_time_limit()
    st.text('')
    st.text('')
    if st.session_state["authentication_status"]:
        try:
            if authenticator.reset_password(st.session_state["username"],
                                            'Reset password'):
                response = requests.post("http://[IP位置]:8000/set_pwd/", json={"Data": config})
                st.success('Password modified successfully')
        except Exception as e:
            st.error(e)
