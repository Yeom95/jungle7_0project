import calendar
import json
import datetime
import jwt
from datetime import timedelta
from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider
from flask_jwt_extended import *
from bson import ObjectId
from werkzeug.security import check_password_hash

app = Flask(__name__)
from pymongo import MongoClient
#client = MongoClient('mongodb://test:test@localhost',27017)
client = MongoClient('localhost',27017)
db = client.dbjungle
collection = db['moneyPlan']


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

@app.route('/')
def home():

    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login():
    #로그인 기능 구현
    #모든 id,pw값 불러옴
    result = list(collection.find({}))

    print(request.form['id_send'])

    user_id = request.form['id_send']
    user_pw = request.form['pw_send']

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
        # 클라이언트로부터 JSON 데이터 받기
        userId_receive = request.form['userId_give']
        userPw_receive = request.form['userPw_give']
        userName_receive = request.form['userName_give']
        
        # MongoDB에 데이터 삽입
        data = {
            'userId': userId_receive,
            'userPw': userPw_receive,
            'userName': userName_receive
        }
            
        result = collection.insert_one(data)
        # 삽입 결과 응답
        response = {
            "message": "데이터가 성공적으로 삽입되었습니다.",
            "inserted_id": str(result.inserted_id)
        }
        return jsonify(response), 200
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
    today = datetime.today()

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
        userId_receive = request.form['userId_give']
        userName_receive = request.form['userName_give']
        date_receive = request.form['Date_give']
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
