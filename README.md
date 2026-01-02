# 👶 딥러닝 모델 기반 중고 유모차 적정 가격 예측 서비스

> **"이미지와 텍스트 정보를 결합하여 중고 유모차의 합리적인 가격을 제안합니다."**

## 1. 프로젝트 개요 (Overview)

중고 거래 플랫폼에서 유모차는 브랜드, 연식, 상태(오염, 파손 등)에 따라 가격 편차가 큽니다. 
판매자와 구매자 간의 정보 비대칭을 해소하고, 제품의 상태(이미지)와 스펙(텍스트)을 종합적으로 분석하여 
적정 중고 가격을 예측하는 AI 모델을 개발했습니다.

* **프로젝트 성격:** End-to-End 머신러닝 파이프라인 구축 (수집-전처리-학습-서빙)
* **주요 역할:** 데이터 수집(당근마켓), 이미지/텍스트 전처리, CNN 기반 회귀 모델링

## 2. 시스템 아키텍처 (System Architecture)

3개의 주요 중고 거래 플랫폼에서 데이터를 수집하여 통합 데이터셋을 구축하고, 딥러닝 모델을 통해 가격을 예측하는 전체 파이프라인입니다.

```text
[ Data Acquisition (Crawling) ]
   │
   ├─ 번개장터 (Bungaejangter) ──┐
   ├─ 당근마켓 (Daangn) ─────────┼──▶ Raw Data 수집
   └─ 네이버 카페 (Naver Cafe) ──┘       │
                                         ▼
[ Data Preprocessing (ETL) ]             │
   │                                     │
   ├─ 텍스트 데이터 ──────────────────▶ [ 정제 및 Feature Engineering ]
   │  (상품명, 가격, 지역 등)              (지역명 표준화, 이상치 제거)
   │                                     │
   └─ 이미지 데이터 ──────────────────▶ [ 이미지 리사이징 & 정규화 ]
                                         │
                                         ▼
                                   (( 통합 데이터셋 구축 ))
                                         │
                                         ▼
[ Model Training (Regression) ]          │
   │                                     │
   ├─ Base Model 선정 ◀──────────────────┘
   │  (ResNet, EfficientNet, ConvNeXt)
   │
   └─ Hyperparameter Tuning ──▶ [ 최종 모델 선정 (Final Model) ]
                                         │
                                         ▼
[ Service ]                              │
   └─ Price Predictor API ◀──────────────┘

```

## 3. 핵심 기술 및 사용 도구 (Tech Stack)

| 구분 | 기술 스택 | 상세 내용 |
| --- | --- | --- |
| **Language** | Python 3.x |  |
| **Data Collection** | Selenium, BeautifulSoup | 동적 웹 페이지 크롤링 및 비동기 데이터 수집 |
| **Data Processing** | Pandas, NumPy | 결측치 처리, 파생 변수 생성(지역, 브랜드 등) |
| **Machine Learning** | Scikit-learn, PyTorch | 회귀 분석 및 딥러닝 모델 학습 |
| **Model Architectures** | ResNet, EfficientNet, ConvNeXt | 이미지 특징 추출을 위한 Backbone 네트워크 활용 |
| **Environment** | Jupyter Notebook, uv | 실험 환경 구성 및 패키지 관리 (`uv.lock`) |

## 4. 데이터셋 구축 및 전처리 (Data Pipeline)

### 4.1 멀티 채널 데이터 수집

국내 대표 중고 거래 플랫폼 3곳에서 다양한 유모차 매물 데이터를 수집하여 데이터의 다양성을 확보했습니다.

* **Target:** `번개장터`, `당근마켓`, `네이버 카페`
* **수집 항목:** 상품명, 가격, 업로드 날짜, 지역 정보(동 단위), 상품 이미지, 본문 텍스트

### 4.2 데이터 전처리 전략

수집된 Raw Data의 노이즈를 제거하고 모델 학습에 적합한 형태로 가공했습니다.

