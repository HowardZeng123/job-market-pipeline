import os
from curl_cffi import requests # <-- Đổi từ requests thường sang curl_cffi
from bs4 import BeautifulSoup
import psycopg
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
import re

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

def crawl_itviec():
    print("Bắt đầu cào dữ liệu từ ITviec...")
    url = "https://itviec.com/it-jobs/data-engineer/ho-chi-minh-hcm"
    
    try:
        # Thêm tham số impersonate="chrome120" để giả dạng như người thật
        response = requests.get(url, impersonate="chrome120")
        my_cookie = '''_ga=GA1.1.955482552.1753366148; _fbp=fb.1.1773739697596.775944665688064831; vi_locale=false; _gcl_gs=2.1.k1$i1776410383$u200988534; _gcl_aw=GCL.1776410445.CjwKCAjwtIfPBhAzEiwAv9RTJpIaI4j0aFudt5Z51h-I2LEr9yu9SZAvYLNbE-Z5pugbNvqWP0aprBoCGowQAvD_BwE; viewed_jobs=xEok7g2TxkGQe3w%2BvRm4pxzWl5XPxCzvIt9fFXPdM%2BacjzwoFSWKfs9AhK8r2Km1h7Hr4bU64fi2KfGTxPI9uobl3xZFmTs8dxSkOLG0wNw0gb%2BWqG1l%2FzRT0f65fIBcPxWoJ2O45zM6sE4qdCm35Kp9ki1LELFDS1FP9zufFX90dsJ89jQwh%2FL5M4ry--mNd%2BOLDwqye0EmRW--XmV49NicSKPoKU1NxqzJIQ%3D%3D; g_state={"i_l":0,"i_ll":1777020193225,"i_e":{"enable_itp_optimization":19},"i_et":1777020188474}; auth_token=tttTuzKEAPpkGmXkwD%2ByiCcjj1BuG9ItmhckNfqf0pKIIrAxHtCzTB7cSrVDWnt24MLvNO%2FmXxOXCHYplzg9b9ZSVZ5SJ7P6qyme55AZYKW6vimendetbxr47E9OtRFlI%2F1OwF7AQNZRgPQOrx0%2Bvobi%2BdoFaxkifWfEdwDHxMCGoOEacKaEKgkkRK3xPKVqQGiPd2m2uenAAYzVPkzx6Joc5kTxRDK8kuy3TbfXfCAEDgJ4rd2ag1mFlaozZM%2FiF39%2FGLuSqVynhC%2FqKSXkU64eVCXE9MQrO%2FYaDfhIdo7ZHWjIyxn6GHIXcyBQ5Awl2tdKqDfnmDHsTM51gOq8a7F2%2Bvs%3D--Rtkq7CJte8TWt%2Fn3--bbhy7e8pt%2BV4xeWywiWw1Q%3D%3D; count_promote_review_popup=1; device_id=eyJfcmFpbHMiOnsibWVzc2FnZSI6IkltSmhOakl3WmpZM0xXSmxNakl0TkdZd1ppMWhNbVkxTFdFeFlqTXlaakE1TXpObU5DST0iLCJleHAiOm51bGwsInB1ciI6ImNvb2tpZS5kZXZpY2VfaWQifX0%3D--42caf7f8e2099d72c2c8947aadccddf20d36791f; recent_searches=OODbHWU7knS3FIHREBc7JYzfoEV53b0K9ymmUmcmU6dpG0dsK%2FGKPQxI9a5j3YWV5zOe61KPXtxSoadc6ZbY76rzPstFsJtskV5CHfGgfaRSJaK51STB--3NTWBIDQQ6dGGtli--eASBu3LdWaumC6BqA%2FUBKQ%3D%3D; last_city_searched=ho-chi-minh-hcm; search_query=eyJfcmFpbHMiOnsibWVzc2FnZSI6IkltUmhkR0V0Wlc1bmFXNWxaWElpIiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuc2VhcmNoX3F1ZXJ5In19--1a2bd420b6c6bdeb42498cc0265aceca0a0fc229; _gcl_au=1.1.1488827741.1773739695.984521520.1777303241.1777303240; cf_clearance=GWUc1B3ky_ckTFruQ3Xoi0M2nKC7wnFfK0hOHbcsrjc-1777304056-1.2.1.1-fUG.GDNLReFw0Fhi7t_x.aGAeaw8F608Dddb0xaE26E8bqAQ4GK_Hfwx6iUzPvXZR7MX.BZ5NOs7rwapHmrYm87WkblPpDqWkusSyWSbjFj3mS.pR6jpdslLpp4JWPXxCFdxvDreoAF0kj8kVQwaQC4SYLnswbtBn97Yvq.to90l3T9BKqAqcYcpCstD0Bz.IEtN4JOIcf54DM4Zr1stAJhkFeDVd3sN1v.SMo1HZcPhGhJDd4frah9Mhzwsae7Hh63_VVEjMYkavAFzXl52B88QZfQKvMyyKte3bBq6t6lDA4TCz9waXRO_ywwiRGrASlDZulC2nV2ZgULU9iukcg; _ITViec_session=GfgZNwBoWw9s6FlUrzqG38Oy52EQ6KQhbY2Ak7xQfYIc829PzlN535IAM1aTMrzYVek%2FPF1Ytl%2BEmYEusYVKqzZGuQdYPAaqc6LOnI3%2FcjPWhQkBmtouHCQ4EV5w2pyj5tkAO%2BztDclY78cCCUQDLtirFP4ZYo5eOUzMMa%2FDNA7DEnxCgjfzIZ3c58MX%2F46GCwbwXNjY38unSyNuRDb%2FLkbsQDK8DPw7hEJu0Nq60ieoScPHB5J8cEMT0bO2Tn5imk6CI3kUiGHzq91bwt4%2FLS54Gkz%2F4G1jCSciYMqMfOta4q2fFpelPZ%2Fw%2FkglVD2bidsatekDjMFU2s4F8MoxmhrjLC1G7B%2BVA1GzmgVHMXZLMKRcswQ58w4oUquMDNJVw0E10y3P1hioSKzODlR9uFTDFl6q2DE6RBDDsn71zsUVlqvT95oZxaAQe9BtbFFh%2Fbm%2Bof%2FpH7oDErGwm1rICbKIL7Y2RIKdWWQFtFcXHNj2%2BukcNmbirJrbTPfhAkqqM2oWjeLj%2FUZsyCwglgi8M3ATDJpxQi4dAp7LutZet3EvnKFNtivheKrALORUu71JTfcgB6DbGmC4vP7Okzj9NShn7Nc3w76db%2FbQKvcxWu6F7U8sDvwruoT%2BRq2Bm1ueZFhaM5PYMYoLFVD3nTGg2jIArOzkUsXCqRcdu%2BqJfKv7rgGoLPQ5P3YSH6zAcc3EuSz9OucuJ6hey9rliH9HH3bEtiPlgHiNX4M5u4Ui3UqjKaAXK1cbN1H3B30MddTklwtgwr0hvcUAbCB4diDbCyMfk8chNSxcGmRr%2Fcx60PBQqampmmzyfJKXdd7SiElap7xIW7xa3L8cHjVp3yT%2BxmnMXJHjFixlP%2FVfPOd7papc%2B7XoIkKohV2FB0TlWVmqvBOUAUHAl9ECsmfSuJU3E5ntiD5Y%2B%2Fl%2BIjsn2Qyc5oXV9VLa542xoG1QuEp1HWJne0ovWRXFxt5JQmDPKUf4dZXfY7QszaxeClSQw%2FFp2aSnWKHXJx4hBhJeGWU3qjvuPCMtojxseXdHruDVFyRsJ9I1wfS0jyJKcsy0Y0s%3D--1QNWMFrmXbRPXfEE--RxUluHpmuqMZGrfQsqftOA%3D%3D; _ga_H9FSZTPEGR=GS2.1.s1777303239$o22$g1$t1777304149$j30$l0$h1996411051'''

        headers = {
        "Cookie": my_cookie,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "Referer": "https://itviec.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }
        
        # 3. KIỂM TRA ĐĂNG NHẬP (Debug)
        if "Đăng nhập" in response.text or 'href="/sign_in"' in response.text:
            print("❌ THẤT BẠI: Bot vẫn bị coi là Khách. Cookie sai, đã hết hạn, hoặc bị từ chối!")
            # Tạm thời cứ cho chạy tiếp để thấy lỗi
        else:
            print("✅ THÀNH CÔNG: Bot đã được ITviec nhận diện là User đăng nhập!")

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('div', class_='job-card') 
        
        if not jobs:
            print("Không tìm thấy class 'job-card'.")
            return []

        job_list = []
        for job in jobs:
            try:
                # 1. Bóc Title
                title_elem = job.find('h3')
                title = title_elem.text.strip() if title_elem else "N/A"
                
                # 2. Bóc Company 
                company_elem = job.find('a', class_='text-rich-grey')
                if not company_elem:
                    company_elem = job.find('a', href=lambda href: href and '/companies/' in href)
                company = company_elem.text.strip() if company_elem else "N/A"
                
                # 3. Bóc Salary (Tối ưu theo ảnh chụp DOM)
                salary_div = job.find('div', class_='salary')
                
                if salary_div:
                    # Chọc thẳng vào thẻ span chứa số tiền bên trong div salary
                    salary_span = salary_div.find('span')
                    # Nếu có thẻ span thì lấy text của nó, không thì lấy text của div cha
                    salary = salary_span.text.strip() if salary_span else salary_div.text.strip()
                else:
                    salary = "Thỏa thuận"
                
                # 4. Bóc Location
                location_elem = job.find('div', class_='location')
                location = location_elem.text.strip() if location_elem else "Hồ Chí Minh"

                job_list.append((title, company, salary, location))
            except Exception as e:
                continue
                
        print(f"Đã cào được {len(job_list)} jobs từ ITviec.")
        return job_list

    except Exception as e:
        print(f"Lỗi khi request web: {e}")
        return []

def insert_to_supabase(conn, jobs_data):
    if not jobs_data:
        print("Không có dữ liệu để insert.")
        return

    print("Đang đẩy dữ liệu lên Supabase...")
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
        jobs_data = crawl_itviec()
        insert_to_supabase(conn, jobs_data)
        conn.close()

if __name__ == "__main__":
    main()