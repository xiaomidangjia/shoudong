# 手动开仓提示
import pandas as pd
import json
import requests
import time
import numpy as np
import os
import re
from telegram import ParseMode
import datetime
from tqdm import tqdm
import importlib
import sys
import os
import urllib
import requests
import base64
import json
from datetime import datetime
import random
import hmac
import telegram
bot = telegram.Bot(token='6361430672:AAG2qr7zuFQkcQb13Xtud2q8KksonuTNVN4')
order_time = ['1960-01-01 00:00:00']
while True:
    time_str = str(datetime.utcnow())[11:16]
    time.sleep(2)
    if time_str in ('00:02','01:02','02:02','03:02','04:02','05:02','06:02','07:02','08:02','09:02','10:02','11:02','12:02',
                   '13:02','14:02','15:02','16:02','17:02','18:02','19:02','20:02','21:02','22:02','23:02'):
        # 引入永续合约流动性的概念
        print('开始运行',time_str)
        url_address = ['https://api.glassnode.com/v1/metrics/derivatives/futures_liquidated_volume_long_relative',
                       'https://api.glassnode.com/v1/metrics/market/price_usd_close',
                      'https://api.glassnode.com/v1/metrics/indicators/sopr_less_155']
        url_name = ['future','price','sopr']
        # insert your API key here
        API_KEY = '26BLocpWTcSU7sgqDdKzMHMpJDm'
        data_list = []
        for num in range(len(url_name)):
            print(num)
            addr = url_address[num]
            name = url_name[num]
            # make API request
            res_addr = requests.get(addr,params={'a': 'BTC','i':'1h', 'api_key': API_KEY})
            # convert to pandas dataframe
            ins = pd.read_json(res_addr.text, convert_dates=['t'])
            #ins.to_csv('test.csv')
            #print(ins['o'])
            #print(ins)
            ins['date'] =  ins['t']
            ins[url_name[num]] =  ins['v']
            ins = ins[['date',url_name[num]]]
            data_list.append(ins)
        result_data = data_list[0][['date']]
        for i in range(len(data_list)):
            df = data_list[i]
            result_data = result_data.merge(df,how='left',on='date')
        #last_data = result_data[(result_data.date>='2016-01-01') & (result_data.date<='2020-01-01')]
        futures_data = result_data[(result_data.date>='2023-10-01')]
        futures_data = futures_data.sort_values(by=['date'])
        futures_data = futures_data.reset_index(drop=True)
        new_futures_data = futures_data[['date','future','price','sopr']]
        sub_df = pd.DataFrame()
        for i in range(len(new_futures_data)-48,len(new_futures_data)+1):
            ins = new_futures_data[i-12:i]
            ins = ins.reset_index(drop=True)
            date = []
            future = []
            sopr = []
            logos = []
            for j in range(6,len(ins)+1):
                sub_ins = ins[j-6:j]
                sub_ins = sub_ins.reset_index(drop=True)
                #print(sub_ins)
                date.append(sub_ins['date'][5])
                sub_ins_1 = sub_ins[-3:].dropna()
                sub_ins_2 = sub_ins[-3:]
                #print(sub_ins_2)
                future.append(np.mean(sub_ins_1['future']))
                sopr.append(np.mean(sub_ins_2['sopr']))

                per_up = (sub_ins['price'][5] - np.min(sub_ins['price']))/np.min(sub_ins['price'])
                per_down = (sub_ins['price'][5] - np.max(sub_ins['price']))/np.max(sub_ins['price'])

                per_5 = 1 if sub_ins['price'][5] - sub_ins['price'][4] > 0 else 0
                per_4 = 1 if sub_ins['price'][4] - sub_ins['price'][3] > 0 else 0
                per_3 = 1 if sub_ins['price'][3] - sub_ins['price'][2] > 0 else 0
                per_2 = 1 if sub_ins['price'][2] - sub_ins['price'][1] > 0 else 0
                per_1 = 1 if sub_ins['price'][1] - sub_ins['price'][0] > 0 else 0

                per_last = (sub_ins['price'][5] - sub_ins['price'][4])/sub_ins['price'][4]
                if per_last > 0.02:
                    logo = 'duo_duo'
                elif per_last < -0.02:
                    logo = 'kong_kong'
                elif per_up == 0 and per_down < -0.03 and per_5 == 0:  #目前价格最低并且从最高点下跌了1%以上
                    logo = 'price_down_last'
                elif per_up == 0 and per_down < -0.01 and (per_5 + per_4 + per_3 + per_2 + per_1) == 0:  #目前价格最低并且从最高点下跌了1%以上
                    logo = 'price_down'
                elif per_up == 0 and per_down < -0.01 and per_5 == 0:
                    logo = 'price_down'
                elif per_up >= 0.03 and per_down ==0 and per_5 == 1:  #目前价格最高并且从最低点上升了1%以上
                    logo = 'price_up_last'
                elif per_up >= 0.01 and per_down ==0 and (per_5 + per_4 + per_3 + per_2 + per_1) == 5:  #目前价格最高并且从最低点上升了1%以上
                    logo = 'price_up'
                elif per_up >= 0.01 and per_down ==0 and per_5 == 1:
                    logo = 'price_up'
                else:
                    logo = 'other'
                logos.append(logo)
            df = pd.DataFrame({'date':date,'future':future,'sopr':sopr,'logos':logos})
            sub_df = pd.concat([sub_df,df])
        sub_df = sub_df.drop_duplicates()
        sub_df = sub_df.sort_values(by='date')
        sub_df = sub_df.reset_index(drop=True)
        new_df = new_futures_data[['date','price']].merge(sub_df,how='inner',on=['date'])
        sub_new_df = new_df[-3:]
        sub_new_df = sub_new_df.reset_index(drop=True)
        if sub_new_df['logos'][2] == ('price_up','price_up_last'):
            if sub_new_df['future'][2] < 0.45 and sub_new_df['future'][1] > 0.5:
                action = 'kong_info'
            elif sub_new_df['future'][2] < 0.45 and sub_new_df['future'][1] < 0.45 and sub_new_df['future'][0] < 0.45:
                action = 'kill_kong'
            else:
                action = 'other'
        elif sub_new_df['logos'][2] in ('price_down','price_down_last'):
            if sub_new_df['future'][2] > 0.5 and sub_new_df['future'][1] < 0.45:
                action = 'duo_info'
            elif sub_new_df['future'][2] > 0.5 and sub_new_df['future'][1] > 0.5 and sub_new_df['future'][0] > 0.5:
                action = 'kill_duo'
            else:
                action = 'other'
        elif sub_new_df['logos'][2] == 'duo_duo':
            if sub_new_df['future'][2] < 0.5:
                action = 'kill_kong'
            else:
                action = 'other'
        elif sub_new_df['logos'][2] == 'kong_kong':
            if sub_new_df['future'][2] > 0.5:
                action = 'kill_duo'
            else:
                action = 'other'
        else:
            action = 'other'
        end_time_str = str(datetime.utcnow())[0:19]
        start_time_str = str(sub_new_df['date'][2])
        # 将字符串转换为日期时间对象
        start_time= datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time= datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        # 计算时间差
        time_diff= end_time- start_time
        # 将时间差转换为分钟数
        minutes= time_diff.total_seconds() // 60
        print(action,minutes)
        if action in ('kong_info','kill_kong','duo_info','kill_duo') and minutes > 60 and minutes<70:
            # =========在此设置api-key，下单金额===========
            API_URL = 'https://api.bitget.com'
            API_SECRET_KEY = "c3dcf7ed5f80ec7b30a3af7e4dc847efe95be64d66570e667af82fc43192a250"
            API_KEY = "bg_e6fd3c23efbe7aa2a09dc8862275a812"
            PASSPHRASE = ""
            # ================================================================================================================================================
            def get_timestamp():
                return int(time.time() * 1000)
            def sign(message, secret_key):
                mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
                d = mac.digest()
                return base64.b64encode(d)
            def pre_hash(timestamp, method, request_path, body):
                return str(timestamp) + str.upper(method) + request_path + body
            def parse_params_to_str(params):
                url = '?'
                for key, value in params.items():
                    url = url + str(key) + '=' + str(value) + '&'
                return url[0:-1]
            def get_header(api_key, sign, timestamp, passphrase):
                header = dict()
                header['Content-Type'] = 'application/json'
                header['ACCESS-KEY'] = api_key
                header['ACCESS-SIGN'] = sign
                header['ACCESS-TIMESTAMP'] = str(timestamp)
                header['ACCESS-PASSPHRASE'] = passphrase
                # header[LOCALE] = 'zh-CN'
                return header

            w5 = 0 
            while w5 == 0:
                timestamp = get_timestamp()
                response = None
                request_path = "/api/mix/v1/market/ticker"
                url = API_URL + request_path
                params = {"symbol":"BTCUSDT_UMCBL"}
                request_path = request_path + parse_params_to_str(params)
                url = API_URL + request_path
                body = ""
                sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                response = requests.get(url, headers=header)
                ticker = json.loads(response.text)
                btc_price = float(ticker['data']['last'])
                if btc_price > 0:
                    w5 = 1
                else:
                    w5 = 0
            per = (btc_price - sub_new_df['price'][2])/sub_new_df['price'][2]
            print(btc_price,per)
            if action in ('kong_info') and per > -0.003:
                logo = str(datetime.utcnow())[0:19]
                last_order_time = order_time[-1]
                end_time1= datetime.strptime(str(datetime.utcnow())[0:19], '%Y-%m-%d %H:%M:%S')
                start_time1= datetime.strptime(last_order_time, '%Y-%m-%d %H:%M:%S')
                # 计算时间差
                time_diff1= end_time1- start_time1
                # 将时间差转换为分钟数
                minutes1= time_diff1.total_seconds() // 60
                if minutes1 < 140:
                    print('不下单')
                else:
                    kong_price = np.max([sub_new_df['price'][2] * 1.005,btc_price])
                    win_price = int(kong_price * 0.99)
                    loss_price = int(kong_price * 1.01)
                    test_data_3 = {
                        "crypto_time": str(end_time1),
                        "crypto_id": 'A' +str(timestamp),
                        "crypto_name": 'btc',
                        "crypto_direction":'kong',
                        "crypto_type":'dianwei',
                        "crypto_open":kong_price,
                        "crypto_win":win_price,
                        "crypto_loss":loss_price
                        }
                    req_url_3 = "http://8.219.61.64:5090/upload_date"
                    r_3 = requests.post(req_url_3, data=test_data_3)
                    api_res_3 = r_3.content.decode('utf-8')
                    api_res_3 = json.loads(api_res_3)
                    api_value_3 = api_res_3['value']
                    if sub_new_df['sopr'][2]>1.05:
                        xinxin = '80%'
                    elif sub_new_df['sopr'][2]>1.03:
                        xinxin = '70%'
                    else:
                        xinxin = '60%'
                    text = '【60分钟内有效】近3个小时BTC价格来到阶段性高点，目前全网大量空单布局，可以顺势做空。此单信心度：%s'%(xinxin)
                    content = ' \
【BTC小时短线单】 \n \
下单方向：BTC永续合约空单 \n \
下单价格建议：%s \n \
止盈价格建议：%s \n \
止损价格建议：%s \n \
下单理由：%s'%(int(kong_price),win_price,loss_price,text)
                    msg_url = 'https://www.coinglass.com/zh/pro/futures/LiquidationMap'
                    content_2 =  "<a href='%s'>点击链接查看清算地图</a>"%(msg_url)
                    bot.sendMessage(chat_id='-1001920263299', text=content,message_thread_id=3)
                    bot.sendMessage(chat_id='-1001920263299', text=content_2, parse_mode = ParseMode.HTML,message_thread_id=3)
                order_time.append(logo)
            elif action in ('kill_duo') and per > -0.003:
                logo = str(datetime.utcnow())[0:19]
                last_order_time = order_time[-1]
                end_time1= datetime.strptime(str(datetime.utcnow())[0:19], '%Y-%m-%d %H:%M:%S')
                start_time1= datetime.strptime(last_order_time, '%Y-%m-%d %H:%M:%S')
                # 计算时间差
                time_diff1= end_time1- start_time1
                # 将时间差转换为分钟数
                minutes1= time_diff1.total_seconds() // 60
                if minutes1 < 140:
                    print('不下单')
                else:
                    kong_price = np.max([sub_new_df['price'][2] * 1.005,btc_price])
                    win_price = int(kong_price * 0.99)
                    loss_price = int(kong_price * 1.01)
                    test_data_3 = {
                        "crypto_time": str(end_time1),
                        "crypto_id": 'A' +str(timestamp),
                        "crypto_name": 'btc',
                        "crypto_direction":'kong',
                        "crypto_type":'dianwei',
                        "crypto_open":kong_price,
                        "crypto_win":win_price,
                        "crypto_loss":loss_price
                        }
                    req_url_3 = "http://8.219.61.64:5090/upload_date"
                    r_3 = requests.post(req_url_3, data=test_data_3)
                    api_res_3 = r_3.content.decode('utf-8')
                    api_res_3 = json.loads(api_res_3)
                    api_value_3 = api_res_3['value']
                    if sub_new_df['sopr'][2]>1.02:
                        xinxin = '80%'
                    elif sub_new_df['sopr'][2]>1.01:
                        xinxin = '70%'
                    else:
                        xinxin = '60%'
                    text = '【60分钟内有效】目前BTC价格一直是下跌趋势，但全网多单越来越多，说明庄家有意在爆多单，可以顺庄做空。此单信心度：%s'%(xinxin)
                    content = ' \
【BTC小时短线单】 \n \
下单方向：BTC永续合约空单 \n \
下单价格建议：%s \n \
止盈价格建议：%s \n \
止损价格建议：%s \n \
下单理由：%s'%(int(kong_price),win_price,loss_price,text)
                    msg_url = 'https://www.coinglass.com/zh/pro/futures/LiquidationMap'
                    content_2 =  "<a href='%s'>点击链接查看清算地图</a>"%(msg_url)
                    bot.sendMessage(chat_id='-1001920263299', text=content,message_thread_id=3)
                    bot.sendMessage(chat_id='-1001920263299', text=content_2, parse_mode = ParseMode.HTML,message_thread_id=3)
                order_time.append(logo)
            elif action in ('duo_info') and per < 0.003:
                logo = str(datetime.utcnow())[0:19]
                last_order_time = order_time[-1]
                end_time1= datetime.strptime(str(datetime.utcnow())[0:19], '%Y-%m-%d %H:%M:%S')
                start_time1= datetime.strptime(last_order_time, '%Y-%m-%d %H:%M:%S')
                # 计算时间差
                time_diff1= end_time1- start_time1
                # 将时间差转换为分钟数
                minutes1= time_diff1.total_seconds() // 60
                if minutes1 < 140:
                    print('不下单')
                else:
                    duo_price = np.min([sub_new_df['price'][2] * 0.995,btc_price])
                    win_price = int(duo_price * 1.01)
                    loss_price = int(duo_price * 0.99)
                    test_data_3 = {
                        "crypto_time": str(end_time1),
                        "crypto_id": 'A' +str(timestamp),
                        "crypto_name": 'btc',
                        "crypto_direction":'duo',
                        "crypto_type":'dianwei',
                        "crypto_open":duo_price,
                        "crypto_win":win_price,
                        "crypto_loss":loss_price
                        }
                    req_url_3 = "http://8.219.61.64:5090/upload_date"
                    r_3 = requests.post(req_url_3, data=test_data_3)
                    api_res_3 = r_3.content.decode('utf-8')
                    api_res_3 = json.loads(api_res_3)
                    api_value_3 = api_res_3['value']
                    if sub_new_df['sopr'][2]<1:
                        xinxin = '80%'
                    elif sub_new_df['sopr'][2]>1 and sub_new_df['sopr'][2]<1.01 :
                        xinxin = '70%'
                    else:
                        xinxin = '60%'
                    text = '【60分钟内有效】近3个小时BTC价格来到阶段性低点，目前全网大量多单布局，可以顺势做多。此单信息心度：%s'%(xinxin)
                    content = ' \
【BTC小时短线单】 \n \
下单方向：BTC永续合约多单 \n \
下单价格建议：%s \n \
止盈价格建议：%s \n \
止损价格建议：%s \n \
下单理由：%s'%(int(duo_price),win_price,loss_price,text)
                    msg_url = 'https://www.coinglass.com/zh/pro/futures/LiquidationMap'
                    content_2 =  "<a href='%s'>点击链接查看清算地图</a>"%(msg_url)
                    bot.sendMessage(chat_id='-1001920263299', text=content,message_thread_id=3)
                    bot.sendMessage(chat_id='-1001920263299', text=content_2, parse_mode = ParseMode.HTML,message_thread_id=3)
                order_time.append(logo)
            elif action in ('kill_kong') and per < 0.003:
                logo = str(datetime.utcnow())[0:19]
                last_order_time = order_time[-1]
                end_time1= datetime.strptime(str(datetime.utcnow())[0:19], '%Y-%m-%d %H:%M:%S')
                start_time1= datetime.strptime(last_order_time, '%Y-%m-%d %H:%M:%S')
                # 计算时间差
                time_diff1= end_time1- start_time1
                # 将时间差转换为分钟数
                minutes1= time_diff1.total_seconds() // 60
                if minutes1 < 140:
                    print('不下单')
                else:
                    duo_price = np.min([sub_new_df['price'][2] * 0.995,btc_price])
                    win_price = int(duo_price * 1.01)
                    loss_price = int(duo_price * 0.99)
                    test_data_3 = {
                        "crypto_time": str(end_time1),
                        "crypto_id": 'A' +str(timestamp),
                        "crypto_name": 'btc',
                        "crypto_direction":'duo',
                        "crypto_type":'dianwei',
                        "crypto_open":duo_price,
                        "crypto_win":win_price,
                        "crypto_loss":loss_price
                        }
                    req_url_3 = "http://8.219.61.64:5090/upload_date"
                    r_3 = requests.post(req_url_3, data=test_data_3)
                    api_res_3 = r_3.content.decode('utf-8')
                    api_res_3 = json.loads(api_res_3)
                    api_value_3 = api_res_3['value']
                    if sub_new_df['sopr'][2]>1:
                        xinxin = '80%'
                    elif sub_new_df['sopr'][2]<1 and sub_new_df['sopr'][2]>0.99 :
                        xinxin = '70%'
                    else:
                        xinxin = '60%'
                    text = '【60分钟内有效】目前BTC价格一直是上涨趋势，但全网空单越来越多，说明庄家有意在爆空单，可以顺庄做多。此单信息心度：%s'%(xinxin)
                    content = ' \
【BTC小时短线单】 \n \
下单方向：BTC永续合约多单 \n \
下单价格建议：%s \n \
止盈价格建议：%s \n \
止损价格建议：%s \n \
下单理由：%s'%(int(duo_price),win_price,loss_price,text)
                    msg_url = 'https://www.coinglass.com/zh/pro/futures/LiquidationMap'
                    content_2 =  "<a href='%s'>点击链接查看清算地图</a>"%(msg_url)
                    bot.sendMessage(chat_id='-1001920263299', text=content,message_thread_id=3)
                    bot.sendMessage(chat_id='-1001920263299', text=content_2, parse_mode = ParseMode.HTML,message_thread_id=3)
                order_time.append(logo)
        else:
            c = 1
        time.sleep(100)
    else:
        continue