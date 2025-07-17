
import pyvista as pv
import nibabel as nib
import numpy as np
import os

# --- 設定檔案路徑 ---
# 您可以修改這個基底路徑和病患編號
BASE_DIR = "teeth_data1"
PATIENT_ID = "002"

# 自動建立檔案路徑
cbct_path = os.path.join(BASE_DIR, PATIENT_ID, f"{PATIENT_ID}_cbct", f"{PATIENT_ID}_cbct.nii.gz")
lower_jaw_path = os.path.join(BASE_DIR, PATIENT_ID, f"{PATIENT_ID}_ios", f"{PATIENT_ID}_LowerJawScan.stl")
upper_jaw_path = os.path.join(BASE_DIR, PATIENT_ID, f"{PATIENT_ID}_ios", f"{PATIENT_ID}_UpperJawScan.stl")

# --- 載入和處理資料 ---

# 1. 載入 STL 網格
try:
    lower_jaw_mesh = pv.read(lower_jaw_path)
    upper_jaw_mesh = pv.read(upper_jaw_path)
except FileNotFoundError as e:
    print(f"錯誤: 找不到 STL 檔案: {e}")
    exit()

# 2. 載入 NIfTI 影像
try:
    nii_img = nib.load(cbct_path)
    # 取得影像資料和仿射矩陣 (affine)
    # 仿射矩陣定義了影像資料在物理空間中的位置、方向和尺度
    affine = nii_img.affine
    # 將資料轉換為 numpy 陣列
    volume_data = nii_img.get_fdata()
except FileNotFoundError as e:
    print(f"錯誤: 找不到 NIfTI 檔案: {e}")
    exit()

# 3. 建立 PyVista 的影像資料物件
# 我們需要將 numpy 陣列轉換為 PyVista 可以理解的格式
# 注意：PyVista 和 Nibabel 的座標方向可能不同，仿射矩陣 (affine) 是關鍵
# 我們先建立一個 UniformGrid
grid = pv.ImageData()
grid.dimensions = np.array(volume_data.shape)
# 將 numpy 陣列與 grid 關聯
grid.point_data["values"] = volume_data.flatten(order="F")  # 使用 Fortran 順序

# 使用仿射矩陣來正確地定位、縮放和旋轉影像
# 我們將仿射矩陣應用到 grid 的點上
transform_matrix = pv.vtkmatrix_from_array(affine)
grid.transform(transform_matrix, inplace=True)


# --- 視覺化 ---

# 建立一個繪圖器
plotter = pv.Plotter(window_size=[1024, 768])

# 1. 加入 STL 網格到場景
# style='surface' 表示以實體表面顯示
# color='white' 和 opacity=0.7 可以讓它看起來像牙齒模型
plotter.add_mesh(lower_jaw_mesh, color="white", opacity=0.7, name="Lower Jaw")
plotter.add_mesh(upper_jaw_mesh, color="white", opacity=0.7, name="Upper Jaw")

# 2. 加入 CBCT 影像
# 我們有幾種方式可以視覺化體積資料：

# 選項 A: 顯示三個正交切面 (類似 3D Slicer 的紅、黃、綠線)
# plotter.add_mesh(grid.slice_orthogonal(), name="Orthogonal Slices")

# 選項 B: 顯示單一一個切面，並可以拖動
# plotter.add_mesh(grid.slice(normal='z'), name="Single Slice")

# 選項 C: 體積渲染 (Volume Rendering) - 這最能展現 3D 結構
# `cmap='bone'` 使用類似骨頭的顏色映射
# `opacity='linear'` 讓低密度區域更透明，高密度區域更實心
plotter.add_volume(grid, cmap="bone", opacity="linear", name="CBCT Volume")


# --- 設定場景和顯示 ---

# 加入一個方向標示
axes_actor = pv.create_axes_marker(labels_off=True)
plotter.add_orientation_widget(axes_actor)

# 設定攝影機初始位置
plotter.camera_position = 'xy'
plotter.camera.roll = 90 # 調整視角以符合通常的牙科視角

# 增加一個標題
plotter.add_title(f"CBCT and IOS Scans for Patient {PATIENT_ID}", font_size=16)

# 顯示場景，這會開啟一個互動視窗
# 您可以用滑鼠左鍵旋轉、右鍵縮放、中鍵平移
print("正在開啟 3D 視覺化視窗...")
print("操作提示: 左鍵=旋轉, 右鍵=縮放, 中鍵=平移")
plotter.show()

print("視窗已關閉。")
