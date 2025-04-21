#!/usr/bin/env python3
import cv2
import numpy as np
import os
import tempfile
import shutil
import pyautogui
from datetime import datetime
from fpdf import FPDF

# Quality presets (width, height)
QUALITY_PRESETS = {
    '480p': (854, 480),
    '720p': (1280, 720),
    '1080p': (1920, 1080),
    '2k': (2560, 1440),
    '4k': (3840, 2160)
}

def create_temp_directory():
    """Create a temporary directory for screenshots"""
    return tempfile.mkdtemp()

def cleanup_temp_directory(temp_dir):
    """Remove temporary directory and all screenshots"""
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def take_screenshot_opencv(temp_folder, quality='720p'):
    """Take a screenshot using pyautogui and process with OpenCV, saving to a temporary folder"""
    try:
        # Get quality dimensions
        if quality not in QUALITY_PRESETS:
            raise ValueError(f"Invalid quality setting: {quality}")
        
        target_width, target_height = QUALITY_PRESETS[quality]
        
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}_{quality}.png"
        filepath = os.path.join(temp_folder, filename)
        
        # Take screenshot using pyautogui
        screenshot = pyautogui.screenshot()
        
        # Convert PIL image to OpenCV format (numpy array)
        screenshot_cv = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)
        
        # Resize to target quality while maintaining aspect ratio
        original_height, original_width = screenshot_cv.shape[:2]
        aspect_ratio = original_width / original_height
        
        # Calculate new dimensions while maintaining aspect ratio
        if aspect_ratio > (target_width / target_height):
            # Width is the limiting factor
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            # Height is the limiting factor
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
        
        # Resize the image
        resized = cv2.resize(screenshot_cv, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Create a black canvas of the target size
        canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        # Calculate position to center the image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        # Place the resized image on the canvas
        canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
        
        # Save screenshot using OpenCV
        cv2.imwrite(filepath, canvas)
        
        print(f"Screenshot captured at {datetime.now().strftime('%H:%M:%S')} ({quality})")
        return filepath
    except Exception as e:
        print(f"Error capturing screenshot: {str(e)}")
        raise

def create_pdf_with_fpdf(screenshot_files, pdf_path):
    """Create a PDF from a list of screenshot files using FPDF"""
    try:
        if not screenshot_files:
            print("No screenshots to create PDF")
            return False

        pdf = FPDF()
        
        for img_path in screenshot_files:
            try:
                # Get image dimensions
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Warning: Could not read image {img_path}, skipping")
                    continue
                    
                height, width, _ = img.shape
                
                # Add a page with appropriate orientation
                if width > height:
                    pdf.add_page('L')  # Landscape
                else:
                    pdf.add_page('P')  # Portrait
                
                # Calculate page dimensions
                page_width = pdf.w
                page_height = pdf.h
                
                # Calculate image size to fit the page with margins
                margin = 10
                max_width = page_width - 2 * margin
                max_height = page_height - 2 * margin - 10  # Extra 10 for timestamp text
                
                # Calculate scale factor to fit within page margins
                width_scale = max_width / width
                height_scale = max_height / height
                scale = min(width_scale, height_scale)
                
                # Calculate dimensions after scaling
                new_width = width * scale
                new_height = height * scale
                
                # Calculate position to center the image
                x = margin + (max_width - new_width) / 2
                y = margin
                
                # Add image to the PDF
                pdf.image(img_path, x=x, y=y, w=new_width, h=new_height)
                
                # Extract timestamp and quality from filename
                filename = os.path.basename(img_path)
                parts = filename.replace("screenshot_", "").replace(".png", "").split("_")
                
                # Handle both formats: timestamp_quality and timestamp
                if len(parts) >= 2:
                    timestamp_part = parts[0]
                    quality = parts[-1]
                else:
                    timestamp_part = parts[0]
                    quality = "unknown"
                
                try:
                    # Try parsing with seconds first
                    timestamp = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                except ValueError:
                    try:
                        # Fallback to just date if time parsing fails
                        timestamp = datetime.strptime(timestamp_part, "%Y%m%d")
                    except ValueError:
                        timestamp = datetime.now()
                
                readable_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                pdf.set_font("Arial", size=10)
                pdf.set_xy(x, y + new_height + 5)
                pdf.cell(new_width, 10, f"Screenshot taken: {readable_timestamp} ({quality})", align='C')
            except Exception as e:
                print(f"Error processing image {img_path}: {str(e)}")
                continue
        
        # Save PDF
        pdf.output(pdf_path)
        print(f"PDF created: {pdf_path}")
        return True
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        return False