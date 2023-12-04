import requests
import time
import numpy as np
import pandas as pd
import streamlit as st
import yaml
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from aggrid_vision import Account_BtnCellRenderer


# create dataframe for account
def make_data():
    # load all account name
    with open('account.yml', 'r') as file:
        data = yaml.safe_load(file)
    credentials = data.get('credentials', {})
    usernames = credentials.get('usernames', {})

    # create a list to store new account name and password
    data_list = []
    for username, info in usernames.items():
        name = info.get('name', '')
        password = '********'
        data_list.append([username, name, password])

    # create dataframe
    df = pd.DataFrame(data_list, columns=['Username', 'Name', 'Password'])
    return df


# account_interface code
def account_interface(authenticator, config):
    authenticator.check_cookie_time_limit()
    add_account_url = "http://[IP位置]:8000/add_account/"
    df = make_data()
    # AgGrid settings
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)
    grid_options = gb.build()
    grid_options['columnDefs'].append({
        "header": "",
        "cellRenderer": Account_BtnCellRenderer,
        "cellRendererParams": {
            "reset_color": "black",
            "delete_color": "red",
        },
    })
    grid_options['rowStyle'] = {'background-color': 'white',
                                'font-size': '15px',
                                'font-family': 'Gill Sans', }
    grid_options['rowHeight'] = 35
    grid_options['pagination'] = True
    grid_options['paginationPageSize'] = 10
    custom_css = {
        ".ag-root.ag-unselectable.ag-layout-normal": {
            "font-size": "18px !important",
            "font-family": "Roboto, sans-serif !important;",
        },
        ".ag-header-cell": {
            "font-size": "20px !important",
            'font-family': 'Gill Sans',
        },
        ".ag-row-hover": {"background-color": "#FFFF99 !important"},
    }

    st.text('')
    st.text('')
    st.subheader('系統登入帳密')
    response = AgGrid(df,
                      theme="streamlit",
                      key='account_table',
                      gridOptions=grid_options,
                      allow_unsafe_jscode=True,
                      fit_columns_on_grid_load=True,
                      reload_data=True,
                      try_to_convert_back_to_original_types=False,
                      custom_css=custom_css
                      )
    st.text('')
    st.text('')
    # a form for create a new account
    try:
        if authenticator.register_user('創建新帳號', preauthorization=False):
            add_account_response = requests.post(add_account_url, json={"Data": config}).json()
            st.success('User registered successfully')
            time.sleep(1)
            st.experimental_rerun()

    except Exception as e:
        st.error(e)
