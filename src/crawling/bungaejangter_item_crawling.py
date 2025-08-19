from bs4 import BeautifulSoup
import requests
import pandas as pd
from io import StringIO
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import uuid
import re
import time
import math
from tools.date_util import parse_relative_time
from tools.image_util import download_image
from tools.file_util import ensure_dir
from spec.data import Item
from dataclasses import dataclass, asdict

base_url = "https://m.bunjang.co.kr/"
data_base_path = "../../data/raw/"

def get_keyword_item_count(driver, keyword):
    # 키워드 URL로 이동
    driver.get(base_url + f"search/products?q={keyword}")
    time.sleep(2)

    # 전체 상품 갯수
    item_count_css = "#root > div > div > div:nth-child(4) > div > div.sc-hRmvpr.jtLTMQ > div > div.sc-cZBZkQ.ckPglo > span.sc-ecaExY.jPSzJz"
    item_count = driver.find_element(By.CSS_SELECTOR, item_count_css).text
    item_count = int(re.sub("[^0-9]", "", item_count).text)

    return item_count

def get_keyword_page_count(driver, keyword):
    # 키워드 URL로 이동
    driver.get(base_url + f"search/products?q={keyword}&page=1")
    time.sleep(2)

    # 첫번째 상품 리스트 만들기
    item_list_css = "#root > div > div > div:nth-child(4) > div > div.sc-gacfCG.QBPXM > div > div > a"
    item_list = driver.find_elements(By.CSS_SELECTOR, item_list_css)
    
    # 첫페이지의 상품 갯수
    first_page_item_count = len(item_list)
    # 전체 상품 갯수
    item_count = get_keyword_item_count(driver, keyword)

    page_count = 1
    if item_count > first_page_item_count:
        page_count = math.ceil(item_count / first_page_item_count)
    
    return page_count
    

def get_page_keyword_item_list(driver, page):
    # 키워드 URL로 이동
    driver.get(base_url + f"search/products?q={keyword}&page={page}")
    time.sleep(2)

    # 상품 리스트 만들기
    item_list_css = "#root > div > div > div:nth-child(4) > div > div.sc-gacfCG.QBPXM > div > div > a"
    item_list = driver.find_elements(By.CSS_SELECTOR, item_list_css)

    for item in item_list:
        # 광고인지 체크
        is_ad_css = "div.sc-gVyKpa.kXoKNq > span.sc-cpmKsF.buJhvy"
        try:
            el = item.find_element(By.CSS_SELECTOR, is_ad_css)
            is_ad = el.text == "광고"
        except NoSuchElementException:
            is_ad = False

        if is_ad :
            return None

        # 판매 완료
        is_completed_css = "div > div > div > img"
        try:
            el = item_list.find_element(By.CSS_SELECTOR, is_completed_css)
            is_completed = el.get_attribute('alt') == "판매 완료"
        except NoSuchElementException:
            is_completed = False

        # 업로드 날짜
        # 1분 전, 2시간 전, 3일 전, 3달 전
        uploaded_date_css = "div.sc-iGPElx.iPIFfd > div.sc-gtfDJT.hZQMHB > div.sc-fOICqy.bgZehm"
        uploaded_date = item_list[0].find_element(By.CSS_SELECTOR, uploaded_date_css)
        
        # 날짜 데이터 변환
        uploaded_date = parse_relative_time(uploaded_date.text)

        link = item_list[0].get_attribute("href")

    return {
        is_completed,
        uploaded_date,
        link
    }

