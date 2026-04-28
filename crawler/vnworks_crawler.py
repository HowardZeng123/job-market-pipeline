import os
import requests
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

def crawl_vnworks_api():
    print("Bắt đầu cào VietnamWorks bằng đường API...")
    url = 'https://ms.vietnamworks.com/job-search/v1.0/search'
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://www.vietnamworks.com',
        'Referer': 'https://www.vietnamworks.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    }

    job_list = []
    
    # Thiết lập vòng lặp cào 3 trang (page 0, 1, 2). Mỗi trang 20 jobs = 60 jobs
    for page_num in range(3):
        print(f"Đang cào dữ liệu Trang {page_num + 1}...")
        
        json_data = {
            'userId': 8137009,
            'query': 'data engineer',
            'filter': [
                {'field': 'workingLocations.cityId', 'value': '29'},
                {'field': 'workingLocations.districtId', 'value': '[{"cityId":29,"districtId":[-1]}]'},
            ],
            'ranges': [],
            'order': [],
            'hitsPerPage': 20,
            'page': page_num, # Truyền số trang vào đây để nhảy trang
            'retrieveFields': [
                'jobTitle', 'companyName', 'prettySalary', 'address'
            ],
            'summaryVersion': '',
        }

        try:
            response = requests.post(url, headers=headers, json=json_data)
            
            if response.status_code != 200:
                print(f"Lỗi gọi API ở trang {page_num}! Mã lỗi: {response.status_code}")
                break
                
            data = response.json()
            
            # API của VietnamWorks thường trả danh sách job trong key 'data'
            jobs = data.get('data', [])
            
            if not jobs:
                print("Đã hết dữ liệu (hoặc API đổi cấu trúc). Dừng cào.")
                break
                
            for job in jobs:
                title = job.get('jobTitle', 'N/A')
                company = job.get('companyName', 'N/A')
                
                # prettySalary là chuỗi lương đã format đẹp (ví dụ: $1000 - $2000)
                salary = job.get('prettySalary')
                if not salary: 
                    salary = "Thỏa thuận"
                    
                location = job.get('address', 'Hồ Chí Minh')

                job_list.append((title, company, salary, location))
                
            # Nghỉ 2 giây trước khi cào trang tiếp theo để tránh bị server block IP
            time.sleep(2)
            
        except Exception as e:
            print(f"Lỗi khi xử lý JSON trang {page_num}: {e}")
            break
            
    print(f"Tổng cộng đã hút được {len(job_list)} jobs từ API VietnamWorks!")
    return job_list

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
        jobs_data = crawl_vnworks_api()
        insert_to_supabase(conn, jobs_data)
        conn.close()

if __name__ == "__main__":
    main()