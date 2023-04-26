#****************** import Libraries ***********************#
import pandas as pd
import requests
import jdatetime
import jalali_pandas
from persiantools import characters

#****************** Live Bourse Function ***********************#
def get_last_bourse_data():
    """
        get last data on bourse market
    """
    r = requests.get('http://www.tsetmc.com/tsev2/data/ClientTypeAll.aspx')
    Mkt_RI_df = pd.DataFrame(r.text.split(';'))
    Mkt_RI_df = Mkt_RI_df[0].str.split(",",expand=True)
    # assign names to columns:
    Mkt_RI_df.columns = ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
    # convert columns to numeric type:
    cols = ['No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
    Mkt_RI_df[cols] = Mkt_RI_df[cols].apply(pd.to_numeric, axis=1)
    Mkt_RI_df['WEB-ID'] = Mkt_RI_df['WEB-ID'].apply(lambda x: x.strip())
    Mkt_RI_df = Mkt_RI_df.set_index('WEB-ID')
    # re-arrange the order of columns:
    Mkt_RI_df = Mkt_RI_df[['No_Buy_R','No_Buy_I','No_Sell_R','No_Sell_I','Vol_Buy_R','Vol_Buy_I','Vol_Sell_R','Vol_Sell_I']]
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # GET MARKET WATCH PRICE AND OB DATA
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    r = requests.get('http://www.tsetmc.com/tsev2/data/MarketWatchPlus.aspx')
    main_text = r.text
    Mkt_df = pd.DataFrame((main_text.split('@')[2]).split(';'))
    Mkt_df = Mkt_df[0].str.split(",",expand=True)
    Mkt_df = Mkt_df.iloc[:,:23]
    Mkt_df.columns = ['WEB-ID','Ticker-Code','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                      'Low','High','Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Sector','Day_UL','Day_LL','Share-No','Mkt-ID']
    # re-arrange columns and drop some columns:
    Mkt_df = Mkt_df[['WEB-ID','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                      'Low','High','Y-Final','EPS','Base-Vol','Sector','Day_UL','Day_LL','Share-No','Mkt-ID']]
    # Just keep: 300 Bourse, 303 Fara-Bourse, 305 Sandoogh, 309 Payeh, 400 H-Bourse, 403 H-FaraBourse, 404 H-Payeh
    Mkt_ID_list = ['300','303','305','309','400','403','404']
    Mkt_df = Mkt_df[Mkt_df['Mkt-ID'].isin(Mkt_ID_list)]
    Mkt_df['Market'] = Mkt_df['Mkt-ID'].map({'300':'بورس','303':'فرابورس','305':'صندوق قابل معامله','309':'پایه','400':'حق تقدم بورس','403':'حق تقدم فرابورس','404':'حق تقدم پایه'})
    Mkt_df.drop(columns=['Mkt-ID'],inplace=True)   # we do not need Mkt-ID column anymore
    # assign sector names:
    r = requests.get('http://www.tsetmc.com/Loader.aspx?ParTree=111C1213')
    sectro_lookup = (pd.read_html(r.text)[0]).iloc[1:,:]
    # convert from Arabic to Farsi and remove half-space
    sectro_lookup[1] = sectro_lookup[1].apply(lambda x: (str(x).replace('ي','ی')).replace('ك','ک'))
    sectro_lookup[1] = sectro_lookup[1].apply(lambda x: x.replace('\u200c',' '))
    sectro_lookup[1] = sectro_lookup[1].apply(lambda x: x.strip())
    Mkt_df['Sector'] = Mkt_df['Sector'].map(dict(sectro_lookup[[0, 1]].values))
    # modify format of columns:
    cols = ['Open','Final','Close','No','Volume','Value','Low','High','Y-Final','EPS','Base-Vol','Day_UL','Day_LL','Share-No']
    Mkt_df[cols] = Mkt_df[cols].apply(pd.to_numeric, axis=1)
    Mkt_df['Time'] = Mkt_df['Time'].apply(lambda x: x[:-4]+':'+x[-4:-2]+':'+x[-2:])
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: (str(x).replace('ي','ی')).replace('ك','ک'))
    Mkt_df['Name'] = Mkt_df['Name'].apply(lambda x: (str(x).replace('ي','ی')).replace('ك','ک'))
    Mkt_df['Name'] = Mkt_df['Name'].apply(lambda x: x.replace('\u200c',' '))
    #calculate some new columns
    Mkt_df['Close(%)'] = round((Mkt_df['Close']-Mkt_df['Y-Final'])/Mkt_df['Y-Final']*100,2)
    Mkt_df['Final(%)'] = round((Mkt_df['Final']-Mkt_df['Y-Final'])/Mkt_df['Y-Final']*100,2)
    Mkt_df['Market Cap'] = round(Mkt_df['Share-No']*Mkt_df['Final'],2)
    # set index
    Mkt_df['WEB-ID'] = Mkt_df['WEB-ID'].apply(lambda x: x.strip())
    Mkt_df = Mkt_df.set_index('WEB-ID')
    #------------------------------------------------------------------------------------------------------------------------------------------
    # reading OB (order book) and cleaning the data
    OB_df = pd.DataFrame((main_text.split('@')[3]).split(';'))
    OB_df = OB_df[0].str.split(",",expand=True)
    OB_df.columns = ['WEB-ID','OB-Depth','Sell-No','Buy-No','Buy-Price','Sell-Price','Buy-Vol','Sell-Vol']
    OB_df = OB_df[['WEB-ID','OB-Depth','Sell-No','Sell-Vol','Sell-Price','Buy-Price','Buy-Vol','Buy-No']]
    # extract top row of order book = OB1
    OB1_df = (OB_df[OB_df['OB-Depth']=='1']).copy()         # just keep top row of OB
    OB1_df.drop(columns=['OB-Depth'],inplace=True)          # we do not need this column anymore
    # set WEB-ID as index for future joining operations:
    OB1_df['WEB-ID'] = OB1_df['WEB-ID'].apply(lambda x: x.strip())
    OB1_df = OB1_df.set_index('WEB-ID')
    # convert columns to numeric format:
    cols = ['Sell-No','Sell-Vol','Sell-Price','Buy-Price','Buy-Vol','Buy-No']
    OB1_df[cols] = OB1_df[cols].apply(pd.to_numeric, axis=1)
    # join OB1_df to Mkt_df
    Mkt_df = Mkt_df.join(OB1_df)
    # calculate buy/sell queue value
    bq_value = Mkt_df.apply(lambda x: int(x['Buy-Vol']*x['Buy-Price']) if(x['Buy-Price']==x['Day_UL']) else 0 ,axis = 1)
    sq_value = Mkt_df.apply(lambda x: int(x['Sell-Vol']*x['Sell-Price']) if(x['Sell-Price']==x['Day_LL']) else 0 ,axis = 1)
    Mkt_df = pd.concat([Mkt_df,pd.DataFrame(bq_value,columns=['BQ-Value']),pd.DataFrame(sq_value,columns=['SQ-Value'])],axis=1)
    # calculate buy/sell queue average per-capita:
    bq_pc_avg = Mkt_df.apply(lambda x: int(round(x['BQ-Value']/x['Buy-No'],0)) if((x['BQ-Value']!=0) and (x['Buy-No']!=0)) else 0 ,axis = 1)
    sq_pc_avg = Mkt_df.apply(lambda x: int(round(x['SQ-Value']/x['Sell-No'],0)) if((x['SQ-Value']!=0) and (x['Sell-No']!=0)) else 0 ,axis = 1)
    Mkt_df = pd.concat([Mkt_df,pd.DataFrame(bq_pc_avg,columns=['BQPC']),pd.DataFrame(sq_pc_avg,columns=['SQPC'])],axis=1)
    # just keep tickers with Value grater than zero! = traded stocks:
    #Mkt_df = Mkt_df[Mkt_df['Value']!=0]
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # JOIN DATA
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    final_df = Mkt_df.join(Mkt_RI_df)
    # add trade types:
    final_df['Trade Type'] = pd.DataFrame(final_df['Ticker'].apply(lambda x: 'تابلو' if((not x[-1].isdigit())or(x in ['انرژی1','انرژی2','انرژی3'])) 
                                                                   else ('بلوکی' if(x[-1]=='2') else ('عمده' if(x[-1]=='4') else ('جبرانی' if(x[-1]=='3') else 'تابلو')))))
    # add update Jalali date and time:
    jdatetime_download = jdatetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    final_df['Download'] = jdatetime_download
    # just keep necessary columns and re-arrange theor order:
    final_df = final_df[['Ticker','Trade Type','Time','Open','High','Low','Close','Final','Close(%)','Final(%)',
                         'Day_UL', 'Day_LL','Value','BQ-Value', 'SQ-Value', 'BQPC', 'SQPC',
                         'Volume','Vol_Buy_R', 'Vol_Buy_I', 'Vol_Sell_R', 'Vol_Sell_I','No','No_Buy_R', 'No_Buy_I', 'No_Sell_R', 'No_Sell_I',
                         'Name','Market','Sector','Share-No','Base-Vol','Market Cap','EPS','Download']]
    final_df = final_df.reset_index()
    final_df['Ticker'] = final_df['Ticker'].apply(lambda x : characters.ar_to_fa(''.join(x.split('\u200c')).strip()))
    # convert columns to int64 data type:
    """cols = ['Open','High','Low','Close','Final','Day_UL', 'Day_LL','Value', 'BQ-Value', 'SQ-Value', 'BQPC', 'SQPC',
            'Volume','Vol_Buy_R', 'Vol_Buy_I', 'Vol_Sell_R', 'Vol_Sell_I','No','No_Buy_R', 'No_Buy_I', 'No_Sell_R', 'No_Sell_I',
            'Share-No','Base-Vol','Market Cap']
    final_df[cols] = final_df[cols].astype('int64')"""
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # PROCESS ORDER BOOK DATA IF REQUESTED
    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    final_OB_df = ((Mkt_df[['Ticker','Day_LL','Day_UL']]).join(OB_df.set_index('WEB-ID')))
    # convert columns to numeric int64
    cols = ['Day_LL','Day_UL','OB-Depth','Sell-No','Sell-Vol','Sell-Price','Buy-Price','Buy-Vol','Buy-No']
    final_OB_df[cols] = final_OB_df[cols].astype('int64')
    # sort using tickers and order book depth:
    final_OB_df = final_OB_df.sort_values(['Ticker','OB-Depth'], ascending = (True, True))
    final_OB_df = final_OB_df.set_index(['Ticker','Day_LL','Day_UL','OB-Depth'])
    return final_df.drop('WEB-ID', axis=1)