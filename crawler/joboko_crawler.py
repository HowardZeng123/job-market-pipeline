import os
from curl_cffi import requests
from bs4 import BeautifulSoup
import psycopg
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

load_dotenv(find_dotenv())

def get_db_connection():
    db_url = os.getenv('DB_CONN')
    if not db_url: return None
    try:
        return psycopg.connect(db_url)
    except Exception as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

def crawl_joboko():
    print("Bắt đầu cào dữ liệu từ Joboko")
    url = "https://vn.joboko.com/jobs?q=data+engineer"
    
    headers = {
        "Accept-Language": "vi-VN,vi;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, impersonate="chrome120", headers=headers)
        if response.status_code != 200:
            print(f"Bị chặn! Mã lỗi: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.select('div.item[data-jid]')
        
        if not jobs:
            print("Không tìm thấy job card nào.")
            return []

        job_list = []
        garbage_badges = ['UP', 'HOT', 'MỚI', 'NEW', 'GẤP'] # Danh sách nhãn rác

        for job in jobs:
            try:
                # 1. BÓC TITLE THÔNG MINH
                a_tags = job.select('.item-head a')
                title = "N/A"
                for a in a_tags:
                    text = a.text.strip()
                    # Nếu text không nằm trong danh sách rác thì nó chính là Title thật
                    if text.upper() not in garbage_badges and text != "":
                        title = text
                        break # Tìm thấy title thật rồi thì dừng vòng lặp ngay
                
                # 2. Bóc các phần còn lại
                company_elem = job.select_one('.item-company')
                company = company_elem.text.strip() if company_elem else "N/A"
                
                location_elem = job.select_one('.item-address')
                location = location_elem.text.strip() if location_elem else "Hồ Chí Minh"
                
                salary_elem = job.select_one('.item-rate')
                salary = salary_elem.text.strip() if salary_elem else "Thỏa thuận"

                # 3. Filter cuối cùng trước khi đưa vào list
                if company != "N/A" and title != "N/A":
                    job_list.append((title, company, salary, location))
                    # In ra Terminal để bro kiểm chứng trực tiếp
                    print(f"Lụm: {title} | {company}")
                    
            except Exception as e:
                continue
                
        job_list = list(set(job_list))
        print(f"\n=> Đã cào xong {len(job_list)} jobs SIÊU SẠCH từ Joboko.")
        return job_list

    except Exception as e:
        print(f"Lỗi request: {e}")
        return []

def insert_to_supabase(conn, jobs_data):
    if not jobs_data: return
    print("Đang đẩy dữ liệu lên Supabase...")
    try:
        with conn.cursor() as cur:
            for job in jobs_data:
                cur.execute(
                    "INSERT INTO raw_jobs (title, company, salary, location, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (job[0], job[1], job[2], job[3], datetime.now())
                )
            conn.commit()
            print("Đã đẩy thành công lên Database!")
    except Exception as e:
        print(f"Lỗi khi insert: {e}")
        conn.rollback()

def main():
    conn = get_db_connection()
    if conn:
        jobs_data = crawl_joboko()
        insert_to_supabase(conn, jobs_data)
        conn.close()

if __name__ == "__main__":
    main()