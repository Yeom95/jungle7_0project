import calendar
from datetime import datetime
from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider
from flask_jwt_extended import *
from bson import ObjectId
app = Flask(__name__)

from pymongo import MongoClient
#client = MongoClient('mongodb://test:test@localhost',27017)
client = MongoClient('localhost',27017)
db = client.dbjungle

#토큰 생성에 사용될 key를 flask 환경 변수에 등록
app.config.update(
    DEBUG = True,
    JWT_SECTRET_KEY = "Secret Key"
)

#JWT 확장 모듈을 flask 어플리케이션에 등록
jwt = JWTManager(app)

#유저별 주간,월간 금액합계 문제
#날짜,요일 계산
#수정 기능 사용 시 폼처리
#유저 데이터 형식

#연도와 몇월인지 받으면,날짜와 해당 달 이름 가져오는 함수
def get_month_days(year,month):
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year,month)
        month_name = calendar.month_name[month]
        return month_name,month_days

@app.route('/')
def home():
    return render_template('MoneyRank.html')

@app.route('/login',methods=['GET'])
def login():
    return 0

@app.route('/logout',methods=['GET'])
def logout():
    #로그아웃 기능 구현
    return 0

@app.route('/register',methods=['POST'])
def register():
    #회원가입 기능 구현
    return 0

@app.route('/getAllRank',methods=['GET'])
def getAllRank():
    #유저별 금액합계 조회 및 정렬 기능 구현
    return 0

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
    return 0

@app.route('/editCost',methods=['POST'])
def editCost():
    #사용금액 수정 기능 구현
    return 0

@app.route('/deleteCost',methods=['POST'])
def deleteCost():
    #사용금액 삭제 기능 구현
    return 0

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)