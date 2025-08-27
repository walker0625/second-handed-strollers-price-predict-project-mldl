from PIL import Image, ImageOps
import os
import pandas as pd

def check_image_size(dst_base):
    image_data = []

    for uuid_folder in os.listdir(dst_base):
        uuid_path = os.path.join(dst_base, uuid_folder)
        if os.path.isdir(uuid_path):
            for file_name in os.listdir(uuid_path):
                if file_name.split('.')[0].split('_')[-1] != '1':
                    continue
                file_path = os.path.join(uuid_path, file_name)
                try:
                    with Image.open(file_path) as img:
                        w, h = img.size
                        image_data.append({"uuid": uuid_folder, "file": file_name, "width": w, "height": h})
                except Exception:
                    continue

    df_img = pd.DataFrame(image_data)

    # 사이즈 분포 요약
    print(df_img.describe())

    # 히스토그램 예시
    import matplotlib.pyplot as plt
    df_img["width"].hist(bins=50)
    plt.title("Width Distribution")
    plt.show()

    df_img["height"].hist(bins=50)
    plt.title("Height Distribution")
    plt.show()

def make_square(img: Image.Image, pad_color=(114,114,114), crop_threshold: float = 1.2):
    """
    이미지를 원본 크기 기반으로 정사각형으로 맞춤
    - 비율 차이가 crop_threshold 이상이면 중앙 크롭
    - 아니면 패딩 추가
    """
    w, h = img.size
    aspect_ratio = max(w/h, h/w)

    if aspect_ratio > crop_threshold:
        # 중앙 크롭 (긴 쪽 잘라내기)
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        return img.crop((left, top, right, bottom))
    else:
        # 패딩으로 맞춤 (긴 쪽에 맞춰서 정사각)
        max_dim = max(w, h)
        return ImageOps.pad(img, (max_dim, max_dim), color=pad_color, method=Image.BICUBIC)
