from flask import Flask,render_template,jsonify,request
from flask.json.provider import JSONProvider
from bson import ObjectId
app = Flask(__name__)

from pymongo import MongoClient
#client = MongoClient('mongodb://test:test@localhost',27017)
client = MongoClient('localhost',27017)
db = client.dbjungle

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

@app.route('/getAllRank',methods=['GET'])
def getAllRank():
    #유저별 금액합계 조회 및 정렬 기능 구현
    return 0

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