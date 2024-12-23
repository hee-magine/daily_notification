import requests

def get_notion_item_with_requests(api_key, page_id):
    """
    노션 페이지(아이템) 상세 정보를 가져오는 함수.

    :param api_key: 노션 API 키 (Integration Token)
    :param page_id: 가져오려는 페이지(아이템)의 ID
    :return: 페이지 정보 (JSON 형식)
    """
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",  # 노션 API 버전
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 상태 코드 확인
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page data: {e}")
        return None

# 예제 사용
if __name__ == "__main__":
    API_KEY = ""  # 노션 API 키
    PAGE_ID = "163359ca-aaac-81ad-b6c2-eabb6f234b38"  # 데이터베이스 아이템 ID

    item = get_notion_item_with_requests(API_KEY, PAGE_ID)
    print(item)