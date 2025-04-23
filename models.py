import mysql.connector 
from datetime import datetime
from flask import jsonify
import json
import requests
import re
import bcrypt # 비밀번호 해싱을 위한 라이브러리

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    ## 데이터베이스 연결
    def connect(self): 
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.4",
                user = "suyong",
                password="1234",
                database="FMV",
                charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True)
        
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패 : {error}")
    
    ## 데이터베이스 연결해제
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    ## 건강기능식품 제품목록 테이블 생성
    def create_supplement_products_table(self):
        try:
            self.connect()

            sql = """
            CREATE TABLE IF NOT EXISTS supplement_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                BSSH_NM VARCHAR(255) NOT NULL,  -- 업소명
                PRDLST_NM VARCHAR(255) NOT NULL UNIQUE,  -- 품목명 (유일값)
                PRIMARY_FNCLTY TEXT,  -- 주된 기능성
                NTK_MTHD TEXT,  -- 섭취 방법
                IFTKN_ATNT_MATR_CN TEXT,  -- 섭취 시 주의 사항
                RAWMTRL_NM TEXT,  -- 품목 유형(기능지표성분)
                INDIV_RAWMTRL_NM TEXT,  -- 기능성 원재료
                ETC_RAWMTRL_NM TEXT,  -- 기타 원재료
                PRODUCTION VARCHAR(50),  -- 생산 종료 여부
                DISPOS TEXT,  -- 제품 형태 (기존 VARCHAR(255) → TEXT)
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            self.cursor.execute(sql)
            self.connection.commit()
            print("supplement_products 테이블 생성 완료")
        except mysql.connector.Error as error:
            print(f"제품 테이블 생성 실패: {error}")
        finally:
            self.disconnect()


    def save_supplement_products(self, api_url, start=1, end=40801, batch_size=1000):
        try:
            self.connect()

            sql = """
            INSERT INTO supplement_products (
                BSSH_NM, PRDLST_NM, PRIMARY_FNCLTY, NTK_MTHD, 
                IFTKN_ATNT_MATR_CN, RAWMTRL_NM, INDIV_RAWMTRL_NM, 
                ETC_RAWMTRL_NM, PRODUCTION, DISPOS
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                BSSH_NM = VALUES(BSSH_NM),
                PRIMARY_FNCLTY = VALUES(PRIMARY_FNCLTY),
                NTK_MTHD = VALUES(NTK_MTHD),
                IFTKN_ATNT_MATR_CN = VALUES(IFTKN_ATNT_MATR_CN),
                RAWMTRL_NM = VALUES(RAWMTRL_NM),
                INDIV_RAWMTRL_NM = VALUES(INDIV_RAWMTRL_NM),
                ETC_RAWMTRL_NM = VALUES(ETC_RAWMTRL_NM),
                PRODUCTION = VALUES(PRODUCTION),
                DISPOS = VALUES(DISPOS)
            """
            # 천 단위로 데이터개수를 저장
            for i in range(start, end, batch_size):
                batch_start = i
                batch_end = min(i + batch_size - 1, end)
                full_url = f"{api_url}/{batch_start}/{batch_end}"
                print(f"요청 중: {full_url}")

                try:
                    response = requests.get(full_url)
                    data = response.json()

                    # ✅ 너가 사용하는 실제 키에 맞게 수정
                    if "I0030" not in data or "row" not in data["I0030"]:
                        print(f"⚠️ 데이터 없음 또는 응답 형식 오류: {batch_start} ~ {batch_end}")
                        continue

                    items = data["I0030"]["row"]
                    if not isinstance(items, list):
                        items = [items]

                    for item in items:
                        values = (
                            item.get("BSSH_NM"),
                            item.get("PRDLST_NM"),
                            item.get("PRIMARY_FNCLTY"),
                            item.get("NTK_MTHD"),
                            item.get("IFTKN_ATNT_MATR_CN"),
                            item.get("RAWMTRL_NM"),
                            item.get("INDIV_RAWMTRL_NM"),
                            item.get("ETC_RAWMTRL_NM"),
                            item.get("PRODUCTION"),
                            item.get("DISPOS")
                        )
                        self.cursor.execute(sql, values)

                    self.connection.commit()
                    print(f"{batch_start}~{batch_end} 저장 완료")

                except mysql.connector.Error as e:
                    self.connection.rollback()
                    print(f"❌ {batch_start}~{batch_end} 처리 중 에러 발생: {e}")

        except mysql.connector.Error as e:
            self.connection.rollback()
            print(f"전체 저장 과정 중 오류 발생: {e}")
        finally:
            self.disconnect()


    ## 비로그인 페이지에서 문의하기
    #비로그인 문의 저장
    def insert_inquiry(self, email, reason, detail, file_path=None):
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO non_user_inquiries (email, reason, reason_detail, file_name)
                    VALUES (%s, %s, %s, %s)
                """
                values = (email, reason, detail, file_path)
                self.cursor.execute(sql, values)
                self.connection.commit()
                print("문의 저장 완료")
        except mysql.connector.Error as e:
            self.connection.rollback()
            print(f"문의 저장 실패: {e}")
        finally:
            self.disconnect()

    ## 비회원 회원가입

    # 아이디 중복 확인
    def duplicate_userid(self, user_id):
        try:
            self.connect()
            sql = 'SELECT 1 FROM users WHERE user_id = %s'
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as e:
            self.connection.rollback()
            print(f"중복 아이디 확인 실패: {e}")
            return False
        finally:
            self.disconnect()
    
    
    # 이메일 중복 확인
    def duplicate_email(self, email):
        try:
            self.connect()
            sql = 'SELECT * FROM users WHERE email = %s'
            self.cursor.execute(sql, (email,))
            return self.cursor.fetchone()    
        except mysql.connector.Error as e:
            self.connection.rollback()
            print(f"이메일 조회 실패: {e}")
            return False
        finally:
            self.disconnect()

    # 연락처 중복 확인
    def dupliceate_phone(self, phone):
        try:
            self.connect()
            sql = 'SELECT * FROM users WHERE phone = %s'
            self.cursor.execute(sql, (phone,))
            return self.cursor.fetchone()    
        except mysql.connector.Error as e:
            self.connection.rollback()
            print(f"연락처 조회 실패: {e}")
            return False
        finally:
            self.disconnect()

    # 회원가입 후 데이터 저장
    def register_users(self, user_id, user_name, password, email, address, birthday, reg_number, gender, age, phone):
        try:
            # 비밀번호 해싱
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            self.connect()
            sql = """
                INSERT INTO users (user_id, user_name, password, email, address, birthday, reg_number, gender, age, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (user_id, user_name, hashed_password, email, address, birthday, reg_number, gender, age, phone)
            self.cursor.execute(sql, values)
            self.connection.commit()
            print("회원 정보 저장 완료")
            return True
        except mysql.connector.Error as e:
            self.connection.rollback()
            print(f"회원가입 실패: {e}")
            return False
        finally:
            self.disconnect()
    
    # 해싱된 비밀번호 확인
    def verify_user(self, userid):
        try:
            self.connect()
            sql = "SELECT password FROM users WHERE user_id = %s"
            value = (userid,)
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()    
        except mysql.connector.Error as e:
            print(f"로그인 실패: {e}")
            return False
        finally:
            self.disconnect()
    
    ## 회원 계정 정보 찾기 - 아이디 찾기
    def find_userid(self, username, email, phone):
        try:
            self.connect()
            sql = "SELECT user_id FROM users WHERE user_name=%s AND email = %s AND phone = %s"
            value = (username, email, phone)
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()    
        except mysql.connector.Error as e:
            print(f"아이디 찾기 실패: {e}")
            return False
        finally:
            self.disconnect()

    ## 회원 계정 정보 찾기 - 비밀번호 찾기
    def find_user_password(self, userid, username, email, phone):
        try:
            self.connect()
            sql = "SELECT password FROM users WHERE user_id=%s AND user_name=%s AND email = %s AND phone = %s"
            value = (userid, username, email, phone)
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()    
        except mysql.connector.Error as e:
            print(f"비밀번호 찾기 실패: {e}")
            return False
        finally:
            self.disconnect()

    # 사용자 정보 가져오기
    def get_user_by_id(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM users WHERE user_id = %s"
            self.cursor.execute(sql, (userid,))
            return self.cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"사용자 정보 조회 실패: {e}")
            return False
        finally:
            self.disconnect()
    
    # 제품 정보 모두 가져오기
    def get_all_supplement_products(self):
        try:
            self.connect()
            sql = "SELECT * FROM supplement_products limit 11"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"제품 테이블에서 제품 정보 조회 실패: {e}")
            return False
        finally:
            self.disconnect()

    # 전체 제품 정보 가져오기 -페이징 처리
    def get_supplements_by_page(self, page, per_page, search_type, search_query):
        try:
            self.connect()

            # 기본 쿼리
            sql = """
                SELECT * FROM supplement_products
                WHERE 1=1
            """
            
            # 검색 조건 추가
            if search_type == 'product_name' and search_query:
                sql += " AND PRDLST_NM LIKE %s"
            elif search_type == 'manufacturer' and search_query:
                sql += " AND BSSH_NM LIKE %s"

            # 페이지네이션 처리
            sql += " ORDER BY id LIMIT %s OFFSET %s"
            
            # OFFSET 계산
            offset = (page - 1) * per_page
            params = (f"%{search_query}%", per_page, offset) if search_query else (per_page, offset)

            # 실행
            self.cursor.execute(sql, params)
            supplements = self.cursor.fetchall()

            # 전체 개수 계산 (검색 조건 반영)
            count_sql = """
                SELECT COUNT(*) as total FROM supplement_products
                WHERE 1=1
            """
            
            if search_type == 'product_name' and search_query:
                count_sql += " AND PRDLST_NM LIKE %s"
            elif search_type == 'manufacturer' and search_query:
                count_sql += " AND BSSH_NM LIKE %s"
            
            count_params = (f"%{search_query}%",) if search_query else ()
            self.cursor.execute(count_sql, count_params)
            total_count = self.cursor.fetchone()['total']

            return supplements, total_count
        except mysql.connector.Error as e:
            print(f"제품 테이블에서 제품 정보 조회 실패: {e}")
            return False
        finally:
            self.disconnect()
            