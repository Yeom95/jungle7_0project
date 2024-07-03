import calendar
import json
import datetime
import jwt
from datetime import timedelta
from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider
from flask_jwt_extended import *
from bson import ObjectId
from werkzeug.security import generate_password_hash,check_password_hash
from math import ceil

app = Flask(__name__)
from pymongo import MongoClient
#client = MongoClient('mongodb://test:test@localhost',27017)
client = MongoClient('localhost',27017)
db = client.dbjungle
collection = db['moneyPlan']

userID=''
week_cost=[{},{}]
total_cost=0
week_rank=0
today_rank=0



#userdata =sdfsdf

#토큰 생성에 사용될 key를 flask 환경 변수에 등록
app.config.update(
    DEBUG = True,
    JWT_SECTRET_KEY = "Secret Key"
)


#JWT 확장 모듈을 flask 어플리케이션에 등록
jwtModule = JWTManager(app)

SECRET_KEY = "SecretKey"

#유저별 주간,월간 금액합계 문제
#날짜,요일 계산
#수정 기능 사용 시 폼처리
#유저 데이터 형식

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)
class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)
    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)
app.json = CustomJSONProvider(app)

#연도와 몇월인지 받으면,날짜와 해당 달 이름 가져오는 함수
def get_month_days(year,month):
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year,month)
        month_name = calendar.month_name[month]
        return month_name,month_days

#해당 요일의 주차를 얻는 함수
def week_of_month(date):#datetime 타입
    first_day = date.replace(day=1)

    dom = date.day
    adjusted_dom = dom + first_day.weekday()

    return int(ceil(adjusted_dom/7.0))

def get_week_byStr(date):#string형
    20240703
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:8])

    dateTime = datetime.datetime(year,month,day)

    return dateTime



@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signUp')
def signUp():
    return render_template('signUp.html')

@app.route('/dailySpending')
def dailySpending():
    return render_template('dailySpending.html')

@app.route('/myPage')
def myPage():
    current_iso_week=datetime.datetime.now().isocalendar()[1]

    pipeline = [
    # userId가 일치하는 문서만 필터링
    {"$match": {"userId": userID}},
    # 저장된 날짜 문자열을 날짜 객체로 변환
    {"$addFields": {
        "convertedDate": {"$dateFromString": {"dateString": "$date", "format": "%Y%m%d"}}
    }},
    # 변환된 날짜의 ISO 주차를 계산
    {"$addFields": {
        "isoWeekConvertedDate": {"$isoWeek": "$convertedDate"}
    }},
    # ISO 주차가 현재 주차와 일치하는 문서만 필터링
    {"$match": {"isoWeekConvertedDate": current_iso_week}},
    # 요일별로 그룹화하여 cost를 합산하고 데이터를 정리
    {"$group": {
        "_id": {"$isoDayOfWeek": "$convertedDate"},
        "total_cost": {"$sum": "$cost"},
        "date_costs": {"$push": {"date": "$date", "cost": "$cost"}}
    }},
    # 요일 순으로 정렬 (ISO 요일: 1(월요일) ~ 7(일요일))
    {"$sort": {"_id": 1}},
    # 필요한 필드만 포함하도록 변환
    {"$project": {
        "_id": 0,
        "day_of_week": "$_id",
        "total_cost": 1,
        "date_costs": 1
    }}
]

# MongoDB 컬렉션 객체가 있다고 가정합니다
# `collection`을 실제 컬렉션 이름으로 교체하세요
    results = list(collection.aggregate(pipeline))

    return render_template('myPage.html',weekInfo = results)

@app.route('/rankingBoard')
def rankingBoard():

    current_date = datetime.datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")

    # 당일 랭크 조회 mongoDB 집계 파이프라인 
    pipeline = [
    # 저장된 날짜 문자열을 날짜 객체로 변환
    {"$addFields": {
        "convertedDate": {"$dateFromString": {"dateString": "$date", "format": "%Y%m%d"}}
    }},
    # 변환된 날짜와 현재 날짜에 대한 ISO 주를 계산
    {"$addFields": {
        "isoWeekConvertedDate": {"$isoWeek": "$convertedDate"},
        "isoWeekCurrentDate": {"$isoWeek": current_date}
    }},
    # ISO 주가 현재 ISO 주와 일치하는 문서를 찾기
    {"$match": {"$expr": {"$eq": ["$isoWeekConvertedDate", "$isoWeekCurrentDate"]}}},
    # userId로 문서를 그룹화하고 cost를 합산
    {"$group": {"_id": "$userId", "total_cost": {"$sum": {"$toInt": "$cost"}}}},
    # total_cost 기준으로 오름차순 정렬
    {"$sort": {"total_cost": 1}}
]

    # 주간 랭크 집계 실행
    weekRank = list(collection.aggregate(pipeline))

    # 당일 랭크 조회 mongoDB 집계 파이프라인 
    pipeline2 = [
    {"$match": {"date" : formatted_date}},  # date로 필터링
    {"$group": {"_id": "$userId", "total_cost": {"$sum": {"$toInt": "$cost"}}}},
    {"$sort": {"total_cost": 1}}  # total_cost를 오름차순으로 정렬
]
    
    dayrank = list(collection.aggregate(pipeline2))

    return render_template('rankingBoard.html',saveweekrank=weekRank,savedayrank=dayrank)


