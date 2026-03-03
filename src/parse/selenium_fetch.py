from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "msedgedriver.exe"

service = Service(str(DRIVER))
options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Edge(service=service, options=options)

url = "https://www.zhipin.com/web/geek/job?query=Python%20数据分析"
driver.get(url)

print("如果出现安全验证/登录，请手动完成。完成后回到控制台按回车继续…")
input()

# 关键：验证完成后，再次打开目标页（避免仍停留在 verify.html）
driver.get(url)

# 等待：用一组“可能出现”的岗位卡片选择器，任意出现即可
possible_selectors = [
    "div.job-primary",
    "li.job-card-wrapper",
    "div.search-job-result",
    "a[data-jid]",
]

wait = WebDriverWait(driver, 20)
found = False
for css in possible_selectors:
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        print("检测到岗位列表结构：", css)
        found = True
        break
    except:
        pass

html = driver.page_source
out = ROOT / "data" / "raw" / "boss_search_auto.html"
out.write_text(html, encoding="utf-8")
print("已保存：", out, " HTML长度=", len(html))
print("当前URL：", driver.current_url)
print("页面标题：", driver.title)

driver.quit()

if not found:
    print("警告：未检测到岗位列表结构，可能仍处于验证页或页面为空壳。")