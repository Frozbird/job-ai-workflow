from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "msedgedriver.exe"

options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")

options.add_argument(r"user-data-dir=C:\Users\Simon\AppData\Local\Microsoft\Edge\User Data\Default")
options.add_argument("profile-directory=Default")

# 关键：去掉自动化特征
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

service = Service(str(DRIVER))
driver = webdriver.Edge(service=service, options=options)

# 关键：隐藏 webdriver 标识
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    },
)

url = "https://www.zhipin.com/web/geek/jobs?query=Python%20数据分析"
driver.get(url)

print("如果出现验证，请手动完成，完成后按回车")
input()

for i in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

time.sleep(5)

print("当前URL:", driver.current_url)
print("页面标题:", driver.title)

driver.quit()