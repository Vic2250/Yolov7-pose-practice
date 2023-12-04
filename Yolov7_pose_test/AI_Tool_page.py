import requests
import time
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from pathlib import Path
import yaml

from aggrid_vision import Model_BtnCellRenderer


# load the model name in config.yml
def open_yaml():
    response = requests.get("http://[IP位置]:8000/get_model/").json()
    now_model = response["now_model"]
    return now_model


# get all model name in the folder
def get_file_names():
    response = requests.get("http://[IP位置]:8000/get_all_model_name/").json()
    all_model = response["all_model_name"]
    return all_model


# get the dataframe which will show on the page
def make_data():
    model_name = get_file_names()
    df = pd.DataFrame(
        {
            "模型名稱": model_name,
            "狀態": [""] * len(model_name),
        }
    )
    load = open_yaml()
    df.loc[df["模型名稱"] == load, "狀態"] = "掛載中"
    if "yolov7-w6-pose.pt" in model_name:
        df.loc[df["模型名稱"] == "yolov7-w6-pose.pt", "模型名稱"] = "yolov7-w6-pose.pt (預設)"
    return df


# main model interface code
def model_interface(authenticator):
    authenticator.check_cookie_time_limit()
    st.text('')
    st.text('')
    st.subheader("模型清單")

    df = make_data()
    # the AgGrid setting
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False)
    gb.configure_grid_options()
    grid_options = gb.build()
    grid_options['columnDefs'].append({
        "field": "狀態",
        "headerName": "操作",
        "cellRenderer": Model_BtnCellRenderer,
        "cellRendererParams": {
            "use_color": "#0099ff",
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
    # show AgGrid
    response = AgGrid(df,
                      theme="streamlit",
                      key='table1',
                      gridOptions=grid_options,
                      allow_unsafe_jscode=True,
                      fit_columns_on_grid_load=True,
                      reload_data=True,
                      try_to_convert_back_to_original_types=False,
                      custom_css=custom_css
                      )
    # Upload code
    uploaded_file = st.file_uploader("請上傳欲上傳的模型權重檔", type=['pt'],
                                     key=None)
    if uploaded_file is not None:
        st.text(uploaded_file.name)
        submit = st.button('確定')
        if submit:
            save_folder = 'Model'
            save_path = Path(save_folder, uploaded_file.name)
            if save_path.exists():
                st.error(
                    f'檔名 "{uploaded_file.name}" 已存在於資料夾中，請重新命名。')
                time.sleep(1)
                st.experimental_rerun()
            else:
                with open(save_path, mode='wb') as w:
                    w.write(uploaded_file.getvalue())
                if save_path.exists():
                    st.success(f'檔案 "{uploaded_file.name}" 儲存成功！')
                    time.sleep(1)
                    st.experimental_rerun()
