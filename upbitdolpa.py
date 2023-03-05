#-*-coding:utf-8 -*
import myUpbit   #우리가 만든 함수들이 들어있는 모듈
import time
import datetime
import pyupbit

import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키  

import json

'''
변동성 돌파 전략 단타 변형!

크론탭에 1분마다 동작하게 등록합니다. 

*투자 로직*
1.0 - 변동성 돌파 + 변동성 조절 + 노이즈 K + 이평선 상승장
      트레일링 스탑 1% 적용
1.1 - 변동성 돌파 + 노이즈 K + 180일봉 볼린저 밴드 상승돌파
      익절선을 넘을 경우 추가 매수(불타기)
      하루가 지나도 수익율이 0% 초과인 경우 유지
1.2 - 변동성 돌파 + 노이즈 K + 상승장 and 180일봉 볼린저 밴드 상승돌파
      슈퍼트렌드 매도타이밍 캐치하면 바로 매도
      비트코인이 상승장일때만 거래시도
      
'''

#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)


#내가 매수할 총 코인 개수
MaxCoinCnt = 10.0

#내가 가진 잔고 데이터를 다 가져온다.
balances = upbit.get_balances()

#TotalMoney = myUpbit.GetTotalMoney(balances) #총 원금

#내 남은 원화(현금))을 구한다.
TotalWon = float(upbit.get_balance("KRW"))

print("-----------------------------------------------")
print ("TotalWon:", TotalWon)
# print ("CoinMoney:", CoinMoney)



#빈 리스트를 선언합니다.
DolPaCoinList = list()

#파일 경로입니다.
dolpha_type_file_path = "/var/autobot/UpbitDolPaCoin.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(dolpha_type_file_path, 'r') as json_file:
        DolPaCoinList = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")




##############################################################
#빈 딕셔너리를 선언합니다!
DolPaRevenueDict = dict()

#파일 경로입니다.
revenue_type_file_path = "/var/autobot/UpbitDolPaRevenue.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(revenue_type_file_path, 'r') as json_file:
        DolPaRevenueDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

##############################################################

# 수익율을 기록으로 남겨봅시다
DolPaDailyLogDict = dict()

#파일 경로입니다.
dailylog_type_file_path = "/var/autobot/UpbitDolPaDailylog.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(dailylog_type_file_path, 'r') as json_file:
        DolPaDailyLogDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

##############################################################
#수익율 0.5%를 트레일링 스탑 기준으로 잡는다. 즉 고점 대비 0.5% 하락하면 매도 처리 한다!
#이 수치는 코인에 따라 한 틱만 움직여도 손절 처리 될 수 있으니 
#1.0 이나 1.5 등 다양하게 변경해서 테스트 해보세요!
stop_revenue = 5.0
##############################################################



#시간 정보를 가져옵니다. 아침 9시의 경우 서버에서는 hour변수가 0이 됩니다.
time_info = time.gmtime()
year = time_info.tm_year
month = time_info.tm_mon
day = time_info.tm_mday
hour = time_info.tm_hour
min = time_info.tm_min
print("오늘은",year,"년",month,"월",day,"일 입니다.")
print("GMT 기준 :", hour,"시", min,"분")

# 코인시장은 24시간 돌아가기 때문에 구매당시 시각을 기록하고 24시간 지나면 매각하도록 합시다.
time_now = datetime.datetime.now()
timestamp = time_now.timestamp()

# 상승장에만 투자할 수 있도록 비트코인을 기준으로 마켓타이밍을 잡는다
BTC_now = pyupbit.get_current_price("KRW-BTC")
df_btc = pyupbit.get_ohlcv("KRW-BTC",interval="minute60")
BTC_Supertrend = myUpbit.GetSupertrend(df_btc,30,5)

btc_ma3 = float(myUpbit.GetMA(df_btc,3,-1))
btc_ma5 = float(myUpbit.GetMA(df_btc,5,-1))
btc_ma10 = float(myUpbit.GetMA(df_btc,10,-1))
btc_ma20 = float(myUpbit.GetMA(df_btc,20,-1))