def get_item_data(driver, link):            
    driver.get(link)
    
    time.sleep(2)

    # 타이틀
    title_css = "#root > div > div > div.Productsstyle__Wrapper-sc-13cvfvh-0.eVEUVR > div.Productsstyle__ProductPageTop-sc-13cvfvh-1.WbLlq > div > div.Productsstyle__ProductContentWrapper-sc-13cvfvh-8.jGywBa > div > div.Productsstyle__ProductSummaryWrapper-sc-13cvfvh-11.iDkwQU > div > div:nth-child(1) > div.ProductSummarystyle__Basic-sc-oxz0oy-2.ifrXrN > div.ProductSummarystyle__Name-sc-oxz0oy-3.dZBHcg"
    title = driver.find_element(By.CSS_SELECTOR, title_css).text

    # 가격
    price_css = "#root > div > div > div.Productsstyle__Wrapper-sc-13cvfvh-0.eVEUVR > div.Productsstyle__ProductPageTop-sc-13cvfvh-1.WbLlq > div > div.Productsstyle__ProductContentWrapper-sc-13cvfvh-8.jGywBa > div > div.Productsstyle__ProductSummaryWrapper-sc-13cvfvh-11.iDkwQU > div > div:nth-child(1) > div.ProductSummarystyle__Basic-sc-oxz0oy-2.ifrXrN > div.ProductSummarystyle__PriceWrapper-sc-oxz0oy-4.dTIDFF > div"
    price = driver.find_element(By.CSS_SELECTOR, price_css).text
    price = re.sub("[^0-9]", "", price)

    # 상품 상태
    condition_css = "#root > div > div > div.Productsstyle__Wrapper-sc-13cvfvh-0.eVEUVR > div.Productsstyle__ProductPageTop-sc-13cvfvh-1.WbLlq > div > div.Productsstyle__ProductContentWrapper-sc-13cvfvh-8.jGywBa > div > div.Productsstyle__ProductSummaryWrapper-sc-13cvfvh-11.iDkwQU > div > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div.ProductSummarystyle__Value-sc-oxz0oy-21.eLyjky"
    condition = driver.find_element(By.CSS_SELECTOR, condition_css).text

    # 상품 정보
    detail_css = "#root > div > div > div.Productsstyle__Wrapper-sc-13cvfvh-0.eVEUVR > div.Productsstyle__ProductPageTop-sc-13cvfvh-1.WbLlq > div > div.Productsstyle__ProductBottom-sc-13cvfvh-14.fxuPQD > div.Productsstyle__ProductInfoContent-sc-13cvfvh-13.jzEavb > div > div.ProductInfostyle__Wrapper-sc-ql55c8-0.gPJVxW > div.ProductInfostyle__Description-sc-ql55c8-2.hWujk > div.ProductInfostyle__DescriptionContent-sc-ql55c8-3.eJCiaL > p"
    detail = driver.find_element(By.CSS_SELECTOR, detail_css).text

    # 이미지
    image_list_css = "#root > div > div > div.Productsstyle__Wrapper-sc-13cvfvh-0.eVEUVR > div.Productsstyle__ProductPageTop-sc-13cvfvh-1.WbLlq > div > div.Productsstyle__ProductContentWrapper-sc-13cvfvh-8.jGywBa > div > div.Productsstyle__ProductImageWrapper-sc-13cvfvh-10.cXRuyi > div > div.sc-kLIISr.gWGEJy > div > img"
    image_list = driver.find_elements(By.CSS_SELECTOR, image_list_css)

    uid = str(uuid.uuid4())

    ensure_dir(data_base_path + uid)
    for index, image in enumerate(image_list):
        url = image.get_attribute('src')
        download_image(url, f"{data_base_path + uid}/bungaejangter_{uid}_{index}.jpg")

    # 모든 정보 
    item = {
        "id" : uid,
        "title" : title,
        "detail" : detail,
        "condition" : condition,
        "price": price,
    }
    item_data.append(item)

    return item_data


# 웹 브라우저 열기
driver = webdriver.Chrome()
driver.maximize_window() 

time.sleep(2)

keyword_list = ["유모차 스토케", "유모차 부가부", "유모차 사이버"]

for keyword in keyword_list:
    # 키워드 URL로 이동
    driver.get(base_url + f"search/products?q={keyword}&page=1")

    page_count = get_keyword_page_count(driver, keyword)

    # 모든 아이템
    item_data = []
    for i in range(page_count) :
        get_page_keyword_item_list(driver, i + 1)
        get_item_data(base_url + f"search/products?q={keyword}&page={i + 1}")

    dict_list = [asdict(it) for it in item_data]
    df = pd.DataFrame(dict_list)
    df.to_csv(f"{data_base_path}bungaejangter.csv")