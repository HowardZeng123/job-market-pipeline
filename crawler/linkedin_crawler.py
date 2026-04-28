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

def crawl_linkedin():
    print("Bắt đầu cào dữ liệu từ LinkedIn (Guest API)...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    job_list = []
    
    # Cào thử 2 trang (mỗi trang LinkedIn load khoảng 25 jobs)
    for page_num in range(2):
        start_index = page_num * 25
        print(f"Đang cào LinkedIn từ vị trí {start_index}...")
        
        # Link API ẩn của LinkedIn. Trả về mã HTML thuần của các thẻ <li>
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Data%20Engineer&location=Ho%20Chi%20Minh&start={start_index}"
        
        try:
            response = requests.get(url, impersonate="chrome120", headers=headers)
            
            if response.status_code != 200:
                print(f"Bị Microsoft chặn rồi! Mã lỗi: {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = soup.find_all('li')
            
            if not jobs:
                print("Không còn job nào hoặc bị block IP tạm thời.")
                break

            for job in jobs:
                try:
                    title_elem = job.find('h3', class_='base-search-card__title')
                    title = title_elem.text.strip() if title_elem else "N/A"
                    
                    if title == "N/A": 
                        continue # Bỏ qua thẻ rỗng
                        
                    company_elem = job.find('h4', class_='base-search-card__subtitle')
                    company = company_elem.text.strip() if company_elem else "N/A"
                    
                    location_elem = job.find('span', class_='job-search-card__location')
                    location = location_elem.text.strip() if location_elem else "Hồ Chí Minh"
                    
                    # LinkedIn cực kỳ hiếm khi public lương, nhưng cứ cào phòng hờ
                    salary_elem = job.find('span', class_='job-search-card__salary-info')
                    salary = salary_elem.text.strip() if salary_elem else "Thỏa thuận"

                    job_list.append((title, company, salary, location))
                except Exception as e:
                    continue
            
            # Ngủ 3 giây né đạn của LinkedIn
            time.sleep(3)
            
        except Exception as e:
            print(f"Lỗi khi request LinkedIn: {e}")
            break
            
    print(f"Đã hút được {len(job_list)} jobs từ LinkedIn.")
    return job_list

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
        jobs_data = crawl_linkedin()
        insert_to_supabase(conn, jobs_data)
        conn.close()

if __name__ == "__main__":
    main()