import streamlit as st
import pandas as pd
import random
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

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

def update_sheet(stage, prize="", name="", title="", team=""):
    sheet = connect_sheet()
    ws = sheet.sheet1
    ws.update("A2", [[stage, prize, name, title, team]])

# 初始化
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

st.title("🎯 同步版抽獎控制端")

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
    st.success("✅ 資料匯入成功")

if st.session_state.participants_df is not None and st.session_state.current_prize_index < len(st.session_state.prizes_df):
    current_prize = st.session_state.prizes_df.iloc[st.session_state.current_prize_index]
    prize_name = current_prize["獎項名稱"]
    prize_count = current_prize["名額"]

    st.header(f"🎁 現在抽的是：{prize_name}（共 {prize_count} 位）")

    if st.button("▶️ 顯示獎項（同步到舞台）"):
        update_sheet("prize", prize_name, "", "", "")

    if st.button("🎉 抽出下一位中獎者"):
        available = st.session_state.participants_df[st.session_state.participants_df["狀態"].isin(["", "缺席"])]
        if len(available) == 0:
            st.warning("⚠️ 沒有可抽的參加者")
        else:
            winner = available.sample(1).iloc[0]
            st.session_state.current_winners.append(winner)
            st.session_state.drawn_count += 1
            update_sheet("winner", prize_name, winner["姓名"], winner["職稱"], winner["社名"])

    for i, row in enumerate(st.session_state.current_winners):
        st.subheader(f"第 {i+1} 位：{row['姓名']} - {row['職稱']} - {row['社名']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ 到場 - {i}", key=f"ok_{i}"):
                st.session_state.participants_df.loc[
                    (st.session_state.participants_df["姓名"] == row["姓名"]) &
                    (st.session_state.participants_df["職稱"] == row["職稱"]),
                    "狀態"
                ] = "中獎"
                st.session_state.current_winners[i] = None
        with col2:
            if st.button(f"❌ 缺席 - {i}", key=f"no_{i}"):
                st.session_state.participants_df.loc[
                    (st.session_state.participants_df["姓名"] == row["姓名"]) &
                    (st.session_state.participants_df["職稱"] == row["職稱"]),
                    "狀態"
                ] = "缺席"
                st.session_state.current_winners[i] = None

    st.session_state.current_winners = [x for x in st.session_state.current_winners if x is not None]

    if st.session_state.drawn_count >= prize_count and not st.session_state.current_winners:
        if st.button("➡️ 下一個獎項"):
            st.session_state.current_prize_index += 1
            st.session_state.drawn_count = 0

    excel_buffer = BytesIO()
    st.session_state.participants_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)

    st.download_button(
        "💾 下載更新後的名單",
        data=excel_buffer,
        file_name="更新後名單.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