BTC_all_up = BTC_now > btc_ma3 and BTC_now > btc_ma5 and BTC_now > btc_ma10 and BTC_now > btc_ma20
BTC_3hours = (df_btc[-1:]['open'] < df_btc[-1:]['close']).all() and (df_btc[-2:-1]['open'] < df_btc[-2:-1]['close']).all() and (df_btc[-3:-2]['open'] < df_btc[-3:-2]['close']).all()

print('==================================================')
print('지금 4개 이평선을 넘었나요? :', BTC_all_up)
print('3시간 연속 상승세인가요? :', BTC_3hours)
print('==================================================')


#베스트봇 과정 진행하면서 탑코인 리스트 만들때 아래 같은 경로에 저장하게 만들었기에
#일단 그대로 사용합니다. https://blog.naver.com/zacra/222670663136
#아래의 경로로 저장하게 되면 실제로는 /home/ec2-user/UpbitTopCoinList.json 이 경로에 파일이 저장되게 됩니다.
top_file_path = "./UpbitTopCoinList.json"

TopCoinList = list()

#파일을 읽어서 리스트를 만듭니다.

if BTC_all_up and BTC_3hours == True:
    try:
        with open(top_file_path, "r") as json_file:
            TopCoinList = json.load(json_file)

    except Exception as e:
        TopCoinList = myUpbit.GetTopCoinList("day",20)
        print("Exception by First")

# 매일 로그를 남기기 위한 사전 작업을 합시다.

today = datetime.date.today().strftime("%Y-%m-%d")
if hour == 0 and min == 0:
    try:
        DolPaDailyLogDict[today] = ({'매수한 코인 개수': 0.0, '매수한 티커': [], '오늘의 수익률':0.0})

        with open(dailylog_type_file_path, 'w') as json_file:
            json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)

    except Exception as e:
        #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
        print("Exception by First")

#거래대금 탑 코인 리스트를 1위부터 내려가며 매수 대상을 찾는다.
#전체 원화 마켓의 코인이 아니라 탑 순위 TopCoinList 안에 있는 코인만 체크해서 매수한다는 걸 알아두세요!

