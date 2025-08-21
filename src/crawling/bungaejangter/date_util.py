from datetime import datetime, timedelta
import re

def parse_relative_time(text: str, now: datetime | None = None) -> datetime:
    """
    한국어 상대 시간을 실제 datetime으로 변환
    ex) "1분 전", "2시간 전", "3일 전", "3달 전"
    """
    if now is None:
        now = datetime.now()

    match = re.match(r"(\d+)(분|시간|일|주|달) 전", text.strip())
    if not match:
        raise ValueError(f"지원하지 않는 형식: {text}")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "분":
        return now - timedelta(minutes=value)
    elif unit == "시간":
        return now - timedelta(hours=value)
    elif unit == "일":
        return now - timedelta(days=value)
    elif unit == "주":
        return now - timedelta(weeks=value)
    elif unit == "달":
        # "달" → 30일로 가정
        return now - timedelta(days=value * 30)
    else:
        raise ValueError(f"알 수 없는 단위: {unit}")
