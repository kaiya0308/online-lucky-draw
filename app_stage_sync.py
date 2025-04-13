import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import json

# 認證與連線 Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1hQ4nWSScK4tQIG1XUZyflCZauGj1MUtApICIglsdSmg")
ws = sheet.sheet1
ws_prizes = sheet.worksheet("獎項")  # 額外抓獎項工作表

st.set_page_config(layout="centered", page_title="抽獎舞台畫面")

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
st.title("🎬 舞台投影畫面")

placeholder = st.empty()
last_state = {}

def get_prize_count(prize_name):
    try:
        data = ws_prizes.get_all_records()
        for row in data:
            if row["獎項名稱"] == prize_name:
                return row["名額"]
    except:
        return ""
    return ""

while True:
    data = ws.get_all_values()
    if len(data) >= 2:
        row = data[1]
        if len(row) < 5:
            row += [""] * (5 - len(row))
        state = {
            "stage": row[0].strip(),
            "prize": row[1].strip(),
            "name": row[2].strip(),
            "title": row[3].strip(),
            "team": row[4].strip()
        }

        if state != last_state:
            with placeholder.container():
                if state["stage"] == "prize" and state["prize"]:
                    count = get_prize_count(state["prize"])
                    st.markdown(f"<div class='big'>🎁 現在抽的是：{state['prize']}（共 {count} 名）</div>", unsafe_allow_html=True)
                elif state["stage"] == "winner" and state["name"]:
                    st.markdown(f"<div class='big'>🎉 恭喜：{state['name']}<br>{state['title']} - {state['team']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='big'>等待主持人操作...</div>", unsafe_allow_html=True)
            last_state = state

    time.sleep(2)
