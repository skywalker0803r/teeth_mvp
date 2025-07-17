import pyvista as pv
import nibabel as nib
import numpy as np
import os
import nibabel.affines as affines

# --- 設定檔案路徑 ---
BASE_DIR = "teeth_data1"
PATIENT_ID = "002"

cbct_path = os.path.join(BASE_DIR, PATIENT_ID, f"{PATIENT_ID}_cbct", f"{PATIENT_ID}_cbct.nii.gz")
lower_jaw_path = os.path.join(BASE_DIR, PATIENT_ID, f"{PATIENT_ID}_ios", f"{PATIENT_ID}_LowerJawScan.stl")
upper_jaw_path = os.path.join(BASE_DIR, PATIENT_ID, f"{PATIENT_ID}_ios", f"{PATIENT_ID}_UpperJawScan.stl")
# --- 載入和處理資料 ---
try:
    lower_jaw_mesh = pv.read(lower_jaw_path)
    upper_jaw_mesh = pv.read(upper_jaw_path)

    # --- 嘗試手動對齊 STL 模型 (需要根據實際情況調整數值) ---
    # 範例：平移下顎模型
    # lower_jaw_mesh.points += [x_offset, y_offset, z_offset] # 替換 x_offset, y_offset, z_offset 為實際數值

    # 範例：旋轉下顎模型 (繞 X 軸旋轉 90 度)
    # lower_jaw_mesh.rotate_x(90, inplace=True)

    # 範例：平移上顎模型
    # upper_jaw_mesh.points += [x_offset, y_offset, z_offset]

    # 範例：旋轉上顎模型
    # upper_jaw_mesh.rotate_y(90, inplace=True)
    # --- 手動對齊範例結束 ---

except FileNotFoundError as e:
    print(f"錯誤: 找不到 STL 檔案: {e}")
    exit()

try:
    nii_img = nib.load(cbct_path)
    affine = nii_img.affine
    volume_data = nii_img.get_fdata()
    print(f"CBCT affine matrix:\n{affine}")
    print(f"CBCT data min/max: {np.min(volume_data)} / {np.max(volume_data)}")
except FileNotFoundError as e:
    print(f"錯誤: 找不到 NIfTI 檔案: {e}")
    exit()

# 從 affine 矩陣提取 spacing 和 origin
spacing = np.abs(np.diag(affine)[:3])
# 使用 nibabel.affines.apply_affine 計算 [0,0,0] 體素在世界座標中的位置
origin = affines.apply_affine(affine, [0, 0, 0])

grid = pv.ImageData()
grid.dimensions = np.array(volume_data.shape)
grid.spacing = spacing
grid.origin = origin
grid.point_data["values"] = volume_data.flatten(order="C")

# --- 視覺化 ---
plotter = pv.Plotter(window_size=[1024, 768])

# 儲存原始網格，以便每次變換都從原始狀態開始
lower_jaw_mesh_initial = lower_jaw_mesh.copy()
upper_jaw_mesh_initial = upper_jaw_mesh.copy()
plotter.add_mesh(lower_jaw_mesh, color="white", opacity=0.7, name="Lower Jaw")
plotter.add_mesh(upper_jaw_mesh, color="white", opacity=0.7, name="Upper Jaw")

# 方案二：使用預設的不透明度傳輸函數
# PyVista 提供了一些預設的函數，例如 'linear' 或 'sigmoid'
# 'sigmoid' 函數通常適用於醫學影像，能有效區分軟組織和硬組織
plotter.add_volume(grid, cmap="bone", opacity="sigmoid", name="CBCT Volume")

# --- 互動式滑桿設定 ---

# 初始變換參數
lower_jaw_params = {'tx': 0.0, 'ty': 0.0, 'tz': 0.0, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0}
upper_jaw_params = {'tx': 0.0, 'ty': 0.0, 'tz': 0.0, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0}

# 更新下顎模型的回調函數
def update_lower_jaw_transform(value, param_name):
    print(f"Lower Jaw: Updating {param_name} to {value}")
    lower_jaw_params[param_name] = value
    
    # 每次都從原始網格的完整副本開始
    transformed_mesh = lower_jaw_mesh_initial.copy()
    
    # 應用平移
    transformed_mesh.translate([lower_jaw_params['tx'], lower_jaw_params['ty'], lower_jaw_params['tz']], inplace=True)
    
    # 應用旋轉
    transformed_mesh.rotate_x(lower_jaw_params['rx'], inplace=True)
    transformed_mesh.rotate_y(lower_jaw_params['ry'], inplace=True)
    transformed_mesh.rotate_z(lower_jaw_params['rz'], inplace=True)
    
    print(f"Lower Jaw points (first 3):\n{transformed_mesh.points[:3]}")
    
    # 直接更新演員的輸入數據
    actor = plotter.actors["Lower Jaw"]
    actor.SetInputData(transformed_mesh.GetPolyData())
    actor.GetMapper().Update()
    
    plotter.render()
    plotter.reset_camera() # 嘗試重置相機以強制重繪

