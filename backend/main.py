from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],  # Update with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "test_images"
OUTPUT_DIR = "processed"

# Ensure the directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
print("current:", os.getcwd())

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"info": f"file '{file.filename}' uploaded successfully"}

@app.get("/processed/{filename}")
def download_processed_image(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# Define paths
YOLOV5_DIR = "yolov5"  # Path to the YOLOv5 folder
WEIGHT_PATH = 'weights/best3.pt'  # Update the weight path

@app.post("/process/")
def process_images():
    for filename in os.listdir(UPLOAD_DIR):
        image_path = f'{UPLOAD_DIR}/{filename}'  # Input image path
        output_path = f'{OUTPUT_DIR}/{filename}'  # Output image path
        yolo_command = f"python {YOLOV5_DIR}/detect.py --source {image_path} --weights {WEIGHT_PATH} --conf 0.4"
        print("my_cmd:", yolo_command)
        subprocess.run(yolo_command, shell=True)
    return {"status": "Processing complete. Files saved in 'processed' folder."}


#? This run
# python detect.py --source ../test_images/test1.jpg --weights ../weights/best3.pt --conf 0.4

