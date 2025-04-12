import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# Google Sheet 設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
sheet_url = "https://docs.google.com/spreadsheets/d/1hQ4nWSScK4tQIG1XUZyflCZauGj1MUtApICIglsdSmg"
spreadsheet_id = sheet_url.split("/d/")[1].split("/")[0]

@st.cache_resource
def connect_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name("gcp_credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id)
    return sheet

def get_current_state():
    sheet = connect_sheet()
    ws = sheet.sheet1
    data = ws.get_all_values()
    if len(data) >= 2:
        row = data[1]
        if len(row) < 5:
            row += [""] * (5 - len(row))
        return {
            "stage": row[0],
            "prize": row[1],
            "name": row[2],
            "title": row[3],
            "team": row[4]
        }
    return None

# 設定背景
def set_bg(image_file):
    with open(image_file, "rb") as f:
        import base64
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            text-align: center;
            color: white;
        }}
        .big {{
            font-size: 60px;
            font-weight: bold;
            margin-top: 100px;
        }}
        </style>
    """, unsafe_allow_html=True)

set_bg("my_bg.jpg")
st.set_page_config(layout="centered", page_title="抽獎舞台畫面")

st.title("🎬 舞台投影畫面")

placeholder = st.empty()

# 自動更新畫面
while True:
    state = get_current_state()
    with placeholder.container():
        if state:
            if state["stage"] == "prize":
                st.markdown(f"<div class='big'>🎁 現在抽的是：{state['prize']}</div>", unsafe_allow_html=True)
            elif state["stage"] == "winner":
                st.markdown(f"<div class='big'>🎉 恭喜：{state['name']}<br>{state['title']} - {state['team']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='big'>等待主持人操作...</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='big'>尚未讀取到資料</div>", unsafe_allow_html=True)
    time.sleep(2)
