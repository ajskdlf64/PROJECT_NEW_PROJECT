# 오늘날짜
date = '20200331' 

# 시뮬레이션 할 종목 코드
code = '307930'

# 경고 무시
import warnings
warnings.filterwarnings(action='ignore') 

# Hyper Parameter
tr_name = 'TR_SCHART'
term = '1'
start_date = date
end_date = date
Lookup = '9999' 
        
# url
url = 'http://ssecd.roboadvisor.co.kr:9999/' + tr_name + '?0=' + code + '&1=' + term + '&2=5' +\
      '&3=' + start_date + '&4=' + end_date + '&5=' + Lookup

# url open
from urllib.request import urlopen
url_page = urlopen(url)

# json 파일로 받아오기
import json
url_data = json.loads(url_page.read())

# json을 데이터프레임으로 바꾸기
import pandas as pd
data = pd.DataFrame(url_data)
    
# Data Column명 변경
data.columns = ['date','time','open','high','low','close','price_ccr','volume_ccr',
                'rock','volume','volume_price']
data = data[['date', 'time', 'open', 'high', 'low', 'close', 'volume', 'volume_price']]
    
# 순서 뒤집기
data = data[::-1]
data['date_time'] = data['date'] + '_' + data['time']
data = data.set_index('date_time')
    
# 필요한 변수만 추출
data = data[['open', 'high', 'low', 'close', 'volume']]

# 변수 속성 정수로 바꾸기
for column in data.columns : 
    data[column] = data[column].apply(lambda x : int(x))

# 진행상태 표시
data['state'] = ''

# Simulation
simulation_df = pd.DataFrame()

# 시작 네이밍
print()
print('{:^50}'. format('======================== 프로그램 매매 시뮬레이션 ======================='))

# 표시
print('\n')

for idx in data.index : 
        
    # 시가에 매수
    if idx == date + '_0905' : 
        temp = data.loc[idx]
        temp['state'] = '매수'
        simulation_df = simulation_df.append(temp)
        print('시가에 매수')
        continue
            
    # 목표가격 설정
    if idx[-4:-2] == '09' : 
        goal_rate = 1.07
    elif idx[-4:-2] == '10' : 
        goal_rate = 1.06
    elif idx[-4:-2] == '11' : 
        goal_rate = 1.05
    elif idx[-4:-2] == '12' : 
        goal_rate = 1.04
    else : 
        goal_rate = 1.03

    # 목표 가격 도달시 매도
    if data.loc[idx]['high'] > goal_rate * simulation_df.loc[date + '_0905']['open'] : 
        temp = data.loc[idx]
        temp['state'] = '매도'
        simulation_df = simulation_df.append(temp)
        print('목표가격에 도달하여 종가로 매도')
        break
        
    # 매입가 대비 10:00 까지는 -5%, 그 이후부터는 -3% 이상 손해가 난 경우 손절
    if idx[-4:-2] == '09' : 
        minus_rate = 0.95
    else : 
        minus_rate = 0.97
    temp = data.loc[idx]
    if temp['close'] < minus_rate * simulation_df.loc[date + '_0905']['open'] :
        temp['state'] = '매도'
        simulation_df = simulation_df.append(temp)
        print("매입가 대비 3% 이상 손해가 나서 일괄 매도")
        break
    
    # 이전 check 단계 대비 종가가 2% 이상 하락 현상이 나타난 경우
    if int(data.loc[idx]['close']) <= 0.98 * int(simulation_df[-1:][['close']].values[0][0]) : 
        temp = data.loc[idx]
        temp['state'] = '매도'
        simulation_df = simulation_df.append(temp)
        print("직전 time point 대비 종가가 2% 하락하여 일괄 매도")
        break
    
    # 15:00의 종가가 매입가와 오차범위(-0.5 ~ 0.5%) 이내일 때
    if idx == date + '_1500' : 
        temp = data.loc[idx]
        if temp['high'] - simulation_df.loc[date + '_0905']['open'] <\
                                          0.005 * simulation_df.loc[date + '_0905']['open']  :
            temp['state'] = '매도'
            simulation_df = simulation_df.append(temp)
            print("15:00 까지 매입가 대비 움직임이 없어서 일괄 매도")
            break
        else : 
            temp['state'] = '보유'
            simulation_df = simulation_df.append(temp)
    
    # 15:20 종가로 일괄 매도
    if idx == date + '_1520' : 
        temp = data.loc[idx]
        temp['state'] = '매도'
        simulation_df = simulation_df.append(temp)
        print('15:20 도달하여 종가로 일괄 매도 --->')
        break
    
    # 손절 요건이 충족되지 않을 경우 계속 보유
    temp = data.loc[idx]
    temp['state'] = '보유'
    simulation_df = simulation_df.append(temp)
    
# 시뮬레이션 종료
print('시뮬레이션 종료!')
    
# 피쳐 순서
simulation_df = simulation_df[['open', 'high', 'low', 'close', 'volume', 'state']]

# 표시
print('\n')

# 시뮬레이션 결과
print(simulation_df)

# 표시
print('\n')

# 수익률
buy = simulation_df.loc[date + '_0905']['open']
cell = int(simulation_df[-1:]['high'])
rate = (100 * (cell - buy)) / buy
print('종목 코드 : {},   매수가 : {},   매도가 : {},   수익률 : {:.2f}%' .format(code, buy, cell, rate))

print('\n')

print('{:^50}' .format('='*76), end='\n\n')