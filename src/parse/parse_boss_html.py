import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# 读取保存的HTML文件
with open('data/raw/boss_search_1.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# 使用BeautifulSoup解析HTML
soup = BeautifulSoup(html_content, 'lxml')

# 获取职位列表
job_listings = soup.find_all('div', class_='job-primary')

# 初始化空列表来存储抓取的数据
job_data = []

# 解析每一个职位的信息
for job in job_listings:
    job_title = job.find('div', class_='job-title').text.strip() if job.find('div', class_='job-title') else None
    salary = job.find('span', class_='red').text.strip() if job.find('span', class_='red') else None
    city = job.find('span', class_='job-area').text.strip() if job.find('span', class_='job-area') else None
    experience = job.find('span', class_='job-exp').text.strip() if job.find('span', class_='job-exp') else None
    education = job.find('span', class_='edu').text.strip() if job.find('span', class_='edu') else None
    company_name = job.find('div', class_='company-text').find('a').text.strip() if job.find('div', class_='company-text') else None
    company_industry = job.find('div', class_='industry').text.strip() if job.find('div', class_='industry') else None
    job_url = job.find('a', class_='js-job-link')['href'] if job.find('a', class_='js-job-link') else None
    crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 当前时间
    
    # 将抓取的数据加入到列表
    job_data.append([job_title, salary, city, experience, education, company_name, company_industry, job_url, crawl_time])

# 将抓取的数据转换为DataFrame
df = pd.DataFrame(job_data, columns=['job_title', 'salary', 'city', 'experience', 'education', 'company_name', 'company_industry', 'job_url', 'crawl_time'])

# 保存为CSV文件
df.to_csv('data/processed/jobs_raw.csv', index=False, encoding='utf-8')

print("数据已保存到 'data/processed/jobs_raw.csv'")