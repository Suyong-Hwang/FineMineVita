from flask import Flask, session, url_for, render_template, flash, jsonify , request, redirect
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from models import DBManager
from functools import wraps
import requests
import json
import bcrypt

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

# 생년월일 계산으로 나이 구하기

def calculate_age(birthday_str):
    today = datetime.today()
    birth_date = datetime.strptime(birthday_str, "%Y-%m-%d")
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

## 비회원 회원가입 
# 비회원 회원가입 페이지
@app.route('/public/register', methods=["GET", "POST"])
def public_register():
    if request.method == "POST":
        user_name = request.form['username']
        user_id = request.form['userid']
        password = request.form['password']
        address= request.form['total_address']
        gender = request.form['gender']
        email = request.form['email']
        birthday = request.form['birthday']
        reg_number = request.form['total_regnumber']
        phone = request.form['phone']
        age = calculate_age(birthday)

        print(address)
        #회원 이메일과 중복여부
        if manager.duplicate_email(email):
            flash('이미 등록된 이메일 입니다.', 'error')
            return render_template('public/register.html')
        
        #회원 연락처 중복여부
        if manager.dupliceate_phone(phone):
            flash('이미 등록된 연락처 입니다', 'error')
            return render_template('public/register.html')
        
        #회원가입 신청 
        if manager.register_users(user_id, user_name, password, email, address, birthday, reg_number, gender, age, phone):
            flash('회원가입 신청이 완료되었습니다.', 'success')
            return redirect(url_for('index'))
        
        flash('회원가입에 실패했습니다.', 'error')
        return redirect(url_for('register'))
    return render_template('public/register.html')

# 비회원 회원가입 - 아이디 중복 확인
@app.route('/check_userid', methods=['POST'])
def check_userid():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '아이디가 입력되지 않았습니다.'}), 400

    if manager.duplicate_userid(user_id):
        return jsonify({'status': 'duplicate', 'message': '이미 사용 중인 아이디입니다.'})
    else:
        return jsonify({'status': 'ok', 'message': '사용 가능한 아이디입니다.'})


# 비회원 회원가입 - 약관 페이지
@app.route('/public/terms_of_service')
def terms_of_service():
    return render_template('public/terms_of_service.html')

# 비회원 회원가입 - 개인정보 처리방침 페이지
@app.route('/public/privacy_policy')
def privacy_policy():
    return render_template('public/privacy_policy.html')

### 로그인 기능
## 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('public_login', next=request.url))  # 로그인되지 않았다면 로그인 페이지로 리디렉션
        return f(*args, **kwargs)
    return decorated_function

## 관리자 권한 필수 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['role'] != 'admin':
            return "접근 권한이 없습니다", 403  # 관리자만 접근 가능
        return f(*args, **kwargs)
    return decorated_function



# 비회원 로그인 페이지
@app.route('/public/login', methods=["GET", "POST"])
def public_login():
    if request.method == "POST":
        userid = request.form['userid']
        password = request.form['password']
        result = manager.verify_user(userid)
        if result is None or result == False:
            flash("일치하는 아이디가 없습니다", 'error')
            return redirect(url_for('public_login'))
        
        if result:
                # 딕셔너리에서 'password'라는 키로 접근
                stored_hash = result['password']
                
                # 비밀번호 비교
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    user = manager.get_user_by_id(userid)
                    session['user_id'] = user['user_id']
                    session['user_name'] = user['user_name']
                    flash(f"{user['user_name']}님, 환영합니다!", 'success')
                    return redirect(url_for('user_dashboard'))
                else:
                    flash("비밀번호가 일치하지 않습니다.", 'error')
                    return redirect(url_for('public_login'))    
                
    return render_template('public/login.html')

#아이디/비밀번호찾기
@app.route('/index/search_account', methods=['GET', 'POST'])
def search_account():
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        userid = None  # 기본값 설정

        if search_type == "id":
            userid = manager.find_userid(username, email, phone)
            return render_template('public/search_account.html', userid=userid, search_type=search_type )

        elif search_type == "password":
            userid = request.form.get('userid')
            password_data = manager.find_user_password(userid, username, email, phone)
            password = None  # 기본값 설정

            if password_data: 
                hash_password = password_data['password']  # 딕셔너리에서 비밀번호 값 가져오기
                password = raw_password[:4] + '*' * (len(raw_password) - 4)  # 앞 4자리만 표시, 나머지는 '*'
            return render_template('public/search_account.html', password = password, userid=userid, search_type=search_type)
    return render_template('public/search_account.html')

#로그아웃 
@app.route('/logout')
def logout():
    session.clear()
    flash("로그아웃 되었습니다.", 'success')
    return redirect(url_for('index'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # 로그인된 사용자의 정보를 세션에서 가져옴
    return render_template('user/dashboard.html')

### 로그인 페이지
# 서비스 소개
@app.route('/user/about')
@login_required
def user_about():
    return render_template('user/about.html')

# 건강기능식품 목록
@app.route('/user/supplement_list', methods=["GET"])
@login_required
def user_supplement_list():
    search_type = request.args.get('search_type', '')
    search_query = request.args.get('search_query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    supplements, total_count = manager.get_supplements_by_page(page, per_page, search_type, search_query)
    total_pages = (total_count + per_page - 1) // per_page  # 올림 처리

    # 페이지네이션 범위 설정
    visible_page_count = 10  # 최대 10개까지 페이지 표시
    start_page = max(1, page - visible_page_count // 2)
    end_page = min(total_pages, start_page + visible_page_count - 1)

    if end_page - start_page < visible_page_count:
        start_page = max(1, end_page - visible_page_count + 1)

    return render_template('user/supplement_list.html', 
                            supplements=supplements,
                            page=page,
                            total_pages=total_pages,
                            start_page=start_page,
                            end_page=end_page,
                            search_type=search_type,
                            search_query=search_query)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5015, debug=True)