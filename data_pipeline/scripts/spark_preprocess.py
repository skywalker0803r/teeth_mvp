import os
import sys

# 模擬 Spark 讀取原始影像並進行前處理
def spark_preprocess(input_dir, output_dir):
    print(f"Simulating Spark preprocessing from {input_dir} to {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.dcm'): # 假設是 DICOM 檔案
            input_filepath = os.path.join(input_dir, filename)
            output_filename = filename.replace('.dcm', '.features.txt')
            output_filepath = os.path.join(output_dir, output_filename)

            # 模擬讀取和寫入特徵檔案
            with open(input_filepath, 'r') as f_in:
                raw_data = f_in.read()
            
            # 模擬生成特徵數據
            features_data = f"Processed features for {filename}: {raw_data.upper()}\n"

            with open(output_filepath, 'w') as f_out:
                f_out.write(features_data)
            print(f"  Processed {filename} -> {output_filename}")

    print("Spark preprocessing simulation complete.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python spark_preprocess.py <input_directory> <output_directory>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    spark_preprocess(input_dir, output_dir)
