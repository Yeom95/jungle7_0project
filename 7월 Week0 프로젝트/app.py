import calendar
from datetime import datetime
import json
from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider
from bson import ObjectId
app = Flask(__name__)

from pymongo import MongoClient
#client = MongoClient('mongodb://test:test@localhost',27017)
client = MongoClient('localhost',27017)
db = client.dbjungle
collection = db['moneyPlan']

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


#유저별 주간,월간 금액합계 문제
#날짜,요일 계산
#수정 기능 사용 시 폼처리
#유저 데이터 형식

@app.route('/')
def home():
    return render_template('MoneyRank.html')

@app.route('/login',methods=['GET'])
def login():
    #로그인 기능 구현
    return 0

@app.route('/logout',methods=['GET'])
def logout():
    #로그아웃 기능 구현
    return 0

@app.route('/register',methods=['POST'])
def register():
    #회원가입 기능 구현
    return 0

@app.route('/getUserRank',methods=['GET'])
def getAllRank():

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
    month = today.month + 1

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year,month)

    month_name = calendar.month_name[month]
    print(month_name)

    return render_template('MoneyRankEditMode.html',month_name=month_name, year=year, month_days=month_days)
    



# 데이터 삽입을 처리하는 API 엔드포인트
@app.route('/addCost', methods=['POST'])
def addCost():
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
