# 시간 측정 시작
import time
start = time.time()

# 라이브러리
import pandas as pd
kospi = pd.read_csv('../data/KOSPI.csv')

# KOSPI에 상장된 종목 코드
kospi['종목코드'] = kospi['종목코드'].apply(lambda x : str(x).rjust(6, '0'))
code_list = kospi['종목코드'].unique()

# 라이브러리
import numpy as np

# 진행과정 Check
check = 0

# 결과 저장 데이터프레임
result_df = pd.DataFrame()

# 코드 별 진행
for code in code_list : 

    # Hyper Parameter
    tr_name = 'TR_SCHART'
    term = 'D'
    start_date = '20180510'   # 학습 시작점
    end_date = '20200229'     # 학습 종료점
    Lookup = '9999' 
    
    # url
    url = 'http://ssecd.roboadvisor.co.kr:9999/' + tr_name + '?0=' + code + '&1=' + term + '&2=1' +\
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
    data = data.set_index('date')
    
    # 필요한 변수만 추출
    data = data[['open', 'high', 'low', 'close', 'volume', 'volume_price']]

    # 만약에 데이터가 비어있다면 그 종목은 PASS
    if data["open"][0] == '' : 
        continue
    
    # 변수 속성 정수로 바꾸기
    for column in data.columns : 
        data[column] = data[column].apply(lambda x : int(x))
        
    # 거래량과 거래가격을 모두 로그 변환
    data['volume'] = data['volume'].apply(lambda x : np.log(x+1))
    data['volume_price'] = data['volume_price'].apply(lambda x : np.log(x+1))
    
    # 각각의 피쳐들에 대해 
    for column in ['open', 'high', 'low', 'close', 'volume', 'volume_price'] : 
        for i in range(1,5,1) : 
            data['{}_shift_{}'.format(column,i)] = data[column].shift(i)
    
    # 타겟 생성 : 다음날의 고가를 예측
    data['y'] = data['high'].shift(-1)
    
    # NaN이 들어가 있는 행 제거
    data = data.dropna()
    
    # Input과 Target을 분리
    X = data[data.columns[:-1]]
    y = data['y']
    
    # Linear Regression
    from sklearn.linear_model import LinearRegression
    reg = LinearRegression(fit_intercept=True, 
                           normalize=False,
                           copy_X=True,
                           n_jobs=-1).fit(X, y)
    
    # Test Data 생성하기
    start_date, end_date = '20200301', '20200330'
    url = 'http://ssecd.roboadvisor.co.kr:9999/' + tr_name + '?0=' + code + '&1=' + term + '&2=1' +\
          '&3=' + start_date + '&4=' + end_date + '&5=' + Lookup
    url_page = urlopen(url)
    url_data = json.loads(url_page.read())
    data = pd.DataFrame(url_data)
    data.columns = ['date','time','open','high','low','close','price_ccr','volume_ccr',
                    'rock','volume','volume_price']
    data = data[['date', 'time', 'open', 'high', 'low', 'close', 'volume', 'volume_price']]
    data = data[::-1]
    data = data.set_index('date')
    data = data[['open', 'high', 'low', 'close', 'volume', 'volume_price']]
    for column in data.columns : 
        data[column] = data[column].apply(lambda x : int(x))
    data['volume'] = data['volume'].apply(lambda x : np.log(x+1))
    data['volume_price'] = data['volume_price'].apply(lambda x : np.log(x+1))
    for column in ['open', 'high', 'low', 'close', 'volume', 'volume_price'] : 
        for i in range(1,5,1) : 
            data['{}_shift_{}'.format(column,i)] = data[column].shift(i)
    data['y'] = data['high'].shift(-1)
        
    data = data[-1:]
    
    data = data[data.columns[:-1]]

    # 필요한것들
    result = dict({'종목' : code,
                   '어제 날짜' : data.index.values[0],
                   '어제 종가' : int(data['close'].values),
                   '오늘 고가' : int(round(reg.predict(data)[0])),
                   '오늘 고가 변동폭 예측' : 100*(int(round(reg.predict(data)[0]))-int(data['close'].values))/\
                                     int(data['close'].values)})
    result_df = result_df.append(result, ignore_index=True)
    
    # 각 종목별 결과 출력
    if check % 100 == 0 : 
        print('{:4} / {:4} 종목 ====> {:7.2f}% 완료  {:.4f}'.format(check+1,2144,100*check/2144,time.time()-start))
    check += 1

# 전체 완료
print('{:4} / {:4} 종목 ====> {:7.2f}% 완료  {:.4f}'.format(check + 1,2144,100*check/2144,time.time()-start))

# 시간측정 완료
print("\n\nall time :", time.time() - start)

# 종목 TOP 20
result_df = result_df[['어제 날짜', '종목', '어제 종가', '오늘 고가', '오늘 고가 변동폭 예측']]
result_df['오늘 고가 변동폭 예측'] = result_df['오늘 고가 변동폭 예측'].apply(lambda x : round(x,2))
result_df = result_df.sort_values(by='오늘 고가 변동폭 예측', ascending=False).set_index('종목')
result_df = result_df[result_df['오늘 고가 변동폭 예측'] < 30.00]
print(result_df[:20])