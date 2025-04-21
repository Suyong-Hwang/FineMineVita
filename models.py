import mysql.connector 
from datetime import datetime
from flask import jsonify
import json
import requests
import re

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    ## 데이터베이스 연결
    def connect(self): 
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.8",
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

                except Exception as e:
                    print(f"❌ {batch_start}~{batch_end} 처리 중 에러 발생: {e}")

        except Exception as e:
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
        except mysql.connector.Error as error:
            print(f"문의 저장 실패: {error}")
        finally:
            self.disconnect()

    ## 비회원 회원가입
    # 아이디 중복 확인
    def duplicate_users(self, user_id):
        try:
            self.connect()
            sql = 'SELECT * FROM users WHERE user_id = %s'
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
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
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()