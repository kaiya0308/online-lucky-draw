import streamlit as st
import pandas as pd
import random
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
import json

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1hQ4nWSScK4tQIG1XUZyflCZauGj1MUtApICIglsdSmg")
ws = sheet.sheet1

def update_sheet(stage, prize="", name="", title="", team=""):
    ws.update("A2", [[stage, prize, name, title, team]])

if "participants_df" not in st.session_state:
    st.session_state.participants_df = None
if "prizes_df" not in st.session_state:
    st.session_state.prizes_df = None
if "current_prize_index" not in st.session_state:
    st.session_state.current_prize_index = 0
if "drawn_count" not in st.session_state:
    st.session_state.drawn_count = 0
if "current_winners" not in st.session_state:
    st.session_state.current_winners = []

st.set_page_config(layout="centered", page_title="抽獎控制端")
st.title("🎯 控制端（獎項即時顯示 + 防錯）")

uploaded = st.file_uploader("📥 上傳抽獎 Excel", type="xlsx")
if uploaded:
    df_part = pd.read_excel(uploaded, sheet_name="參加者")
    df_prizes = pd.read_excel(uploaded, sheet_name="獎項")
    df_part["狀態"] = df_part["狀態"].fillna("")
    st.session_state.participants_df = df_part
    st.session_state.prizes_df = df_prizes
    st.session_state.current_prize_index = 0
    st.session_state.drawn_count = 0
    st.session_state.current_winners = []
    update_sheet("", "", "", "", "")
    st.success("✅ 資料匯入成功並已重設舞台畫面")

if st.session_state.participants_df is not None and st.session_state.current_prize_index < len(st.session_state.prizes_df):
    current_prize = st.session_state.prizes_df.iloc[st.session_state.current_prize_index]
    prize_name = current_prize["獎項名稱"]
    prize_count = current_prize["名額"]

    st.header(f"🎁 現在抽的是：{prize_name}（共 {prize_count} 位）")

    if st.button("▶️ 顯示獎項（同步到舞台）"):
        update_sheet("prize", prize_name, "", "", "")

    if st.button("🎉 由抽獎者點擊這裡抽出下一位中獎者（可用第二滑鼠）"):
        available = st.session_state.participants_df[st.session_state.participants_df["狀態"].isin(["", "缺席"])]
        if len(available) == 0:
            st.warning("⚠️ 沒有可抽的參加者")
        else:
            winner = available.sample(1).iloc[0].to_dict()
            st.session_state.current_winners.append(winner)
            st.session_state.drawn_count += 1
            update_sheet("winner", prize_name, winner["姓名"], winner["職稱"], winner["社名"])

    for i, row in enumerate(st.session_state.current_winners):
        if row is not None:
            st.subheader(f"第 {i+1} 位：{row['姓名']} - {row['職稱']} - {row['社名']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ 到場 - {i}", key=f"ok_{i}"):
                    idx = st.session_state.participants_df.index[
                        (st.session_state.participants_df["姓名"] == row["姓名"]) &
                        (st.session_state.participants_df["職稱"] == row["職稱"])
                    ]
                    if not idx.empty:
                        st.session_state.participants_df.at[idx[0], "狀態"] = "中獎"
                        st.session_state.current_winners[i] = None
            with col2:
                if st.button(f"❌ 缺席 - {i}", key=f"no_{i}"):
                    idx = st.session_state.participants_df.index[
                        (st.session_state.participants_df["姓名"] == row["姓名"]) &
                        (st.session_state.participants_df["職稱"] == row["職稱"])
                    ]
                    if not idx.empty:
                        st.session_state.participants_df.at[idx[0], "狀態"] = "缺席"
                        st.session_state.current_winners[i] = None

    if st.button("➡️ 下一個獎項（主持人手動控制）"):
        st.session_state.current_prize_index += 1
        st.session_state.drawn_count = 0
        st.session_state.current_winners = []

        if st.session_state.current_prize_index < len(st.session_state.prizes_df):
            next_prize = st.session_state.prizes_df.iloc[st.session_state.current_prize_index]
            update_sheet("prize", next_prize["獎項名稱"], "", "", "")
        else:
            update_sheet("", "", "", "", "")

        st.rerun()

    excel_buffer = BytesIO()
    st.session_state.participants_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)

    st.download_button(
        "💾 下載更新後的名單",
        data=excel_buffer,
        file_name="更新後名單.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
