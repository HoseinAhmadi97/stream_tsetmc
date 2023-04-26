import time  # to simulate a real time data, time loop
from get_price import *
import numpy as np  # np mean, np random
import pandas as pd  # read csv, df manipulation
import matplotlib.pyplot as plt
import plotly.express as px  # interactive charts
import streamlit as st  # 🎈 data web app development
import yfinance as yf
import numpy as np

st.set_page_config(
    page_title="Tehran Securities Exchange Technology Management Co",
    page_icon="✅",
    layout="wide",
)

# ------------ some functions for preparing data ---------------- #
def add_column(data):
    ##add values column
    data['Val_Buy_R'] = data['Vol_Buy_R'] * data['Final']/10**10
    data['Val_Sell_R'] = data['Vol_Sell_R'] * data['Final']/10**10
    data['Val_Buy_I'] = data['Vol_Buy_I'] * data['Final']/10**10
    data['Val_Sell_I'] = data['Vol_Sell_I'] * data['Final']/10**10
    
    
    #add power columns
    data['Power_Buy_R'] = data['Val_Buy_R'] / data['No_Buy_R']
    data['Power_Sell_R'] = data['Val_Sell_R'] / data['No_Sell_R']
    data['Balance_R'] = (data['Val_Buy_R'] - data['Val_Sell_R']) - (data['Val_Buy_I'] - data['Val_Sell_I'])
    
    return data

def get_fix_stock_etfs(x):
    types = ['صندوق سهامی', 'صندوق درآمد ثابت', 'سایر صندوق‌ها']
    if '-س' in x:
        return types[0]
    elif 'سهام' in x:
        return types[0]
    elif 'شاخص' in x:
        return types[0]
    elif '-د' in x:
        return types[1]
    elif 'ثابت' in x:
        return types[1]
    elif 'پایدار' in x:
        return types[1]
    else:
        return types[2]

def get_last_bourse_filtred_data():
    data = get_last_bourse_data()
    filtered_data = data[data['Trade Type'] == 'تابلو']
    add_filtred_data = add_column(filtered_data)
    select = add_filtred_data[add_filtred_data['Sector'] == 'صندوق سرمایه گذاری قابل معامله']
    add_filtred_data.loc[select.index, 'Sector'] = select['Name'].apply(get_fix_stock_etfs)
    return add_filtred_data

# ------------ get data ---------------- #
def get_data():
    main_data = get_last_bourse_filtred_data()
    data = main_data[main_data['Sector'] != ('صندوق درآمد ثابت')]
    data = data[data['Sector'] != ('سایر صندوق‌ها')]
    return data

# ------------ finctions for plotting ---------------- #
def get_time():
    time = jdatetime.datetime.now()
    time = str(time.year) + '-' + str(time.month) + '-'  + str(time.day) + ', ' + str(time.hour) + ':' + str(time.minute)
    return time

def plot_buy_sell_RI(data):
    df = pd.DataFrame((data[['Val_Buy_R', 'Val_Buy_I', 'Val_Sell_R', 'Val_Sell_I']].sum()/(data['Value'].sum()/10**12)), columns=['% of buy'])
    #colors
    colors = ['green','orange','red','orange']
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.pie(df['% of buy'].iloc[:2], colors = colors[:2], labels=df.index[:2], autopct='%1.1f%%', startangle=90)
    ax2.pie(df['% of buy'].iloc[2:], colors = colors[2:], labels=df.index[2:], autopct='%1.1f%%', startangle=90)
    #draw circle
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax1.axis('equal') 
    ax2.axis('equal')  
    plt.tight_layout()
    return fig
    
# ------------ Dashboard ---------------- #
# dashboard title
st.title("Tehran Securities Exchange Technology Management Co")

# creating a single-element container
placeholder = st.empty()

for seconds in range(200):
    
    try:
        main_data = get_last_bourse_filtred_data()
    except:
        continue
    data = main_data[main_data['Sector'] != ('صندوق درآمد ثابت')]
    data = data[data['Sector'] != ('سایر صندوق‌ها')]

    # creating KPIs
    R_Power_Buy = round(data['Val_Buy_R'].sum() / data['No_Buy_R'].sum()* 1000)
    R_Power_Sell = float(data['Val_Sell_R'].sum() / data['No_Sell_R'].sum()* 1000)
    Money_Entrance = float(data['Balance_R'].sum())
    Retail_Value = float(data['Value'].sum()/10**13)
    P_Final_Stock_Number = len(data[data['Final(%)']>0])/len(data)
    P_Close_Stock_Number = len(data[data['Close(%)']>0])/len(data)

    with placeholder.container():
        st.markdown("**last update: {}**".format(get_time()))

        # create three columns
        R_Power_Buy_, R_Power_Sell_, Money_Entrance_,Retail_Value_,P_Final_Stock_Number_,P_Close_Stock_Number_ = st.columns(6)

        # fill in those three columns with respective metrics or KPIs
        R_Power_Buy_.metric(
            label="R_Power_Buy",
            value=(R_Power_Buy),
            #delta=df.iloc[-1]['Close'] - df.iloc[0]['Close'],
        )
        
        R_Power_Sell_.metric(
            label="R_Power_Sell",
            value=round(R_Power_Sell),
        )
        
        Money_Entrance_.metric(
            label="Money_Entrance",
            value=round(Money_Entrance),
        )
        Retail_Value_.metric(
            label="Retail_Value",
            value=round(Retail_Value, 2),
        )
        
        P_Final_Stock_Number_.metric(
            label="P_Final_Stock_Number",
            value=round(P_Final_Stock_Number, 2),
        )
        
        P_Close_Stock_Number_.metric(
            label="P_Close_Stock_Number",
            value=round(P_Close_Stock_Number, 2),
        )

        # create two columns for charts
        fig_col1, fig_col2 = st.columns(2)
        with fig_col1:
            st.markdown("### buy_sell_RI")
            fig = plot_buy_sell_RI(data)
            st.write(fig)
            
        with fig_col2:
            st.markdown("### Money-Entrance")
            fig2 = px.bar(main_data.groupby('Sector')[['Balance_R']].sum().sort_values('Balance_R', ascending = False))
            st.write(fig2)
            
        fig_col3 = st.columns(1)
        with fig_col1:
            st.markdown("#### Return By Sector")
            fig = px.bar(
                        main_data.groupby('Sector')[['Market Cap']]
                        .sum()
                        .sort_values('Market Cap', ascending = False)
                        .merge(
                            main_data.groupby('Sector')[['Close(%)']].mean().sort_values('Close(%)', ascending = False),
                            on = ['Sector'])
                        .rename({'Close(%)': 'Mean Close(%)'}, axis=1),
                        y = 'Mean Close(%)',
                        barmode='group'
                        )
            st.write(fig)

        #st.markdown("### Detailed Data View")
        #st.dataframe(df)
        time.sleep(10)