@app.route('/login',methods=['POST'])
def login():
    #로그인 기능 구현
    #모든 id,pw값 불러옴
    result = list(collection.find({}))

    print(request.form['id_send'])

    user_id = request.form['id_send']
    user_pw = request.form['pw_send']

    global userID
    userID = user_id

    for user in result:
        # 아이디와 비밀번호가 일치하는 경우
        if user_id == user['userId'] and check_password_hash(user['userPw'], user_pw):
            payload = {
                'id': user_id,
                'exp': datetime.datetime.now() + datetime.timedelta(hours=24)  # 로그인 24시간 유지
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return jsonify({'result': 'success', 'token': token})

    # 아이디 또는 비밀번호가 일치하지 않는 경우
    return jsonify({'result': '로그인 실패'})

    '''for user in result:
        #아이디,비밀번호가 일치하지 않는 경우
        if(user_id != user['userId'] or user_pw != user['userPw']):
            return jsonify(result = "로그인 실패")
        #아이디,비밀번호가 일치하는 경우
        #검증된 경우,access 토큰 반환
        else: 
            payload = {
			'id': user_id,
			'exp': datetime.datetime.now() + datetime.timedelta(seconds=60)  # 로그인 24시간 유지
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return jsonify({'result': 'success', 'token': token})           
            

    return 0'''

    

@app.route('/logout',methods=['GET'])
def logout():
    #로그아웃 기능 구현
    return 0

@app.route('/register',methods=['POST'])
def register():
    try:
        hashed_password = generate_password_hash(request.form['userPw_give'], method='pbkdf2')

        print(hashed_password)

        # 클라이언트로부터 JSON 데이터 받기
        userId_receive = request.form['userId_give']
        userPw_receive = hashed_password
        userName_receive = request.form['userName_give']
        category_receive = 0
        cost_receive = 0
        
        # MongoDB에 데이터 삽입
        data = {
            'userId': userId_receive,
            'userPw': userPw_receive,
            'userName': userName_receive,
            'category': category_receive,
            'cost' : cost_receive
        }
            
        result = collection.insert_one(data)
        # 삽입 결과 응답
        response = {
            "message": "데이터가 성공적으로 삽입되었습니다.",
            "inserted_id": str(result.inserted_id)
        }
        return jsonify({"result":'success'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/getUserRank',methods=['GET'])
def getUserRank():

    date = request.args.get('date')
    # 유저 아이디 입력
    userId_receive = request.form["userID_give"]
    # MongoDB 집계 파이프라인
    pipeline = [
        {"$match": {"date": date}},  # date로 필터링
        {"$group": {"_id": userId_receive, "total_cost": {"$sum": {"$toInt": "$cost"}}}},
        {"$sort": {"total_cost": 1}}  # total_cost를 오름차순으로 정렬
    ]

    # 집계 실행
    result = list(collection.aggregate(pipeline))

    # 결과를 JSON 형식으로 반환?
    return jsonify({'result': 'success', 'moneyRankList': result})

@app.route('/getAllRank',methods=['GET'])
def getAllRank():

    date = request.args.get('date')
    
    # MongoDB 집계 파이프라인
    pipeline = [
        {"$match": {"date": date}},  # date로 필터링
        {"$group": {"_id": "$userId", "total_cost": {"$sum": {"$toInt": "$cost"}}}},
        {"$sort": {"total_cost": 1}}  # total_cost를 오름차순으로 정렬
    ]

    # 집계 실행
    result = list(collection.aggregate(pipeline))
    # 결과를 JSON 형식으로 반환?
    return jsonify({'result': 'success', 'moneyRankList': result})

@app.route('/setMyCost')
def myCalendar():
    today = datetime.datetime.today()

    year = today.year
    month = today.month

    month_name,month_days = get_month_days(year,month)

    return render_template('MoneyRankEditMode.html',month_name=month_name, year=year, month_days=month_days)

@app.route('/get_calendar',methods = ['GET'])
def get_calendar():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))
    month_name,month_days = get_month_days(year,month)

    return jsonify({
        'month_name' : month_name,
        'month_days' : month_days,
        'year' : year
    })

@app.route('/addCost',methods=['POST'])
def addCost():
    #사용금액 등록 기능 구현
    try:
        # 클라이언트로부터 JSON 데이터 받기
        userId_receive = userID
        userName_receive = request.form['userName_give'] #id값으로 찾아서 저장하도록 수정
        date_receive = request.form['Date_give']#API에서 dailySpending에 전달받은 Date값을 기반으로 형식에 맞게 전달
        category_receive = request.form['Category_give']
        cost_receive = request.form['Cost_give']
        # 데이터 유효성 검사 (Id/Name/Date는 사용자가 입력하는게 아니기에 굳이 안해도되는가?)
        if not (userId_receive and userName_receive and date_receive and category_receive and cost_receive):
            return jsonify({"error": "필수 필드가 누락되었습니다."}), 400
        # MongoDB에 데이터 삽입
        data = {
            'userId': userId_receive,
            'userName': userName_receive,
            'date': date_receive,
            'category': category_receive,
            'cost': cost_receive
        }
        result = collection.insert_one(data)
        print(response["result"])
        # 삽입 결과 응답
        response = {
            "message": "데이터가 성공적으로 삽입되었습니다.",
            "inserted_id": str(result.inserted_id)
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/editCost',methods=['POST'])
def editCost():
    try:
        id = request.form['id']
        category = request.form['category']
        money = request.form['money']

        # MongoDB에서 해당 문서 업데이트
        result = db.moneyPlan.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"category": category, "money": money}}
        )

        if result.modified_count > 0:
            return jsonify({"result": "success", "message": "사용금액이 수정되었습니다."}), 200
        else:
            return jsonify({"result": "fail", "message": "해당 ID를 가진 문서가 없습니다."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/deleteCost',methods=['POST'])
def deleteCost():
    #사용금액 삭제 기능 구현
    id = request.form['id']
    db.moneyPlan.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'success'})

#5000으로 수정 필요
if __name__ == '__main__':
    app.run('0.0.0.0',port=5001,debug=True)
