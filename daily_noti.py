import requests
import os
import logging
import pandas as pd
from datetime import datetime

# Configuration
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = 'appVQixeY8ZIvhpRF'
MEMBER_TABLE_NAME = 'tbl4rSDtQ1aHWdP7E'
DAILY_TABLE_NAME = 'tblkkU88vQGr1MPoa'

# 사용자 정보
user_info_dict = {
    "user_name": ["강희산", "이새롬", "선우윤", "김나연", "이경원", "김지은"],
    "user_id": ["U07T2RD6R2R", "U07T9LYQL82", "U07TCDZNZPF", "U07TE0FTLSG", "U07U091C2SU", "U07U5QZ96AC"],
    "daily_notification": [True, True, True, True, True, True]  # Default to True
}
user_info = pd.DataFrame(user_info_dict)

# Step 1: Airtable 멤버 테이블에서 사용자 정보 가져와서 매일의 기록 알림 상태 업데이트
def update_status_for_notification(user_info, user_name, table_name):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table_name}?filterByFormula={{이름}}="{user_name}"'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Log the URL and headers
    logging.info(f"Requesting URL: {url}")
    logging.info(f"Request Headers: {headers}")
    
    response = requests.get(url, headers=headers)
    
    if response.ok:
        logging.info(f'Response from Airtable: {response.json()}')  # Log the entire response
        if response.json().get("records"):  # Check if there are records
            for user in user_info["user_name"]:
                if user == user_name:
                    status = response.json()["records"][0]["fields"].get("매일의 기록 알림")  # Use .get() to avoid KeyError
                    if status:
                        user_info.loc[user_info["user_name"]==user, "daily_notification"] = True
                    else:
                        user_info.loc[user_info["user_name"]==user, "daily_notification"] = False
                    break
        else:
            logging.warning('No records found for the given user name.')
    else:
        # Log the error response content
        logging.error(f'Error fetching user info from Airtable: {response.json()}')
        raise Exception(f'Error fetching user info from Airtable: {response.json().get("error")}')

# Step 2: Airtable 데일리 기록 테이블에서 사용자 기록 가져와서 DB item id 추출
def get_db_item_id(member_name, date_string, table_name):
    # Construct the filter formula for multiple conditions
    filter_formula = f"AND({{팀원}}='{member_name}', {{Date String}}='{date_string}')"
    
    # Construct the URL with the filter
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table_name}?filterByFormula={filter_formula}'
    
    # Set up headers with API key
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Make the request
    response = requests.get(url, headers=headers)
    
    # Check if request was successful
    if response.ok:
        data = response.json()
        records = data.get('records', [])
        if records:
            db_item_id = records[0]['fields'].get('DB item id')
            return db_item_id
        else:
            return None
    else:
        print(f'Error: {response.status_code}')
        print(response.json())
        return None

# Step 3: Notion에서 해당 DB item id의 checkbox 상태 확인
def check_notion_checkbox(db_item_id):
    url = f"https://api.notion.com/v1/pages/{db_item_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",  # 노션 API 버전
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 상태 코드 확인
        item = response.json()
        result = {
            "활동 기록": item["properties"]["활동 기록"].get("checkbox"),
            "식사 기록": item["properties"]["식사 기록"].get("checkbox")
        }
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page data: {e}")
        return None

# Step 4: 슬랙 DM 채널 열기
def open_dm_channel(user_id):
    url = "https://slack.com/api/conversations.open"
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}
    payload = {"users": user_id}
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if data.get("ok"):
        return data["channel"]["id"]
    else:
        raise Exception(f"Error opening DM channel: {data.get('error')}")

# Step 5: 슬랙 메시지 보내기
def send_message(channel_id, text):
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}
    payload = {"channel": channel_id, "text": text}
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Error sending message: {data.get('error')}")

# 실행 예제
try:
    for user in user_info["user_name"]:
        # user = "강희산"
        update_status_for_notification(user_info, user, MEMBER_TABLE_NAME)

        if user_info.loc[user_info["user_name"]==user, "daily_notification"].values[0]:
            # 오늘 추출
            today = datetime.today()
            date_string = today.strftime("%Y-%m-%d")
            print(date_string)
            db_item_id = get_db_item_id(user, date_string, DAILY_TABLE_NAME)
            cleaned_db_item_id = db_item_id.replace("-", "")
            print(cleaned_db_item_id)
            checked_status = check_notion_checkbox(db_item_id)
            user_id = user_info.loc[user_info["user_name"]==user, "user_id"].values[0]
            if not(checked_status["활동 기록"] & checked_status["식사 기록"]):
                channel_id = open_dm_channel(user_id)
                message = f"오늘의 기록을 아직 완료하지 않으셨네요! 하루를 마무리하며 오늘의 활동과 식사를 기록해볼까요? \nhttps://www.notion.so/{cleaned_db_item_id}"
                send_message(channel_id, message)
                print("메시지가 성공적으로 전송되었습니다!")
            else:
                print("메시지를 전송하지 않았습니다.")
        
        # if user == "강희산":
        #     break

except Exception as e:
    print(f"오류 발생: {e}")
