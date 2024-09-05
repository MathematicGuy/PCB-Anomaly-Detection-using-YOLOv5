import glob
import os
import re
import csv
import tempfile
import zipfile
from io import BytesIO

import torch
import shutil
import subprocess
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import models
from database.database import get_db, engine
from database.models import PCB, Error  # Assuming your SQLAlchemy models are in models.py
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin for development; limit this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories for uploading and processing
UPLOAD_DIR = "../images/test_images"
SAVE_DIR = "../images/uploaded"
OUTPUT_DIR = "../images/processed"
YOLO_DETECT_PATH = 'yolov5/runs/detect'  # Path for YOLOv5 results
WEIGHT_PATH = 'weights/best3.pt'  # YOLOv5 model weights

# Ensure the directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize database
models.Base.metadata.create_all(bind=engine)


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image to the server."""
    # Validate file type
    if not file.filename.endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, JPEG, and PNG files are allowed.")

    try:
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        # Save file asynchronously
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logging.info(f"File uploaded: {file.filename}")
        return {"info": f"file '{file.filename}' uploaded successfully"}
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")


@app.delete("/delete/{filename}")
async def delete_image(filename: str):
    """Delete an image from the UPLOAD_DIR folder."""
    # Construct the file path
    file_location = os.path.join(UPLOAD_DIR, filename)

    # Check if the file exists
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    try:
        # Remove the file
        os.remove(file_location)
        logging.info(f"File deleted: {file_location}")
        return {"info": f"file '{filename}' deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file '{filename}'.")


@app.post("/process/")
async def process_images(db: Session = Depends(get_db)):
    """Process uploaded images with YOLOv5 and save the results."""
    
    try:
        # Process each file in the upload directory
        for filename in os.listdir(UPLOAD_DIR):
            image_path = f"{UPLOAD_DIR}/{filename}"  # Input image path

            # Run YOLOv5 detection on the image
            yolo_command = f'python yolov5/detect.py --source {image_path} --weights {WEIGHT_PATH} --conf 0.4'
            subprocess.run(yolo_command, shell=True, check=True)

            logging.info(f"Processed file: {filename}")
            
            # Load YOLOv5 model and perform inference (assuming you use the torch hub API in detect.py)
            model = torch.hub.load('ultralytics/yolov5', 'custom', path=WEIGHT_PATH)
            results = model(image_path)  # Perform inference
            
            # Get the detection predictions
            det = results.xyxy[0]  # Format: [x1, y1, x2, y2, confidence, class]
            class_names = results.names  # Get class names from the model
            
            # Extract detections
            detections = extract_detections(det, class_names)

            # Save detection results (CSV and database)
            for detection in detections:
                save_to_csv(filename, detection['class'], detection['confidence'], detection['bbox'])
                save_to_db(db, filename, detection['class'], detection['confidence'], detection['bbox'])

        # Copy results to the processed directory
        move_images_to_processed(YOLO_DETECT_PATH, OUTPUT_DIR)
        
        # Move processed images to the processed folder
        move_images_to_uploaded(UPLOAD_DIR, SAVE_DIR)

        return {"status": "Processing complete. Results saved to CSV and database."}

    except subprocess.CalledProcessError as e:
        logging.error(f"YOLOv5 processing error: {e}")
        raise HTTPException(status_code=500, detail="Error processing images.")

    except Exception as e:
        logging.error(f"Error in processing images: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@app.get("processed/{filename}")
def download_processed_image(filename: str):
    """Download a processed image by filename."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        logging.error(f"Processed file not found: {filename}")
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/latest-pros/")
async def get_latest_pros():
    """API to return the contents of the latest 'pros' folder."""
    latest_folder = get_latest_pros_folder()

    if not latest_folder:
        raise HTTPException(status_code=404, detail="No 'pros' folder found.")

    folder_path = os.path.join(OUTPUT_DIR, latest_folder)
    files = os.listdir(folder_path)

    if not files:
        raise HTTPException(status_code=404, detail=f"No files found in the latest folder '{latest_folder}'.")

    return {"folder": latest_folder, "files": files}


@app.get("/download-latest-pros/")
async def download_latest_pros():
    """Download all images from the latest 'pros' folder as a zip."""
    latest_folder = get_latest_pros_folder()

    if not latest_folder:
        raise HTTPException(status_code=404, detail="No 'pros' folder found.")

    folder_path = os.path.join(OUTPUT_DIR, latest_folder)
    files = os.listdir(folder_path)

    if not files:
        raise HTTPException(status_code=404, detail=f"No files found in the latest folder '{latest_folder}'.")

    # Create a zip file in a temporary location
    zip_filename = f"{latest_folder}.zip"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                file_path = os.path.join(folder_path, file)
                zf.write(file_path, arcname=file)  # Add file to the zip, use arcname to avoid full path

        zip_path = tmp.name  # Store the temp file path

    return FileResponse(zip_path, media_type="application/x-zip-compressed", filename=zip_filename)

#? Helper function
def get_latest_pros_index(destination_folder):
    """Get the highest index of existing 'pros' folders in the destination folder."""
    existing_folders = os.listdir(destination_folder)
    max_index = 0

    # Use regex to find folders that match 'pros', 'pros2', 'pros3', etc.
    for folder in existing_folders:
        match = re.match(r'pros(\d*)', folder)
        if match:
            index = match.group(1)
            if index == "":  # This is the first 'pros' folder without a number
                index = 1
            else:
                index = int(index)
            max_index = max(max_index, index)

    return max_index


