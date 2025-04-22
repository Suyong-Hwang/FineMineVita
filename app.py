from flask import Flask, session, url_for, render_template, flash, send_from_directory, jsonify ,request, redirect
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from models import DBManager
import requests
import json

app = Flask(__name__)

app.secret_key = 'your-secret-key'

# 파일 업로드 경로 설정
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
# 업로드 폴더가 없으면 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

manager = DBManager()

@app.context_processor
def inject_full_date():
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    today_date = datetime.now()
    today = today_date.strftime("%Y년 %m월 %d일")
    weekday = weekdays[today_date.weekday()]
    full_date = f"{today} ({weekday})"
    return {"full_date": full_date}


## 건건강기능식품 기능성 원료인정현황 테이블 생성
# manager.create_approved_functional_ingredients()

# #건강기능식품 기능성 원료인정현황 오픈API데이터 url
# api_url = "http://openapi.foodsafetykorea.go.kr/api/API키/I-0040/json/1/691"

# #건강기능식품 기능성 원료인정현황 오픈API 데이터 저장
# manager.approved_functional_ingredients(api_url)

# 건강기능식품 품목 제조 신고사항 현황 테이블 생성
# manager.create_supplement_products_table()
# # 건강기능식품 품목제조 신고사항 현황 오픈API데이터 url
# api_url = "http://openapi.foodsafetykorea.go.kr/api/API키/I0030/json"

# manager.save_supplement_products(api_url, start=1, end=40801, batch_size=1000)


# 건강기능식품 기능성 원료인정현황 오픈API 데이터 저장

## 비회원 홈페이지
# 비회원 홈페이지
@app.route('/')
def index():
    return render_template('public/index.html')

# 비회원 소개페이지
@app.route('/public/about')
def public_about():
    return render_template('public/about.html')

# 비회원 문의하기 페이지
@app.route('/public/inquiry', methods=["GET", "POST"])
def public_inquiry():
    if request.method == "POST":
        email = request.form.get('email')
        reason = request.form.get('inquiry_reason')
        detail = request.form.get('reason-detail')
        file = request.files.get('file')

        file_path = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

       
        manager.insert_inquiry(email, reason, detail, file_path)

        flash("문의가 성공적으로 접수되었습니다.", "success")
        return redirect(url_for('index'))

    return render_template('public/inquiry.html')

# 비회원 로그인 페이지
@app.route('/public/login', methods=["GET", "POST"])
def public_login():
    if request.method == "POST":
       pass

    return render_template('public/login.html')

# 비회원 회원가입 페이지
@app.route('/public/register', methods=["GET", "POST"])
def public_register():
    if request.method == "POST":
        user_name = request.form['username']
        user_id = request.form['userid']
        password = request.form['password']
        address= request.form['address']
        gender = request.form['gender']
        email = request.form['email']
        birthday = request.form['birthday']
        reg_number = request.form['total_regnumber']
        
        #회원과 아이디가 중복되는지 확인
        if manager.duplicate_users(user_id):
            flash('이미 존재하는 아이디 입니다.', 'error')
            return render_template('public/register.html')
        
        #회원 이메일과 중복여부
        if manager.duplicate_email(email):
            flash('이미 등록된 이메일 입니다.', 'error')
            return render_template('public/register.html')
        
        #회원가입 신청 
        if manager.register_users(user_id, user_name, password, email, address, birthday, reg_number, gender):
            flash('회원가입 신청이 완료되었습니다.', 'success')
            return redirect(url_for('index'))
        
        flash('회원가입에 실패했습니다.', 'error')
        return redirect(url_for('register'))
    return render_template('public/register.html')

# 비회원 회원가입 - 약관 페이지
@app.route('/public/terms_of_service')
def terms_of_service():
    return render_template('public/terms_of_service.html')

# 비회원 회원가입 - 개인정보 처리방침 페이지
@app.route('/public/privacy_policy')
def privacy_policy():
    return render_template('public/privacy_policy.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5015, debug=True, use_reloader=False)