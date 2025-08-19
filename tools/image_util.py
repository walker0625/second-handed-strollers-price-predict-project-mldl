import requests

def download_image(url: str, save_path: str, chunk_size: int = 1024) -> bool:
    """
    주어진 URL에서 이미지를 다운로드하여 지정한 경로에 저장합니다.

    Args:
        url (str): 이미지 URL
        save_path (str): 저장할 파일 경로
        chunk_size (int): 다운로드할 때 사용할 청크 크기 (기본 1024)

    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    try:
        resp = requests.get(url, stream=True, timeout=10)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size):
                    if chunk:  # keep-alive chunks 건너뛰기
                        f.write(chunk)
            print(f"다운로드 완료: {save_path}")
            return True
        else:
            print(f"다운로드 실패: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"오류 발생: {e}")
        return False