def move_images_to_processed(base_source_folder, destination_folder):
    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    # Get the next available 'pros' folder name based on the latest index
    latest_index = get_latest_pros_index(destination_folder)
    if latest_index == 0:
        pros_folder = os.path.join(destination_folder, 'pros')
    else:
        pros_folder = os.path.join(destination_folder, f'pros{latest_index + 1}')

    # Now create the unique pros folder
    os.makedirs(pros_folder)

    i = 1
    while True:
        # The first folder is named 'exp', then 'exp2', 'exp3', etc.
        if i == 1:
            source_folder = os.path.join(base_source_folder, "exp")
        else:
            source_folder = os.path.join(base_source_folder, f"exp{i}")

        # Check if the source folder exists; if not, break the loop
        if not os.path.exists(source_folder):
            break

        # Loop through all the files in the exp{i} folder
        for filename in os.listdir(source_folder):
            if filename.endswith((".jpg", ".jpeg", ".png")):  # Only move image files
                source_path = os.path.join(source_folder, filename)

                # Add _processed before the file extension
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}_processed{ext}"

                destination_path = os.path.join(pros_folder, new_filename)

                # Move the file with the new name
                shutil.move(source_path, destination_path)
                print(f"Moved {filename} from {source_folder} to {pros_folder} as {new_filename}")

        # Move to the next exp{i} folder
        i += 1

    print(f"All images from yolov5/runs/detect/exp folders have been moved to {pros_folder}")


def get_latest_upload_index(destination_folder):
    """Get the highest index of existing 'upload' folders in the destination folder."""
    existing_folders = os.listdir(destination_folder)
    max_index = 0

    # Use regex to find folders that match 'upload', 'upload2', 'upload3', etc.
    for folder in existing_folders:
        match = re.match(r'upload(\d*)', folder)
        if match:
            index = match.group(1)
            if index == "":  # This is the first 'upload' folder without a number
                index = 1
            else:
                index = int(index)
            max_index = max(max_index, index)

    return max_index


def move_images_to_uploaded(source_folder, destination_folder):
    # Ensure destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    # Get the next available 'upload' folder name based on the latest index
    latest_index = get_latest_upload_index(destination_folder)
    if latest_index == 0:
        upload_folder = os.path.join(destination_folder, 'upload')
    else:
        upload_folder = os.path.join(destination_folder, f'upload{latest_index + 1}')

    # Now create the unique upload folder
    os.makedirs(upload_folder)

    # Loop through all the files in the source folder
    for filename in os.listdir(source_folder):
        if filename.endswith((".jpg", ".jpeg", ".png")):  # Only move image files
            source_path = os.path.join(source_folder, filename)

            # Move the file to the new upload folder
            destination_path = os.path.join(upload_folder, filename)
            shutil.move(source_path, destination_path)
            print(f"Moved {filename} to {upload_folder}")

    print(f"All images from {source_folder} have been moved to {upload_folder}")


def extract_detections(det, class_names):
    """Extract detection information from YOLOv5 output."""
    results = []
    for *xyxy, conf, cls in reversed(det):
        bbox = [float(x) for x in xyxy]
        confidence = float(conf)
        class_id = int(cls)
        class_name = class_names[class_id]
        results.append({
            "class": class_name,
            "confidence": confidence,
            "bbox": bbox
        })
    return results


def save_to_csv(image_name, prediction, confidence, bbox):
    """Save detection results to a CSV file."""
    CSV_PATH = "yolov5/runs/detect/detection_results.csv"
    try:
        data = {"Image Name": image_name, "Prediction": prediction, "Confidence": confidence, "BBox": bbox}
        with open(CSV_PATH, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if os.stat(CSV_PATH).st_size == 0:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")
        raise HTTPException(status_code=500, detail="Error saving to CSV.")


def save_to_db(db: Session, image_name, prediction, confidence, bbox):
    """Save detection results to the PostgreSQL database using SQLAlchemy."""
    try:
        # Check if the PCB already exists
        pcb = db.query(PCB).filter(PCB.image_path == image_name).first()

        if pcb is None:
            pcb = PCB(image_path=image_name)
            db.add(pcb)
            db.commit()
            db.refresh(pcb)

        # Save the detection (Error record) linked to pcb_id
        new_error = Error(
            pcb_id=pcb.pcb_id,
            error_type=prediction,
            confidence=confidence,
            location=str(bbox)
        )
        db.add(new_error)
        db.commit()
    except Exception as e:
        logging.error(f"Error saving to database: {e}")
        raise HTTPException(status_code=500, detail="Error saving to database.")

def get_latest_pros_folder():
    """Find the latest 'pros' folder inside the processed directory."""
    existing_folders = os.listdir(OUTPUT_DIR)
    max_index = 0
    latest_pros_folder = ""

    # Use regex to find folders that match 'pros', 'pros2', 'pros3', etc.
    for folder in existing_folders:
        if folder.startswith('pros'):
            index = folder.replace('pros', '')
            if index == "":
                index = 1
            else:
                index = int(index)
            if index > max_index:
                max_index = index
                latest_pros_folder = folder

    if latest_pros_folder:
        return latest_pros_folder
    return None

@app.post("/clean-database/")
def clean_database(db: Session = Depends(get_db)):
    try:
        # Run the queries to clean the database
        db.execute(text("DELETE FROM errors"))
        db.execute(text("DELETE FROM pcbs"))
        db.execute(text("ALTER SEQUENCE pcbs_pcb_id_seq RESTART WITH 1"))

        # Commit the changes
        db.commit()

        return {"status": "Database cleaned successfully. The pcb_id sequence has been reset."}
    
    except Exception as e:
        # Rollback the transaction in case of an error
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while cleaning the database: {str(e)}")


