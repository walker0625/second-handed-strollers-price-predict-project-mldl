import os
import time
from datetime import datetime

import streamlit as st
import torch
import torch.nn as nn
from torchvision import models
from PIL import Image

# 페이지 & 스타일
st.set_page_config(page_title="유모차 중고거래 가격 추천", page_icon="🍼", layout="centered")
st.markdown(
    """
    <style>
    
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    
    h1 {font-weight: 800; letter-spacing: -0.3px;}
    
    div.stButton > button {
        width: 100%; height: 56px; font-size: 20px; font-weight: 700;
        background: #FF8A1E; color: white; border: none; border-radius: 8px;
    }
    
    div.stButton > button:hover {background: #ff9e45; color: white; border: none;}
    
    .card {background: #111111; padding: 24px; border-radius: 10px; margin-top: 16px; margin-bottom: 24px;}
    
    .card h3 {margin-top: 0; font-weight: 800; letter-spacing: -0.3px;}
    
    label, .stSelectbox label, .stNumberInput label, .stRadio label, label {
        font-weight: 800 !important; font-size: 18px !important;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1>🍼 유모차 중고거래 가격 추천</h1>", unsafe_allow_html=True)

# 옵션 (학습 때 사용한 순서와 동일해야 함)
condition_options = ['새 상품', '거의 새 것', '사용감 있음']
city_options = [
    '서울특별시','부산광역시','경기도','인천광역시','대구광역시',
    '대전광역시','광주광역시','세종특별자치시','울산광역시','제주특별자치도'
]
model_options = ['yoyo','explori','trailz','beat','crusi','scoot']
model_type_options = ['절충형','디럭스']

# 이미지 업로드
st.markdown("<div>이미지를 업로드 해주세요</div>", unsafe_allow_html=True)
uploaded = st.file_uploader("이미지를 업로드 해주세요", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
if uploaded is not None:
    st.image(uploaded, use_column_width=True, caption="업로드한 이미지 미리보기")

st.divider()

# 입력 UI
col = st.container()
with col:
    condition = st.selectbox("사용감", condition_options, index=2, key="condition")
    city = st.selectbox('도시명', city_options, index=9, key="location")
    model_name = st.selectbox('모델명', model_options, index=4, key="model")
    model_type = st.selectbox('모델 등급', model_type_options, index=1, key="model_type")

# 모델 정의 (학습 구조와 동일)
class CombinedModel(nn.Module):
    """
    ConvNeXt-Small image + csv -> 회귀 출력(가격)
    """
    def __init__(self, tabular_data_size, backbone, img_dim=64, tab_dim=256, tab_scale=1.0, img_scale=1.0):
        super().__init__()
        self.tab_scale = tab_scale
        self.img_scale = img_scale
        self.conv_part = backbone

        with torch.no_grad():
            dummy = torch.randn(1, 3, 224, 224)
            out = self.conv_part(dummy)
            conv_out_dim = out.shape[-1] if out.ndim == 2 else out.numel()

        self.img_head = nn.Sequential(nn.Linear(conv_out_dim, img_dim), nn.ReLU())
        self.tab_head = nn.Sequential(nn.Linear(tabular_data_size, tab_dim), nn.ReLU())

        combined_features_size = img_dim + tab_dim
        
        self.reg_part = nn.Sequential(
            nn.Linear(combined_features_size, 512), nn.ReLU(),
            nn.Linear(512, 128), nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, images, tabular_data):
        image_features = self.conv_part(images) * self.img_scale
        tab_features   = tabular_data * self.tab_scale
        image_features = self.img_head(image_features)   
        tab_features   = self.tab_head(tab_features)     
        combined = torch.cat([image_features, tab_features], dim=1)
        
        return self.reg_part(combined)                   

WEIGHT_PATH = "../training/model/convnext_best.pt"

def _extract_state_dict(obj):
    if isinstance(obj, dict):
        if "state_dict" in obj and isinstance(obj["state_dict"], dict):
            return obj["state_dict"]
        
        for k in ["model_state_dict", "net", "model"]:
            if k in obj and isinstance(obj[k], dict):
                return obj[k]
            
    return obj  

def _strip_module_prefix(state):
    if not isinstance(state, dict):
        return state
    
    need_strip = any(k.startswith("module.") for k in state.keys())
    
    if not need_strip:
        return state
    
    return {k.replace("module.", "", 1): v for k, v in state.items()}

@st.cache_resource(show_spinner=False)
def load_model_and_preprocess(weight_path: str = WEIGHT_PATH):
    # 1) 체크포인트 읽기
    try:
        raw = torch.load(weight_path, map_location="cpu")
    except Exception as e:
        st.error(f"가중치 파일을 불러올 수 없습니다: {e}")
        st.stop()

    state = _extract_state_dict(raw)
    state = _strip_module_prefix(state)

    # 2) 체크포인트에서 기대 차원 읽기
    try:
        img_dim_from_ckpt = state["img_head.0.weight"].shape[0]   
        tab_size_from_ckpt = state["tab_head.0.weight"].shape[1]  
    except Exception as e:
        st.error(f"체크포인트에서 레이어 모양을 읽을 수 없습니다: {e}")
        st.stop()

    # 3) 백본 & 전처리
    weights = models.ConvNeXt_Small_Weights.DEFAULT
    backbone = models.convnext_small(weights=weights)
    backbone.classifier[2] = nn.Identity()
    backbone.eval()
    preprocess = weights.transforms()

    # 4) 모델 인스턴스 (체크포인트 모양에 맞추기)
    model = CombinedModel(
        tabular_data_size=tab_size_from_ckpt,
        backbone=backbone,
        img_dim=img_dim_from_ckpt,   # ex) 32
        tab_dim=256
    )
    model.eval()

    # 5) 가중치 로드(모양이 이미 맞아서 strict=True 가능)
    try:
        model.load_state_dict(state, strict=True)
    except Exception as e:
        st.error(f"가중치 로드 실패: {e}")
        st.stop()

    return model, preprocess, tab_size_from_ckpt

model, preprocess, TAB_EXPECT = load_model_and_preprocess()


# 탭 인코딩 (체크포인트 기대 크기에 맞춤)
def build_tab_tensor(condition, city, model_name, model_type, expected_size: int):
    c_idx = condition_options.index(condition)
    s_idx = city_options.index(city)
    m_idx = model_options.index(model_name)
    t_idx = model_type_options.index(model_type)

    if expected_size == 21:
        vec = []
        # condition (3)
        for opt in condition_options: vec.append(1.0 if condition==opt else 0.0)
        # city (10)
        for opt in city_options: vec.append(1.0 if city==opt else 0.0)
        # model (6)
        for opt in model_options: vec.append(1.0 if model_name==opt else 0.0)
        # model_type (2)
        for opt in model_type_options: vec.append(1.0 if model_type==opt else 0.0)
        return torch.tensor(vec, dtype=torch.float32).unsqueeze(0)

    elif expected_size in (4, 5):
        vec = [float(c_idx), float(s_idx), float(m_idx), float(t_idx)]
        if expected_size == 5:
            vec.append(1.0)  
        return torch.tensor(vec, dtype=torch.float32).unsqueeze(0)

    else:
        st.error(f"지원되지 않는 탭 입력 크기입니다: {expected_size}")
        st.stop()

def save_uploaded_image(file):
    os.makedirs("sent_data", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"sent_data/{ts}.jpg"
    Image.open(file).convert("RGB").save(path)
    return path

# 버튼 & 추론
clicked = st.button("가격 예측하기")

if clicked:
    if uploaded is None:
        st.warning("이미지를 먼저 업로드해 주세요.")
        st.stop()

    with st.spinner("🔮 모델이 가격을 예측 중입니다..."):
        saved_path = save_uploaded_image(uploaded)

        image = Image.open(uploaded).convert("RGB")
        img_tensor = preprocess(image).unsqueeze(0)  # (1,3,224,224)
        tab_tensor = build_tab_tensor(condition, city, model_name, model_type, expected_size=TAB_EXPECT)

        with torch.no_grad():
            pred = model(img_tensor, tab_tensor).squeeze().item()

        rec_price = max(0, round(float(pred)))
        time.sleep(0.4)

    st.success("예측이 완료되었습니다 ✅")
    st.markdown("<div>", unsafe_allow_html=True)
    st.markdown("<h3>결과</h3>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2.2])
    with c1:
        st.markdown("**추천 가격**")
    with c2:
        st.text_input("추천 가격", f"{rec_price:,} 원", key="predict_price", disabled=True, label_visibility="collapsed")

    st.caption(f"이미지 저장 위치: {saved_path}")
else:
    st.markdown(
        """
        <div class="card">
            <h3>결과</h3>
            <p>입력 후 <b>가격 예측하기</b> 버튼을 눌러주세요.</p>
        </div>
        """,
        unsafe_allow_html=True
    )