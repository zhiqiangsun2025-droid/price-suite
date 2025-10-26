import os
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service


def build_chrome_options() -> webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()
    # Headless and stability flags for WSL
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1366,900")
    # Try both Google Chrome and Chromium paths if present
    for binary in [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/opt/google/chrome/chrome",
    ]:
        if os.path.exists(binary):
            options.binary_location = binary
            break
    return options


def get_chromedriver_service():
    """尝试多种方式获取chromedriver"""
    # 方法1：使用系统chromedriver
    system_drivers = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ]
    for driver_path in system_drivers:
        if os.path.exists(driver_path):
            return Service(driver_path)
    # 方法2：不指定service，让selenium自动查找
    return None


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def take_admin_screenshots(base_url: str, admin_password: str, out_dir: str) -> dict:
    ensure_dir(out_dir)
    options = build_chrome_options()
    service = get_chromedriver_service()
    if service:
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    results = {"login_png": None, "clients_png": None, "login_html": None, "clients_html": None}
    try:
        login_url = urljoin(base_url, "/admin/login")
        driver.get(login_url)
        # Wait for password input
        wait.until(EC.presence_of_element_located((By.NAME, "password")))

        # Screenshot login page
        login_png = os.path.join(out_dir, "admin_login.png")
        login_html = os.path.join(out_dir, "admin_login.html")
        driver.save_screenshot(login_png)
        with open(login_html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        results["login_png"] = login_png
        results["login_html"] = login_html

        # Fill and submit
        pwd = driver.find_element(By.NAME, "password")
        pwd.clear()
        pwd.send_keys(admin_password)
        # Prefer clicking the submit button
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit.click()

        # Wait for redirect to clients page
        try:
            wait.until(EC.url_contains("/admin/clients"))
        except TimeoutException:
            # Fallback: small delay then continue
            time.sleep(2)

        clients_png = os.path.join(out_dir, "admin_clients.png")
        clients_html = os.path.join(out_dir, "admin_clients.html")
        driver.save_screenshot(clients_png)
        with open(clients_html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        results["clients_png"] = clients_png
        results["clients_html"] = clients_html

        return results
    finally:
        driver.quit()


if __name__ == "__main__":
    BASE_URL = os.environ.get("ADMIN_BASE_URL", "http://127.0.0.1:5000")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    OUT_DIR = os.environ.get(
        "ADMIN_OUT_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tmp")),
    )
    res = take_admin_screenshots(BASE_URL, ADMIN_PASSWORD, OUT_DIR)
    print(res)


