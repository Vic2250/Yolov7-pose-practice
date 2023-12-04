from st_aggrid import  JsCode

# AI模型列表-AgGrid-JavaScript語法
Model_BtnCellRenderer = JsCode('''
class Model_BtnCellRenderer {
    init(params) {
        this.params = params;
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = `
            <span>
                <button id='use-button' 
                    class='btn-simple' 
                    style='color: ${this.params.use_color}; 
                        background-color: white; 
                        border: 2px solid ${this.params.use_color}; 
                        border-radius: 5px; font-weight: 750'>掛載</button>
                <button id='delete-button' 
                    class='btn-simple' 
                    style='color: ${this.params.delete_color};
                        background-color: white;
                        border: 2px solid ${this.params.delete_color};
                        border-radius: 5px; font-weight: 750'>刪除</button>
            </span>
        `;

        this.use_eButton = this.eGui.querySelector('#use-button');
        this.delete_eButton = this.eGui.querySelector('#delete-button');

        this.use_btnClickedHandler = this.use_btnClickedHandler.bind(this);
        this.use_eButton.addEventListener('click', this.use_btnClickedHandler);

        this.delete_btnClickedHandler = this.delete_btnClickedHandler.bind(this);
        this.delete_eButton.addEventListener('click', this.delete_btnClickedHandler);

        // Check if the button should be disabled
        if (this.params.data.狀態 === '掛載中') {
            this.disableButton(); // 將掛載和刪除按鈕禁用
        }
        if (this.params.data.模型名稱 === 'yolov7-w6-pose.pt (預設)') {
            this.disable_delete_Button(); // 將刪除按鈕禁用
        }
    }

    getGui() {
        return this.eGui;
    }

    refresh() {
        return true;
    }

    call_Use_API(value) {
        const payload = {
            data: value // 設置 data 的值為 this.params.data
        };

        // 發送 POST 請求
        fetch("http://[IP位置]:8000/use_model/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json" // 設置表頭，指定發送的數據是 JSON 格式
            },
            body: JSON.stringify(payload) // 將數據轉成 JSON 格式
        })
        .then(response => {
            if (!response.ok) {
                // 請求失敗處理
                console.error("Request failed. Status:", response.status);
                alert('Error: Failed to fetch');
                throw new Error("Network response was not ok.");
            }
            return response.json();
        })
        .then(data => {
            // 請求成功處理
            console.log(data);
            alert(data.message);
        })
        .catch(error => {
            // 捕獲錯誤處理
            console.error("Error:", error);
        });
    }

    use_btnClickedHandler(event) {
        if (confirm('確定要掛載這個模型嗎?') == true) {

            // 檢查模型名稱
            if (this.params.data.模型名稱 === 'yolov7-w6-pose.pt (預設)') {
                // 如果是預設，則建立新變量取其原來的檔案名稱
                let model_name = 'yolov7-w6-pose.pt';
                // 使用新變量進行 call_use_API 函數
                this.call_Use_API(model_name);
            } else {
                // 其餘正常使用模型名稱傳入 call_use_API 函數
                this.call_Use_API(this.params.data.模型名稱);
            }
            this.disableButton();
            this.refreshTable('掛載中');
            this.resetOtherButtons();

        }
    }

    call_Delete_API(value) {
        const payload = {
            data: value // 設置 data 值為 this.params.data
        };

        // 發送 POST 請求
        fetch("http://[IP位置]:8000/delete_model/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json" // 設置表頭，指定發送的數據是 JSON 格式
            },
            body: JSON.stringify(payload) // 將數據轉換成 JSON 格式
        })
        .then(response => {
            if (!response.ok) {
                // 請求失敗處理
                console.error("Request failed. Status:", response.status);
                alert('Error: Failed to fetch');
                throw new Error("Network response was not ok.");
            }
            return response.json();
        })
        .then(data => {
            // 請求成功處理
            console.log(data);
            alert(data.message);
        })
        .catch(error => {
            // 捕獲錯誤處理
            console.error("Error:", error);
        });
    }

    delete_btnClickedHandler(event) {
        if (confirm('確定要刪除嗎?') == true) {
            this.call_Delete_API(this.params.data.模型名稱);

            // 在處理完畢後，移除表格中的行
            const rowIndex = this.params.rowIndex;
            this.params.api.applyTransaction({ remove: [this.params.data] });
            this.refreshTable('');
        }
    }



    disableButton() {
        this.use_eButton.disabled = true;
        this.use_eButton.style.backgroundColor = '#f2f2f2';
        this.use_eButton.style.color = 'black';
        this.use_eButton.style.border = '2px solid #cccccc';
        this.use_eButton.style.setProperty('font-weight', '300');
        this.disable_delete_Button();
    }

    disable_delete_Button() {
        this.delete_eButton.disabled = true;
        this.delete_eButton.style.backgroundColor = '#f2f2f2';
        this.delete_eButton.style.color = 'black';
        this.delete_eButton.style.border = '2px solid #cccccc';
        this.delete_eButton.style.setProperty('font-weight', '300');
    }

    resetOtherButtons() {
        const allRenderers = this.params.api.getCellRendererInstances();
        allRenderers.forEach(renderer => {
            if (renderer !== this && renderer.params.data.狀態) {
                renderer.enableButton();
            }
        });
    }

    enableButton() {
        this.use_eButton.disabled = false;
        this.delete_eButton.disabled = false;
        if (this.params.data.模型名稱 === 'yolov7-w6-pose.pt (預設)') {
            this.disable_delete_Button(); // 將刪除按鈕禁用
        }
        this.refreshTable('');
    }

    refreshTable(value) {
        this.params.setValue(value);
    }
};
''')