* **지역 정보 표준화:** `dong-number.txt` 등을 활용하여 '강남', '서울시 강남구' 등의 비정형 주소를 행정동 코드로 매핑하여 통일.
* **이상치(Outlier) 제거:** 100원, 1억 원 등 비정상적인 가격 데이터와 오기입 데이터를 통계적 기법으로 제거.
* **이미지 전처리:** 다양한 해상도의 이미지를 모델 입력 사이즈에 맞춰 리사이징하고 정규화(Normalization) 수행.

## 5. 모델링 및 성능 (Modeling & Performance)

단순한 텍스트 기반 분석을 넘어, **제품의 상태가 담긴 '이미지'**를 가격 예측의 핵심 변수로 활용하기 위해 Multi-modal 방식을 적용했습니다.

### 5.1 모델 실험 아키텍처

이미지 Feature와 텍스트(정형) 데이터를 결합(Concatenate)하여 최종 가격을 예측하는 구조입니다.

```text
   [이미지 입력 (Image)]             [텍스트/정형 데이터 (Tabular)]
           │                                      │
           ▼                                      ▼
  ┏━━━━━━━━━━━━━━━━━┓                    ┏━━━━━━━━━━━━━━━━━┓
  ┃  CNN Backbone   ┃                    ┃   Dense Layers  ┃
  ┃ (ConvNeXt 등)   ┃                    ┃ (Brand, Region) ┃
  ┗━━━━━━━━━━━━━━━━━┛                    ┗━━━━━━━━━━━━━━━━━┛
           │ Feature Vector                       │ Feature Vector
           └───────────────┬──────────────────────┘
                           │
                           ▼
                 (( Concatenate Layer ))
                           │
                           ▼
                 ┏━━━━━━━━━━━━━━━━━┓
                 ┃ Fully Connected ┃
                 ┗━━━━━━━━━━━━━━━━━┛
                           │
                           ▼
                   [ 예측 가격 (Price) ]

```

### 5.2 실험 결과 (Results)

최신 아키텍처인 **ConvNeXt**를 포함하여 다양한 모델을 비교 실험했습니다.

* `ResNet`: 안정적인 베이스라인 성능 제공
* `EfficientNet`: 파라미터 대비 효율적인 학습 속도
* `ConvNeXt`: Vision Transformer의 장점을 CNN에 적용하여 가장 정교한 Feature 추출 성능을 보임 (최종 선정)

## 6. 트러블 슈팅 및 배운 점 (Trouble Shooting)

### 🚨 문제 1: 지역 데이터의 비표준화

* **상황:** '서울시 강남구', '강남', '역삼동' 등 플랫폼마다 지역 표기 방식이 제각각이라 지역별 시세 분석이 어려웠음.
* **해결:** 행정안전부의 행정동 코드를 크롤링하여 매핑 테이블을 구축. 비정형 텍스트를 표준 행정동 단위로 변환하여 지역 변수의 퀄리티를 높임.

### 🚨 문제 2: 이미지 데이터의 다양성 처리

* **상황:** 사용자가 직접 찍은 사진은 조명, 각도, 배경이 다양하여 모델 학습이 불안정함.
* **해결:** Data Augmentation(Flip, Rotation)을 적용하고, 전이 학습(Transfer Learning)을 통해 일반화된 이미지 특징을 먼저 학습시킨 후 미세 조정(Fine-tuning)을 수행함.

---

### 📂 Directory Structure

```bash
├── csv/                 # 수집 및 전처리된 데이터셋
├── src/
│   ├── crawling/        # 3사(번개, 당근, 네이버) 크롤러 소스코드
│   ├── preprocessed/    # 데이터 정제 및 병합(Merge) 로직
│   ├── training/        # 모델 학습 및 튜닝 (ConvNeXt, ResNet 등)
│   └── app/             # 추론 모듈 (stroller_price_predictor.py)
├── requirements.txt     # 의존성 패키지 목록
└── main.py              # 메인 실행 파일

```


