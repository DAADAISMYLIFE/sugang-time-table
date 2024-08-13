import time
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# 기본 설정
URL = "http://sugang.deu.ac.kr:8080/DEUSugangPage.aspx#"
COURSE_TYPE = '교양'
GYOYANG_INDEX = 1


# 입력
def input_schedule():
    day = input("수업 요일을 입력하세요 (예: 월, 화, 수, 목, 금): ").strip()
    time_range = input("가능한 시간을 입력하세요 (예: 1-4, 5-8): ").strip()

    # 시간 범위 처리
    start, end = map(int, time_range.split('-')) if '-' in time_range else (int(time_range), int(time_range))

    return day, start, end


# 강의 중 조건에 맞는 강의만 필터링
def filter_classes(all_data, day, start, end):
    filtered_data = []

    for subject_name, classroom, professor in all_data:
        if classroom == "사이버강좌":
            filtered_data.append([subject_name, classroom, professor])
        else:
            if "[" in classroom and "]" in classroom:
                time_info = classroom.split('[')[1][:-1]  # "월7-8" 부분
                lecture_day, time_range = time_info[0], time_info[1:]  # 요일 및 시간

                available_start, available_end = map(int, time_range.split('-')) if '-' in time_range else (
                    int(time_range), int(time_range))

                # 요일 체크 및 시간 범위 비교
                if lecture_day == day and not (available_end <= start or available_start >= end):
                    filtered_data.append([subject_name, classroom, professor])

    return filtered_data


def input_user():
    id = input("학번 : ")
    pw = getpass("비번 : ")

    # CATEGORY 입력 받기
    while True:
        print("카테고리를 선택하세요:")
        print("1: 자율교양")
        print("2: 균형교양")
        choice = input("선택 (1~2): ")

        if choice == "1":
            category = "23 자율교양"
            break
        elif choice == "2":
            category = "25 균형교양"
            break
        else:
            print("잘못된 입력입니다. 1~5 중 하나를 입력해 주세요.")

    gyoyang_index = None
    if category == "25 균형교양":
        while True:
            print("균형교양 인덱스를 선택하세요:")
            print("1: 인간의 이해")
            print("2: 사회의 이해")
            print("3: 자연의 이해")
            print("4: SW의 이해")
            print("5: 공통")
            gyoyang_index = int(input("선택 (1~5): "))

            if not (1 <= gyoyang_index <= 5):
                print("잘못된 입력입니다. 1~5 중 하나를 입력해 주세요.")
            else:
                break

    return id, pw, category, gyoyang_index


# 초기 설정
def setup_driver():
    # 최적화 다 때려박음(이거 나도 잘 모름)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disk-cache-size=20000000")
    chrome_options.add_argument("--media-cache-size=20000000")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-extensions")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


# 로그인
def login(driver, id, pw):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="txtID"]')))
    driver.find_element(By.XPATH, '//*[@id="txtID"]').send_keys(id)
    driver.find_element(By.XPATH, '//*[@id="txtPW"]').send_keys(pw)
    driver.find_element(By.XPATH, '//*[@id="ibtnLogin"]').click()


# 드롭박스로 된 요소 선택
def select_dropdown(driver, xpath, value):
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath)))
    dropdown = Select(driver.find_element(By.XPATH, xpath))
    if isinstance(value, int):
        dropdown.select_by_index(value)
    else:
        dropdown.select_by_visible_text(value)


# 테이블로 된 수강정보들 추출
def extract_data(driver):
    all_data = []
    page_count = 2

    while True:
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "CP1_grdView")))
            table = driver.find_element(By.ID, "CP1_grdView")
            rows = table.find_elements(By.TAG_NAME, "tr")

            # 여기서 한 행씩 뽑는거
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 9:
                    subject_name = cells[4].text
                    classroom = cells[7].text
                    professor = cells[8].text
                    all_data.append([subject_name, classroom, professor])

            try:
                # 다음 페이지로 이동
                next_page_button = driver.find_element(By.ID, f'CP1_COM_Page_Controllor1_lbtnPage{page_count}')
                next_page_button.click()
                page_count += 1
                time.sleep(0.5)
            except Exception:
                break  # 더 이상 다음 페이지가 없으면 종료

        except TimeoutException:
            print("데이터 추출 중 타임 아웃 발생.")
            break

    return all_data


def main():
    #TODO : 예외처리 좀 해주십쇼...
    

    # 사용자 입력
    id, pw, category, gyoyang_index = input_user()

    # 드라이버 초기 셋업
    driver = setup_driver()

    try:
        # 로그인
        login(driver, id, pw)

        # 수강시간표 페이지 이동
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="pnl_stu"]/ul/li[2]/a')))
        driver.find_element(By.XPATH, '//*[@id="pnl_stu"]/ul/li[2]/a').click()
        driver.switch_to.frame("contentFrame")

        # 드롭박스 값 입력
        select_dropdown(driver, '//*[@id="CP1_ddlSubjType"]', COURSE_TYPE)
        select_dropdown(driver, '//*[@id="CP1_ddlIsuGb"]', category)

        gyoyang_domain = ""

        if gyoyang_index is not None:
            select_dropdown(driver, '//*[@id="CP1_ddlGyoyangGb21"]', gyoyang_index)
            gyoyang_domain = ["인간의이해", "사회의이해", "자연의이해", "SW의이해", "공통"]
            gyoyang_domain = gyoyang_domain[gyoyang_index]

        driver.find_element(By.XPATH, '//*[@id="CP1_BtnSearch"]').click()
        all_data = extract_data(driver)

        # 사용자에게 요일과 시간 범위를 입력받음
        day, start, end = input_schedule()

        # 교과목 필터링
        filtered_data = filter_classes(all_data, day, start, end)

        # 결과 출력
        if filtered_data:
            filename = f'{COURSE_TYPE}_{category[3:]}_{gyoyang_domain}_{day}[{start}-{end}].txt'
            with open(filename, 'w', encoding='utf-8') as f:
                for item in filtered_data:
                    f.write('\t'.join(item) + '\n')

            print(f'{filename} 파일 생성 완료')

    except TimeoutException as e:
        print(f"타임 아웃 발생 : {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