# video AgGrid-JavaScript
Video_BtnCellRenderer = JsCode('''
class Video_BtnCellRenderer {
    init(params) {
        this.params = params;
        this.eGui = document.createElement('div');
        this.editingCells = this.params.api.getEditingCells();
        this.isCurrentRowEditing = this.editingCells.some((cell) => {
            return cell.rowIndex === params.node.rowIndex;
        });
        this.params.api.addEventListener('cellEditingStopped', this.onCellEditingStopped.bind(this));
        this.showButtons();
    }

    getGui() {
        return this.eGui;
    }

    refresh() {
        return true;
    }

    showButtons() {
        if (this.isCurrentRowEditing) {
            this.eGui.innerHTML = `
                <button class="action-button update" data-action="update">Update</button>
                <button class="action-button cancel" data-action="cancel">Cancel</button>
            `;
            this.update_eButton = this.eGui.querySelector('.action-button.update');
            this.cancel_eButton = this.eGui.querySelector('.action-button.cancel');
            this.update_btnClickedHandler = this.update_btnClickedHandler.bind(this);
            this.update_eButton.addEventListener('click', this.update_btnClickedHandler);
            this.cancel_btnClickedHandler = this.cancel_btnClickedHandler.bind(this);
            this.cancel_eButton.addEventListener('click', this.cancel_btnClickedHandler);
        } else {
            this.eGui.innerHTML = `
                <button class="action-button edit" data-action="edit">編輯</button>
                <button class="action-button delete" data-action="delete">刪除</button>
            `;
            this.edit_eButton = this.eGui.querySelector('.action-button.edit');
            this.delete_eButton = this.eGui.querySelector('.action-button.delete');
            this.edit_btnClickedHandler = this.edit_btnClickedHandler.bind(this);
            this.edit_eButton.addEventListener('click', this.edit_btnClickedHandler);
            this.delete_btnClickedHandler = this.delete_btnClickedHandler.bind(this);
            this.delete_eButton.addEventListener('click', this.delete_btnClickedHandler);
        }
    }

    edit_btnClickedHandler (event) {
        this.params.api.startEditingCell({
            rowIndex: this.params.node.rowIndex,
            colKey: this.params.columnApi.getDisplayedCenterColumns()[1].colId
        });
        this.isCurrentRowEditing = true;
        this.showButtons();
    }

    delete_btnClickedHandler(event) {
        if (confirm('確定要刪除嗎?')) {
            const rowData = this.params.data;
            const rowIndex = this.params.rowIndex;
            this.call_Delete_API(rowData); // 呼叫 API 並傳遞 rowData 資訊
            this.params.api.applyTransaction({remove:[this.params.node.data]});
        }
    }

    call_Delete_API(rowData) {
        const payload = {
            data: rowData // 將 rowData 放入 payload
        };
        fetch("http://[IP位置]:8000/delete_monitor_info/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload) // 將 payload 轉成 JSON 格式
        })
        .then(response => {
            if (!response.ok) {
                console.error("Request failed. Status:", response.status);
                alert('Error: Failed to fetch');
                throw new Error("Network response was not ok.");
            }
            return response.json();
        })
        .then(data => {
            console.log(data);
            alert(data.message);
        })
        .catch(error => {
            console.error("Error:", error);
        });
    }

    update_btnClickedHandler(event) {
        if (confirm('確定編輯完成?')) {
            const rowData = this.params.data;
            this.params.api.stopEditing();
            this.call_Update_API(rowData); // 呼叫 API 並傳遞 rowData 資訊
            this.isCurrentRowEditing = false;
            this.showButtons();
        }
    }

    call_Update_API(rowData) {
        const payload = {
            data: rowData // 將 rowData 放入 payload
        };
        fetch("http://[IP位置]:8000/change_monitor_info/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload) // 將 payload 轉成 JSON 格式
        })
        .then(response => {
            if (!response.ok) {
                console.error("Request failed. Status:", response.status);
                alert('Error: Failed to fetch');
                throw new Error("Network response was not ok.");
            }
            return response.json();
        })
        .then(data => {
            console.log(data);
            alert(data.message);
        })
        .catch(error => {
            console.error("Error:", error);
        });
    }

    cancel_btnClickedHandler(event) {
        this.params.api.stopEditing();
        this.isCurrentRowEditing = false;
        this.showButtons(); // 更新按鈕顯示
    }

    onCellEditingStopped(event) {
        if (event.node === this.params.node) {
            this.rowIndex = -1;
            this.isCurrentRowEditing = false;
            this.showButtons();
        }
    }
}
''')


