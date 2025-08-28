import streamlit as st
from datetime import datetime
import time

st.set_page_config(page_title="유모차 중고거래 가격 추천", page_icon="🍼", layout="centered")

# ----------------------------
# 스타일
# ----------------------------
st.markdown(
    """
    <style>
    /* 제목 간격 */
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {font-weight: 800; letter-spacing: -0.3px;}

    /* 큰 오렌지 버튼 */
    div.stButton > button {
        width: 100%;
        height: 56px;
        font-size: 20px;
        font-weight: 700;
        background: #FF8A1E;
        color: white;
        border: none;
        border-radius: 8px;
        
    }
    div.stButton > button:hover {
        background: #ff9e45;
        color: white;
        border: none;
    }

    /* 결과 카드 */
    .card {
        background: #111111;
        padding: 24px;
        border-radius: 10px;
        margin-top: 16px;
        margin-bottom: 24px;
    }
    .card h3 {
        margin-top: 0;
        font-weight: 800;
        letter-spacing: -0.3px;
    }

    /* 레이블 강조 */
    label, .stSelectbox label, .stNumberInput label, .stRadio label, label {
        font-weight: 800 !important;
        font-size: 18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# 헤더
# ----------------------------
st.markdown("<h1>🍼 유모차 중고거래 가격 추천</h1>", unsafe_allow_html=True)

# ----------------------------
# 이미지 업로드 (큰 업로드 박스)
# ----------------------------
st.markdown("<div>이미지를 업로드 해주세요</div>", unsafe_allow_html=True)
uploaded = st.file_uploader("이미지를 업로드 해주세요", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# 업로드 미리보기 (선택)
if uploaded is not None:
    st.image(uploaded, use_column_width=True, caption="업로드한 이미지 미리보기")

st.divider()

# ----------------------------
# 입력 영역
# ----------------------------
brand_options = ["Bugaboo", "Stokke", "Cybex"]

condition_options = ["새상품급", "매우 좋음", "보통", "사용감 있음", "수리 필요"]

col = st.container()

with col:
    brand = st.selectbox("브랜드명", brand_options, index=0, key="brand")
    condition = st.selectbox("사용감", condition_options, index=2, key="cond")
    year = st.number_input(
        "구매연도",
        min_value=2010, max_value=datetime.now().year, value=2021, step=1
    )
    fold = st.selectbox("접이식", ["가능", "불가"], index=0)

# ----------------------------
# 예시 예측 로직 (단순 더미: 레이아웃용)
# 실제 모델 연결 시 이 부분만 교체
# ----------------------------
def simple_pricing(brand: str, condition: str, year: int, foldable: str):
    base_by_brand = {
        "Bugaboo": 850000, "Stokke": 900000, "Cybex": 800000, "UPPAbaby": 850000,
        "Doona": 700000, "Silver Cross": 780000, "iCandy": 750000, "Baby Jogger": 600000,
        "Quinny": 550000, "Joie": 420000, "Aprica": 520000, "페도라": 400000, "리안": 380000, "기타": 350000
    }
    cond_mult = {
        "새상품급": 0.95, "매우 좋음": 0.85, "보통": 0.70, "사용감 있음": 0.55, "수리 필요": 0.35
    }
    age = max(0, datetime.now().year - year)
    dep = 0.85 ** age  # 단순 감가
    fold_bonus = 1.03 if foldable == "가능" else 0.97

    base = base_by_brand.get(brand, 350000)
    price = int(base * cond_mult[condition] * dep * fold_bonus)

    low = int(price * 0.9)
    high = int(price * 1.1)

    # 간단한 판매예상일: 상태/브랜드로 가중
    speed = 30  # 기본 30일
    if condition in ["새상품급", "매우 좋음"]:
        speed -= 7
    if brand in ["Bugaboo", "Stokke", "Cybex", "UPPAbaby", "Doona", "Silver Cross"]:
        speed -= 5
    speed = max(7, speed)

    return price, (low, high), speed

# ----------------------------
# 버튼 & 결과
# ----------------------------
clicked = st.button("가격 예측하기")

if clicked:
    rec_price, (low, high), days = simple_pricing(brand, condition, year, fold)

    with st.spinner("🔮 모델이 가격을 예측 중입니다... 잠시만 기다려주세요!"):
        # 실제 모델 호출 대신, 예시로 3초 대기
        time.sleep(3)

        # 모델 응답 결과 (예시)
        rec_price = 480000
        low, high = 450000, 520000
        days = 12

        # 실제 코드 (예)
        # response = model.predict({
        #     "brand": brand,
        #     "condition": condition,
        #     "year": year,
        #     "fold": fold,
        # })

    # 결과 출력
    st.success("예측이 완료되었습니다 ✅")
    
    st.markdown("<div>", unsafe_allow_html=True)
    st.markdown("<h3>결과</h3>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2.2])
    with c1:
        st.markdown("**추천 가격**")
    with c2:
        st.text_input("추천 가격", f"{rec_price:,} 원", key="r_price", disabled=True, label_visibility="collapsed")

    c1, c2 = st.columns([1, 2.2])
    with c1:
        st.markdown("**가격 범위**")
    with c2:
        st.text_input("가격 범위", f"{low:,} 원 ~ {high:,} 원", key="r_range", disabled=True, label_visibility="collapsed")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    # 빈 결과 카드(레이아웃 유지 원하면 주석 해제)
    st.markdown(
        """
        <div class="card">
            <h3>결과</h3>
            <p>입력 후 <b>가격 예측하기</b> 버튼을 눌러주세요.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