# 비트코인이 상승장일때에만 거래를 한다.
if BTC_all_up and BTC_3hours == True:

    print('야호! 상승장이다! 매수 가즈아!')

    for ticker in TopCoinList:
        try: 
            print("Coin Ticker: ",ticker)

            #변동성 돌파리스트에 없다. 즉 아직 변동성 돌파 전략에 의해 매수되지 않았다.
            if myUpbit.CheckCoinInList(DolPaCoinList,ticker) == False:
                
                time.sleep(0.05)
                df = pyupbit.get_ohlcv(ticker,interval="day") #일봉 데이타를 가져온다.
                
                #코인당 매수할 매수금액을 재지정 한다.
                #여기서 마켓타이밍을 기준으로 투자금을 조절한다.
                ma3 = float(myUpbit.GetMA(df,3,-2))
                ma5 = float(myUpbit.GetMA(df,5,-2))
                ma10 = float(myUpbit.GetMA(df,10,-2))
                ma20 = float(myUpbit.GetMA(df,20,-2))

                j = 0

                for i in [ma3,ma5,ma10,ma20]:
                    if i == True:
                        j = j + 1
                ma_score = (j / 4)

                CoinMoney = (TotalWon / MaxCoinCnt) * ma_score

                #그리고 자금관리를 통해 한 번더 안전하게 투자금을 조절한다.
                money_ctrl = (((float(df['high'][-2]) - float(df['low'][-2]))) / float(df['close'][-2])) * 100
                
                #최종 투자금액은 다음과 같다.
                f_cm = CoinMoney * round((3 / money_ctrl),0)
                #여기서 K/자금관리 값의 K는 투자를 공격적으로 할건지를 결정한다
                #1은 소극적, 2는 보통, 3은 공격적 투자이다

                # 다만 투자금이 5천원 미만일 경우 투자 및 손절이 불가하므로 강제로 6000원으로 만들어 준다!
                if f_cm < 6000:
                    f_cm = 6000

                print('최종 투자금 :',f_cm)

                #유동적인 K값을 구하기 위해 평균 노이즈 비율을 이용하자
                noise = 1 - ((abs(df.close - df.open))/(df.high - df.low))
                #20일 평균 노이즈 비율을 구해서 K값으로 이용한다.
                noise_20 = noise.tail(20).mean()
                print('현재 노이즈 값은? :',round(noise_20,2))

                #어제의 고가와 저가의 변동폭에 0.5를 곱해서
                #오늘의 시가와 더해주면 목표 가격이 나온다!
                target_price = float(df['open'][-1]) + (float(df['high'][-2]) - float(df['low'][-2])) * round(noise_20,2)
                
                ######################################################################

                

                ######################################################################

                #과도한 변동성에 투자를 막기 위한 변동성 조절도 필요하다.
                change_per = (df.high.shift(1) - df.low.shift(1)) / (df.open) * 100
                change_f = change_per.tail(5).mean()
            
                #현재가
                now_price = float(df['close'][-1])

                #5일 이동평균선
                # df_15 = pyupbit.get_ohlcv(ticker,interval="minute15") #15분봉 데이타를 가져온다.
                ma5 = float(myUpbit.GetMA(df,5,-2))

                # 볼린저 밴드(180일봉) 돌파를 이용해 큰추세로 상승세인지 알아본다
                BBdolpa = myUpbit.BBUSignal(df,180,-1)

                print('==================================================')    
                print('현재가 :',now_price , "타겟가 :", target_price,'변동성 :', round(change_f,1), '5일이평선 :', ma5)
                print('==================================================')
                print('현재가가 타겟가보다 높은가? :',now_price > target_price)
                # print('변동성이 10 미만인가? :',change_f <= 10)
                print('==================================================')
                print('5일 이평선 보다 현재가가 높은가? :',now_price > ma5)
                print('볼린저 180일봉 상단선을 상향돌파했는가? :',BBdolpa == True)
                print('')

                #이를 돌파했다면 변동성 돌파 성공!! 코인을 매수하고 지정가 익절을 걸고 파일에 해당 코인을 저장한다!
                #그 전에 상승장인지(각 화폐의 가격이 5일 이동평균보다 높은지) 여부 파악하여 낮으면 거래하지 않고 높으면 거래한다.
                
                if now_price > target_price and now_price > ma5 and len(DolPaCoinList) < MaxCoinCnt or now_price > target_price and len(DolPaCoinList) < MaxCoinCnt and BBdolpa == True: #and Supertrend == True:
                    # and now_price > ma5 and change_f <= 10 change_f < 5 and change_f <= 5 and myUpbit.GetHasCoinCnt(balances) < MaxCoinCnt: 

                    #보유하고 있지 않은 코인 (매수되지 않은 코인)일 경우만 매수한다!
                    if myUpbit.IsHasCoin(balances, ticker) == False:

                        print("!!!!!!!!!!!!!!!DolPa GoGoGo!!!!!!!!!!!!!!!!!!!!!!!!")
                        #시장가 매수를 한다.
                        balances = myUpbit.BuyCoinMarket(upbit,ticker,f_cm)
                
                        #매수된 코인을 DolPaCoinList 리스트에 넣고 이를 파일로 저장해둔다!
                        DolPaCoinList.append(ticker)
                    
                        #파일에 리스트를 저장합니다
                        with open(dolpha_type_file_path, 'w') as outfile:
                            json.dump(DolPaCoinList, outfile)

                        ##############################################################
                        #매수와 동시에 초기 수익율과 구매당시 시간을 넣는다. (당연히 수익율은 0일테니 0을 넣고)
                        DolPaRevenueDict[ticker] = [0,timestamp]
                        
                        #파일에 딕셔너리를 저장합니다
                        with open(revenue_type_file_path, 'w') as outfile:
                            json.dump(DolPaRevenueDict, outfile)
                    
                    ##############################################################
                    # 매수된 코인 개수와 티커를 기록합시다.
                    buy_count = myUpbit.GetHasCoinCnt(balances)
                    today_profit = DolPaDailyLogDict.get(today, {}).get('오늘의 수익률', 0.0)

                    DolPaDailyLogDict[today] = ({'매수한 코인 개수': buy_count, '매수한 티커': ticker, '오늘의 수익률':today_profit})

                    with open(dailylog_type_file_path, 'w', encoding='utf-8') as json_file:
                        json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)
                    ##############################################################

        except Exception as e:
            print("---:", e)

