# 人員AI偵測系統

### 開發環境
1. Ubuntu: 18.04.6
2. Anaconda: https://www.anaconda.com/
3. Python version: 3.8.18

### 執行步驟

開啟兩個Terminal，並在以下Terminal執行各自的指令:

##### Terminal 1

```python
uvicorn API_server:app --host [自訂IP位置] -- port [自訂Port]
```

##### Terminal 2

```
streamlit run index.py
```

### 參考來源
 - https://github.com/WongKinYiu/yolov7
 - https://github.com/RizwanMunawar/yolov7-pose-estimation
 - https://steam.oxxostudio.tw/category/python/ai/opencv-read-video.html
 - https://github.com/prabhakar-sivanesan/OpenCV-rtsp-server