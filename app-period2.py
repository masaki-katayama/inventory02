#!/usr/bin/env python
# coding: utf-8

# In[41]:


import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt
import streamlit as st
import inventorize as inv
from PIL import Image
import math


# In[34]:


image1 = Image.open('logigeek-logo-short.png')
st.set_page_config(
    page_title="INV_Simulation02|LogiGeek", 
    page_icon=image1,
    layout="wide")

image2 = Image.open('logigeek-logo-long.png')
st.image(image2, caption='ロジスティクスをDXするための小ネタ集')
st.link_button(":blue[ロジギークへリンク]", 
               "https://rikei-logistics.com/",
                use_container_width = True)

st.header('定期発注方式のシミュレーションアプリ')
st.subheader('～輸送コスト（発注コスト）可変～')
st.text('')
st.subheader('このアプリでできること')
st.text('１．定期発注を行った場合の在庫推移／欠品率／トータル物流コスト等をシミュレーションします。')
st.text('２．リードタイムや輸送／保管コスト等を設定できるため、輸送モードの違いによるトータル物流コストをシミュレーションできます。')
st.text('３．輸送コストは固定費と変動費に分けて設定できます。')
st.text('４．需要データはcsvファイルでアップロードできます。')

st.text('詳細な使い方については下記サイトをご覧下さい↓')
st.link_button(":blue[物量が少ない時FCLとLCLのどっちが安い？アプリでトータル物流コストをシミュレーション|ロジギーク]", 
               "https://rikei-logistics.com/app-periodic2")
st.text('')


# In[35]:


st.sidebar.header('◆条件設定画面◆')
st.sidebar.subheader('１．需要データの読み込み')
uploaded_file = st.sidebar.file_uploader('csvファイルをアップロードして下さい。',type='csv')

if uploaded_file:
    raw_df = pd.read_csv(uploaded_file)
else:
    raw_df = pd.read_csv('default_data.csv')

st.sidebar.subheader('２．訓練データと検証データの比率')
split_rate = st.sidebar.number_input(label = '検証データ（％）', 
                                     value = 70, label_visibility="visible", 
                                     min_value=0, max_value=100)

st.sidebar.subheader('３．発注関連パラメータ')
ld = st.sidebar.number_input(label = '納品リードタイム（日）', 
                                     value = 3, label_visibility="visible", 
                                     min_value=0, max_value=180)
oc = st.sidebar.number_input(label = '発注サイクル（日）', 
                                     value = 7, label_visibility="visible", 
                                     min_value=0, max_value=180)
so = st.sidebar.number_input(label = '許容欠品率（％）', 
                                     value = 5, label_visibility="visible", 
                                     min_value=0, max_value=100)

st.sidebar.subheader('４．物流コスト')
st.sidebar.markdown('''#### １）輸送コスト''')
fixed_cost = st.sidebar.number_input(label = '固定単価（円／発注）', 
                                     value = 40000, label_visibility="visible", 
                                     min_value=0, max_value=1000000)
prop_cost = st.sidebar.number_input(label = '比例単価（円／個）', 
                                     value = 10, label_visibility="visible", 
                                     min_value=0, max_value=1000000)
step_cost = st.sidebar.number_input(label = 'ステップ単価（円／ステップ）', 
                                     value = 30000, label_visibility="visible",                             
                                     min_value=0, max_value=1000000)
step_qty = st.sidebar.number_input(label = 'ステップ区切り（個／ステップ）', 
                                     value = 4000, label_visibility="visible",                             
                                     min_value=0, max_value=1000000)
st.sidebar.markdown('''#### ２）保管コスト''')
inventory_cost = st.sidebar.number_input(label = '比例単価（円／個･日）', 
                                     value = 3, label_visibility="visible", 
                                     min_value=0, max_value=1000)
st.sidebar.markdown('''#### ３）欠品コスト''')
shortage_cost = st.sidebar.number_input(label = '比例単価（円／個）', 
                                     value = 1000, label_visibility="visible", 
                                     min_value=0, max_value=100000)
st.subheader('需要データ')
st.write('データ数　：', f'{len(raw_df)}個')
st.dataframe(raw_df)

raw_df = np.array(raw_df)

x = range(1, len(raw_df)+1)
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111)
ax.plot(x, raw_df)
ax.set_xlabel('Days', weight ='bold', size = 14, color ='black')
ax.set_ylabel('Demand', weight ='bold', size = 14, color ='black')
st.pyplot(fig)

learn_df, test_df = train_test_split(raw_df, test_size=split_rate/100, shuffle=False)
    
av = learn_df.mean()
sd = learn_df.std(ddof = 1)
    
result = inv.Periodic_review_normal(
    test_df,
    av,
    sd,
    ld,
    1-so/100,
    oc,
    shortage_cost = shortage_cost,
    inventory_cost = inventory_cost,
    ordering_cost = 0
)



st.text('')
st.subheader('シミュレーション結果（在庫推移）', divider='blue')
show_df = result[0].rename(columns={'period': '日', 'demand': '需要', 'sales': '出荷', 'inventory_level': '庫内在庫',
                                   'inventory_position': 'トータル在庫', 'order': '発注', 'max': '補充目標', 'recieved': '入庫',
                                    'lost_order': '欠品'})

show_df['輸送コスト'] = 0
for i in range(show_df.shape[0]):
    if show_df.iloc[i, 5] != 0:
        show_df.iloc[i, 9] = fixed_cost + prop_cost * show_df.iloc[i, 5] + step_cost * math.ceil(show_df.iloc[i, 5] / step_qty)

st.dataframe(show_df)

sf_stock = int(result[1]['saftey_stock'])
max_stock = int(result[0].iloc[1,6])
av_stock = int(result[1]['average_inventory_level'])
ts_cost = show_df['輸送コスト'].sum()
st_cost = int(result[1]['inventory_cost'])
so_cost = int(result[1]['shortage_cost'])
fill_rate = result[1]['Item_fill_rate'] * 100
service_rate = result[1]['cycle_service_level'] * 100

sf_stock_c = f'{sf_stock:,}個'
max_stock_c = f'{max_stock:,}個'
av_stock_c = f'{av_stock:,}個'
ts_cost_c = f'{ts_cost:,}円'
st_cost_c = f'{st_cost:,}円'
so_cost_c = f'{so_cost:,}円'
fill_rate_c = f'{fill_rate:.1f}％'
service_rate_c = f'{service_rate:.1f}％'

st.write('安全在庫 ： ', sf_stock_c)
st.write('在庫補充目標 ： ', max_stock_c)
st.write('平均在庫 ： ', av_stock_c)
st.write('サービス率 ： ', service_rate_c)
st.write('充足率 ： ', fill_rate_c)

st.text('')
st.subheader(':mag: 庫内在庫推移')
x = range(1, len(test_df)+2)
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111)
ax.plot(x, result[0]['inventory_level'])
ax.set_xlabel('Days', weight ='bold', size = 14, color ='black')
ax.set_ylabel('Stock', weight ='bold', size = 14, color ='black')
st.pyplot(fig)

st.text('')
st.subheader('シミュレーション結果（物流コスト）', divider='blue')
st.write('トータル輸送コスト ： ', ts_cost_c)
st.write('トータル保管コスト ： ', st_cost_c)
st.write('トータル欠品コスト ： ', so_cost_c)
st.write('トータルロジスティクスコスト ： ', f'{ts_cost + st_cost + so_cost:,}円')