# account AgGrid-JavaScript
Account_BtnCellRenderer = JsCode('''
class Account_BtnCellRenderer {
    init(params) {
        this.params = params;
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = `
         <span>
            <button id='reset-button' 
                class='btn-simple' 
                style='color: ${this.params.reset_color}; background-color: white; border: 2px solid ${this.params.reset_color}; border-radius: 5px; font-weight: 750'>重置</button>
            <button id='delete-button' 
                class='btn-simple' 
                style='color: ${this.params.delete_color}; background-color: white; border: 2px solid ${this.params.delete_color}; border-radius: 5px; font-weight: 750'>刪除</button>
         </span>
      `;

        this.reset_eButton = this.eGui.querySelector('#reset-button');
        this.delete_eButton = this.eGui.querySelector('#delete-button');

        this.reset_btnClickedHandler = this.reset_btnClickedHandler.bind(this);
        this.reset_eButton.addEventListener('click', this.reset_btnClickedHandler);
        this.delete_btnClickedHandler = this.delete_btnClickedHandler.bind(this);
        this.delete_eButton.addEventListener('click', this.delete_btnClickedHandler);

        if (this.params.data.Username === 'admin') {
            this.disable_delete_Button(); // 將刪除按鈕禁用
        }
    }

    getGui() {
        return this.eGui;
    }

    refresh() {
        return true;
    }

    reset_btnClickedHandler(event) {
        if (confirm('確定要將這個帳號重設為預設密碼嗎?') == true) {
            this.call_Reset_API(this.params.data.Username);
        }
    };

    call_Reset_API(value) {
        const payload = {
            Username: value // 設置 data 的值為 this.params.data
        };

        // 發送 POST 請求
        fetch("http://[IP位置]:8000/reset_account/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json" // 設置表頭，指定發送的數據是 JSON 格式
            },
            body: JSON.stringify(payload) // 將數據轉成 JSON 格式
        })
        .then(response => {
            if (!response.ok) {
                // 請求失敗處理
                console.error("Request failed. Status:", response.status);
                alert('Error: Failed to fetch');
                throw new Error("Network response was not ok.");
            }
            return response.json();
        })
        .then(data => {
            // 請求成功處理
            console.log(data);
            alert(data.message);
        })
        .catch(error => {
            // 捕獲錯誤處理
            console.error("Error:", error);
        });
    }

    delete_btnClickedHandler(event) {
        if (confirm('確定要刪除這個帳號嗎?') == true) {
            const rowData = this.params.data;
            const rowIndex = this.params.rowIndex;
            this.call_Delete_API(this.params.data.Username);
            this.params.api.applyTransaction({remove:[this.params.node.data]});
        }
    };
    call_Delete_API(value) {
        const payload = {
            Username: value // 設置 data 值為 this.params.data
        };

        // 發送 POST 請求
        fetch("http://[IP位置]:8000/delete_account/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json" // 設置表頭，指定發送的數據是 JSON 格式
            },
            body: JSON.stringify(payload) // 將數據轉換成 JSON 格式
        })
        .then(response => {
            if (!response.ok) {
                // 請求失敗處理
                console.error("Request failed. Status:", response.status);
                alert('Error: Failed to fetch');
                throw new Error("Network response was not ok.");
            }
            return response.json();
        })
        .then(data => {
            // 請求成功處理
            console.log(data);
            alert(data.message);
        })
        .catch(error => {
            // 捕獲錯誤處理
            console.error("Error:", error);
        });
    }
    disable_delete_Button() {
        this.delete_eButton.disabled = true;
        this.delete_eButton.style.backgroundColor = '#f2f2f2';
        this.delete_eButton.style.color = 'black';
        this.delete_eButton.style.border = '2px solid #cccccc';
        this.delete_eButton.style.setProperty('font-weight', '300');
    }
}
''')
