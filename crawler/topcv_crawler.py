import os
from curl_cffi import requests
from bs4 import BeautifulSoup
import psycopg
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
import time

load_dotenv(find_dotenv())

def get_db_connection():
    db_url = os.getenv('DB_CONN')
    if not db_url:
        print("Lỗi: Không tìm thấy biến DB_CONN.")
        return None
    try:
        return psycopg.connect(db_url)
    except Exception as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

def crawl_topcv():
    print("Bắt đầu cào dữ liệu từ TopCV...")
    
    # URL tìm kiếm Data Engineer tại HCM (kl2 là mã của HCM trên TopCV)
    url = "https://www.topcv.vn/tim-viec-lam-data-engineer-tai-ho-chi-minh-kl2"
    
    # Vũ trang Headers cực mạnh để vượt Cloudflare của TopCV
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.topcv.vn/",
        "Sec-Ch-Ua": '"Chromium";v="120", "Google Chrome";v="120", "Not=A?Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # Dùng impersonate="chrome120" để có fingerprint xịn
        response = requests.get(url, impersonate="chrome120", headers=headers)
        
        if response.status_code != 200:
            print(f"Bị chặn rồi bro! Mã lỗi: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm các job card. TopCV thường bọc 1 job trong div có class 'job-item'
        # Dùng regex để tìm tất cả các thẻ div mà class có chứa chữ 'job-item'
        import re
        jobs = soup.find_all('div', class_=re.compile('job-item'))
        
        if not jobs:
            print("Vào được web nhưng không tìm thấy class 'job-item'. Có thể TopCV đã đổi UI.")
            return []

        job_list = []
        for job in jobs:
            try:
                # 1. Bóc Title (Thường nằm trong thẻ h3 hoặc a có class 'title')
                title_elem = job.find(['h3', 'a'], class_=re.compile('title'))
                # Bỏ qua nếu là job lặp lại (TopCV hay có mấy div rỗng hoặc div quảng cáo)
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # 2. Bóc Company (Nằm trong thẻ a có class 'company')
                company_elem = job.find('a', class_=re.compile('company'))
                company = company_elem.text.strip() if company_elem else "N/A"
                
                # 3. Bóc Salary (Nằm trong class 'salary')
                salary_elem = job.find('label', class_=re.compile('salary')) or job.find('span', class_=re.compile('salary'))
                salary = salary_elem.text.strip() if salary_elem else "Thỏa thuận"
                
                # 4. Bóc Location (Nằm trong class 'address')
                location_elem = job.find('label', class_=re.compile('address')) or job.find('span', class_=re.compile('address'))
                location = location_elem.text.strip() if location_elem else "Hồ Chí Minh"

                job_list.append((title, company, salary, location))
            except Exception as e:
                continue
                
        # Lọc trùng lặp (vì class regex có thể bắt nhầm 1 job 2 lần do cấu trúc lồng nhau)
        job_list = list(set(job_list))
        
        print(f"Đã cào được {len(job_list)} jobs từ TopCV.")
        return job_list

    except Exception as e:
        print(f"Lỗi khi request web: {e}")
        return []

def insert_to_supabase(conn, jobs_data):
    if not jobs_data:
        print("Không có dữ liệu để insert.")
        return

    print("Đang đẩy dữ liệu lên Supabase (bảng raw_jobs)...")
    try:
        with conn.cursor() as cur:
            for job in jobs_data:
                cur.execute(
                    """
                    INSERT INTO raw_jobs (title, company, salary, location, created_at) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (job[0], job[1], job[2], job[3], datetime.now())
                )
            conn.commit()
            print("Đã đẩy thành công lên Database!")
    except Exception as e:
        print(f"Lỗi khi insert dữ liệu: {e}")
        conn.rollback()

def main():
    conn = get_db_connection()
    if conn:
        jobs_data = crawl_topcv()
        insert_to_supabase(conn, jobs_data)
        conn.close()

if __name__ == "__main__":
    main()