# 更新上顎模型的回調函數
def update_upper_jaw_transform(value, param_name):
    print(f"Upper Jaw: Updating {param_name} to {value}")
    upper_jaw_params[param_name] = value
    
    # 每次都從原始網格的完整副本開始
    transformed_mesh = upper_jaw_mesh_initial.copy()
    
    # 應用平移
    transformed_mesh.translate([upper_jaw_params['tx'], upper_jaw_params['ty'], upper_jaw_params['tz']], inplace=True)
    
    # 應用旋轉
    transformed_mesh.rotate_x(upper_jaw_params['rx'], inplace=True)
    transformed_mesh.rotate_y(upper_jaw_params['ry'], inplace=True)
    transformed_mesh.rotate_z(upper_jaw_params['rz'], inplace=True)
    
    print(f"Upper Jaw points (first 3):\n{transformed_mesh.points[:3]}")
    
    # 直接更新演員的輸入數據
    actor = plotter.actors["Upper Jaw"]
    actor.SetInputData(transformed_mesh.GetPolyData())
    actor.GetMapper().Update()
    
    plotter.render()
    plotter.reset_camera() # 嘗試重置相機以強制重繪

# 添加下顎平移滑桿
plotter.add_slider_widget(
    lambda value: update_lower_jaw_transform(value, 'tx'),
    [-100, 100], value=0, title='Lower Jaw Tx',
    pointa=(0.02, 0.9), pointb=(0.3, 0.9)
)
plotter.add_slider_widget(
    lambda value: update_lower_jaw_transform(value, 'ty'),
    [-100, 100], value=0, title='Lower Jaw Ty',
    pointa=(0.02, 0.85), pointb=(0.3, 0.85)
)
plotter.add_slider_widget(
    lambda value: update_lower_jaw_transform(value, 'tz'),
    [-100, 100], value=0, title='Lower Jaw Tz',
    pointa=(0.02, 0.8), pointb=(0.3, 0.8)
)

# 添加下顎旋轉滑桿
plotter.add_slider_widget(
    lambda value: update_lower_jaw_transform(value, 'rx'),
    [-180, 180], value=0, title='Lower Jaw Rx',
    pointa=(0.02, 0.7), pointb=(0.3, 0.7)
)
plotter.add_slider_widget(
    lambda value: update_lower_jaw_transform(value, 'ry'),
    [-180, 180], value=0, title='Lower Jaw Ry',
    pointa=(0.02, 0.65), pointb=(0.3, 0.65)
)
plotter.add_slider_widget(
    lambda value: update_lower_jaw_transform(value, 'rz'),
    [-180, 180], value=0, title='Lower Jaw Rz',
    pointa=(0.02, 0.6), pointb=(0.3, 0.6)
)

# 添加上顎平移滑桿
plotter.add_slider_widget(
    lambda value: update_upper_jaw_transform(value, 'tx'),
    [-100, 100], value=0, title='Upper Jaw Tx',
    pointa=(0.7, 0.9), pointb=(0.98, 0.9)
)
plotter.add_slider_widget(
    lambda value: update_upper_jaw_transform(value, 'ty'),
    [-100, 100], value=0, title='Upper Jaw Ty',
    pointa=(0.7, 0.85), pointb=(0.98, 0.85)
)
plotter.add_slider_widget(
    lambda value: update_upper_jaw_transform(value, 'tz'),
    [-100, 100], value=0, title='Upper Jaw Tz',
    pointa=(0.7, 0.8), pointb=(0.98, 0.8)
)

# 添加上顎旋轉滑桿
plotter.add_slider_widget(
    lambda value: update_upper_jaw_transform(value, 'rx'),
    [-180, 180], value=0, title='Upper Jaw Rx',
    pointa=(0.7, 0.7), pointb=(0.98, 0.7)
)
plotter.add_slider_widget(
    lambda value: update_upper_jaw_transform(value, 'ry'),
    [-180, 180], value=0, title='Upper Jaw Ry',
    pointa=(0.7, 0.65), pointb=(0.98, 0.65)
)
plotter.add_slider_widget(
    lambda value: update_upper_jaw_transform(value, 'rz'),
    [-180, 180], value=0, title='Upper Jaw Rz',
    pointa=(0.7, 0.6), pointb=(0.98, 0.6)
)

# --- 設定場景和顯示 ---
axes_actor = pv.create_axes_marker(labels_off=True)
plotter.add_orientation_widget(axes_actor)
plotter.add_title(f"CBCT and IOS Scans for Patient {PATIENT_ID}", font_size=16)

print("正在開啟 3D 視覺化視窗...")
print("操作提示: 左鍵=旋轉, 右鍵=縮放, 中鍵=平移")
print("使用滑桿調整牙齒模型位置和方向。")
plotter.show()
print("視窗已關閉。")