else:
    # 매수된 코인 개수와 티커를 기록합시다.
    today_cnt = DolPaDailyLogDict.get(today, {}).get('매수한 코인 개수')
    today_ticker = DolPaDailyLogDict.get(today, {}).get('매수한 티커')
    today_profit = DolPaDailyLogDict.get(today, {}).get('오늘의 수익률')

    DolPaDailyLogDict[today] = ({'매수한 코인 개수': today_cnt, '매수한 티커': today_ticker, '오늘의 수익률':today_profit})

    with open(dailylog_type_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)

    print('######################')
    print('오늘은 날이 좋지 않군...')
    print('######################')
    print('')





#모든 원화마켓의 코인을 순회하여 체크한다!
# 이렇게 두번에 걸쳐서 for문을 도는 이유는
# 매수된 코인이 거래대금 탑순위에 (TopCoinList) 빠져서 아예 체크되지 않은 걸 방지하고자
# 매수 후 체크하는 로직은 전체 코인 대상으로 체크하고
# 매수 할때는 TopCoinList안의 코인만 체크해서 매수 합니다.

Tickers = pyupbit.get_tickers("KRW")


for ticker in Tickers:
    try: 
        print("Coin Ticker: ",ticker)

        #변동성 돌파로 매수된 코인이다!!! (실제로 매도가 되서 잔고가 없어도 파일에 쓰여있다면 참이니깐 이 안의 로직을 타게 됨)
        if myUpbit.CheckCoinInList(DolPaCoinList,ticker) == True:


            #구매 당시 시간 기준 24시간이 지났다면 (아직 익절이나 손절이 안된 경우)
            if (timestamp - DolPaRevenueDict[ticker][1]) > 86400 :
                
                # 수익율을 먼저 계산합니다.
                revenue_rate = myUpbit.GetRevenueRate(balances,ticker)

                 # 만일 수익이 나고 있지 않다면
                if revenue_rate <= stop_revenue:

                    #리스트에서 코인을 빼 버리고
                    DolPaCoinList.remove(ticker)

                    #시장가로 모두 매도!
                    balances = myUpbit.SellCoinMarket(upbit,ticker,upbit.get_balance(ticker))

                    # 매도 당시 수익율을 구해 로그에 저장합니다.
                    today_profit = DolPaDailyLogDict.get(today, {}).get('오늘의 수익률', 0.0)
                    new_profit = today_profit + revenue_rate

                    DolPaDailyLogDict[today] = {'오늘의 수익률': new_profit}

                    with open(dailylog_type_file_path, 'w', encoding='utf-8') as json_file:
                        json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)

                    #파일에 리스트를 저장합니다
                    with open(dolpha_type_file_path, 'w') as outfile:
                        json.dump(DolPaCoinList, outfile)
            


            #영상에 빠져 있지만 이렇게 매수된 상태의 코인인지 체크하고 난뒤 진행합니다~!
            if myUpbit.IsHasCoin(balances, ticker) == True:

                #수익율과 슈퍼트렌드를 구한다.
                #여기서 슈퍼트렌드는 민감도를 올리기 위해 1분봉으로 한다.
                df_1m = pyupbit.get_ohlcv(ticker,interval="minute1")
                revenue_rate = myUpbit.GetRevenueRate(balances,ticker)
                Supertrend = myUpbit.GetSupertrend(df_1m,30,5)

                ##############################################################
                #방금 구한 수익율이 파일에 저장된 수익율보다 높다면
                if revenue_rate > DolPaRevenueDict[ticker][0] :

                    #먼저 딕셔너리에 값을 넣어주고
                    DolPaRevenueDict[ticker][0] = revenue_rate
                    
                    # 수익률이 매번 정해진 숫자의 배수를 넘길때마다 추가매수!
                    
                    if DolPaRevenueDict[ticker][0] > stop_revenue:
                        
                        i += 1
                        balances = myUpbit.BuyCoinMarket(upbit, ticker, f_cm)
                        stop_revenue = stop_revenue * i

                    else:
                        i = 1
                    
                    #파일에 딕셔너리를 저장합니다
                    with open(revenue_type_file_path, 'w') as outfile:
                        json.dump(DolPaRevenueDict, outfile)

                #그게 아닌데 
                else:
                    #수익율을 구한다.
                    revenue_rate = myUpbit.GetRevenueRate(balances,ticker)

                    # 고점 수익율 - 스탑 수익율 >= 현재 수익율... 즉 고점 대비 정해진 값보다 떨어진 상황이라면 트레일링 스탑!!! 모두 매도한다!
                    if (DolPaRevenueDict[ticker][0] - stop_revenue) >= revenue_rate :
                        #시장가로 모두 매도!
                        balances = myUpbit.SellCoinMarket(upbit,ticker,upbit.get_balance(ticker))
                        
                        # 수익율을 기록하고 저장합니다
                        today_profit = DolPaDailyLogDict.get(today, {}).get('오늘의 수익률', 0.0)
                        new_profit = today_profit + revenue_rate

                        DolPaDailyLogDict[today] = {'오늘의 수익률':new_profit}

                        with open(dailylog_type_file_path, 'w', encoding='utf-8') as json_file:
                            json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)
                    
                    # 슈퍼트렌드에서 매도신호가 떴다면 모두 매도!
                    elif Supertrend == False :
                        
                        #시장가로 모두 매도!
                        balances = myUpbit.SellCoinMarket(upbit,ticker,upbit.get_balance(ticker))
                        
                        # 수익율을 기록하고 저장합니다
                        today_profit = DolPaDailyLogDict.get(today, {}).get('오늘의 수익률', 0.0)
                        new_profit = today_profit + revenue_rate

                        DolPaDailyLogDict[today] = {'오늘의 수익률':new_profit}

                        with open(dailylog_type_file_path, 'w', encoding='utf-8') as json_file:
                            json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)

                    # 볼린저 밴드를 상향 돌파후 다시 내려 않으면
                    # elif BBdolpa == False:
                    #     #시장가로 모두 매도!
                    #     balances = myUpbit.SellCoinMarket(upbit,ticker,upbit.get_balance(ticker))

                    #     # 수익율을 기록하고 저장합니다
                    #     DolPaDailyLogDict[today][ticker]['수익율'] = revenue_rate

                    #     with open(dailylog_type_file_path, 'w') as outfile:
                    #         json.dump(DolPaDailyLogDict, outfile)

                    # 만일 실시간 수익율이 50% 이상 넘어갈 경우
                    elif revenue_rate > 50:
                        #시장가로 모두 매도!
                        balances = myUpbit.SellCoinMarket(upbit,ticker,upbit.get_balance(ticker))

                        # 수익율을 기록하고 저장합니다
                        today_profit = DolPaDailyLogDict.get(today, {}).get('오늘의 수익률', 0.0)
                        new_profit = today_profit + revenue_rate

                        DolPaDailyLogDict[today] = {'오늘의 수익률':new_profit}

                        with open(dailylog_type_file_path, 'w', encoding='utf-8') as json_file:
                            json.dump(DolPaDailyLogDict, json_file, ensure_ascii=False, indent=4)
                ##############################################################

    except Exception as e:
        print("---:", e)



