#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import subprocess
import os
import sys
import signal
import psutil
import time
import utils
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Active capture process
active_process = None
process_pid = None
capture_thread = None

# Store manual screenshots for inclusion in the final PDF
manual_screenshots = []
temp_dir_for_manual = None

def ensure_temp_dir_exists():
    """Ensure temporary directory exists for manual screenshots"""
    global temp_dir_for_manual
    if not temp_dir_for_manual:
        temp_dir_for_manual = utils.create_temp_directory()
    return temp_dir_for_manual

# A global flag for stopping the capture process
should_stop_capture = False

def run_capture_process(cmd, env):
    """Run the capture process in a way that can be safely terminated"""
    global active_process, process_pid, should_stop_capture
    
    try:
        # Reset the stop flag
        should_stop_capture = False
        
        # Start the process
        proc = subprocess.Popen(cmd, env=env)
        process_pid = proc.pid
        
        # Check for the stop flag at regular intervals
        while proc.poll() is None:  # While process is still running
            if should_stop_capture:
                # Try to send a gentle termination signal
                try:
                    if os.name == 'nt':  # Windows
                        os.kill(process_pid, signal.CTRL_C_EVENT)
                    else:  # macOS, Linux
                        os.kill(process_pid, signal.SIGINT)
                except Exception as e:
                    print(f"Error sending signal to process: {e}")
                
                # Give it some time to terminate gracefully
                time.sleep(2)
                
                # If still running, terminate forcefully
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=3)
                
                break
            
            # Sleep to avoid CPU hogging
            time.sleep(0.5)
        
        # Process completed naturally or was terminated
        print(f"Capture process ended with return code: {proc.returncode}")
    except Exception as e:
        print(f"Error in capture process: {str(e)}")
    finally:
        # Clean up global variables
        active_process = None
        process_pid = None

@app.route('/start_capture', methods=['POST'])
def start_capture():
    global active_process, process_pid, manual_screenshots, temp_dir_for_manual, capture_thread, should_stop_capture
    
    # If a capture is already running, don't start another
    if active_process and active_process.is_alive():
        return jsonify({
            'success': False,
            'message': 'A screenshot capture is already in progress'
        })
    
    # Clear any previous manual screenshots when starting a new capture
    manual_screenshots = []
    
    # Create a new temp directory for manual screenshots if needed
    if temp_dir_for_manual:
        utils.cleanup_temp_directory(temp_dir_for_manual)
    temp_dir_for_manual = ensure_temp_dir_exists()
    
    # Get parameters from request
    data = request.json
    quality = data.get('quality', '720p')
    rate = data.get('rate', 10)
    duration = data.get('duration', 1800)
    output = data.get('output', 'myPDFs')
    name = data.get('name')
    
    # Validate quality parameter
    valid_qualities = ['480p', '720p', '1080p', '2k', '4k']
    if quality not in valid_qualities:
        return jsonify({
            'success': False,
            'message': f'Invalid quality setting. Must be one of: {", ".join(valid_qualities)}'
        })
    
    # Build command for running main.py
    cmd = [sys.executable, os.path.join(script_dir, 'main.py')]
    cmd.extend(['-q', quality])
    cmd.extend(['-r', str(rate)])
    cmd.extend(['-d', str(duration)])
    cmd.extend(['-o', output])
    if name:
        cmd.extend(['-n', name])
    
    # Add environment variable to pass manual screenshots temp directory
    env = os.environ.copy()
    env['MANUAL_SCREENSHOTS_DIR'] = temp_dir_for_manual
    
    # Start screenshot process in a separate thread
    capture_thread = threading.Thread(target=run_capture_process, args=(cmd, env))
    capture_thread.daemon = True  # Make thread a daemon so it exits when main thread exits
    capture_thread.start()
    active_process = capture_thread
    
    return jsonify({
        'success': True,
        'message': 'Screenshot capture started',
        'params': {
            'quality': quality,
            'rate': rate,
            'duration': duration,
            'output': output,
            'name': name
        }
    })

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global active_process, process_pid, temp_dir_for_manual, should_stop_capture
    
    # Get parameters from request for PDF generation
    data = request.json
    output = data.get('output', 'myPDFs')
    name = data.get('name')
    
    if not active_process or not active_process.is_alive():
        return jsonify({
            'success': False,
            'message': 'No screenshot capture is currently running'
        })
    
    try:
        # Set the flag to stop the process
        should_stop_capture = True
        
        # Wait a bit for the process to be signaled to stop
        time.sleep(1)
        
        # Generate PDF from collected screenshots
        if temp_dir_for_manual and os.path.exists(temp_dir_for_manual):
            # Create output directory if it doesn't exist
            if not os.path.exists(output):
                os.makedirs(output)
            
            # Collect all screenshots from the temp directory
            screenshot_files = []
            for file in os.listdir(temp_dir_for_manual):
                if file.startswith("screenshot_") and file.endswith(".png"):
                    screenshot_files.append(os.path.join(temp_dir_for_manual, file))
            
            if screenshot_files:
                # Create PDF filename
                if name:
                    pdf_filename = name if name.endswith('.pdf') else f"{name}.pdf"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = f"screenshots_{timestamp}.pdf"
                
                pdf_path = os.path.join(output, pdf_filename)
                success = utils.create_pdf_with_fpdf(screenshot_files, pdf_path)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Screenshot capture stopped and PDF saved to {pdf_path}',
                        'pdf_path': pdf_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to create PDF'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No screenshots were captured to create a PDF'
                })
        else:
            return jsonify({
                'success': False,
                'message': 'No temporary directory found for screenshots'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping capture: {str(e)}'
        })

@app.route('/manual_screenshot', methods=['POST'])
def manual_screenshot():
    global manual_screenshots, temp_dir_for_manual
    
    # Ensure we have a temp directory
    temp_dir = ensure_temp_dir_exists()
    
    # Get quality parameter
    data = request.json
    quality = data.get('quality', '720p')
    
    # Validate quality parameter
    valid_qualities = ['480p', '720p', '1080p', '2k', '4k']
    if quality not in valid_qualities:
        return jsonify({
            'success': False,
            'message': f'Invalid quality setting. Must be one of: {", ".join(valid_qualities)}'
        })
    
    try:
        # Take a manual screenshot and add it to our list
        filepath = utils.take_screenshot_opencv(temp_dir, quality=quality)
        manual_screenshots.append(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Manual screenshot captured',
            'filepath': filepath,
            'quality': quality
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error capturing manual screenshot: {str(e)}'
        })

@app.route('/status', methods=['GET'])
def status():
    if active_process and active_process.is_alive():
        return jsonify({
            'status': 'active',
            'message': 'Screenshot capture is in progress'
        })
    else:
        return jsonify({
            'status': 'inactive',
            'message': 'No screenshot capture in progress'
        })

@app.route('/recent_directories', methods=['GET'])
def get_recent_directories():
    """Return a list of common directories the user might want to use"""
    common_dirs = []
    
    try:
        # Add user's home directory
        home_dir = os.path.expanduser("~")
        common_dirs.append({
            'path': home_dir,
            'name': 'Home Directory'
        })
        
        # Add Desktop
        desktop_dir = os.path.join(home_dir, 'Desktop')
        if os.path.exists(desktop_dir):
            common_dirs.append({
                'path': desktop_dir,
                'name': 'Desktop'
            })
        
        # Add Documents
        docs_dir = os.path.join(home_dir, 'Documents')
        if os.path.exists(docs_dir):
            common_dirs.append({
                'path': docs_dir,
                'name': 'Documents'
            })
        
        # Add Downloads
        downloads_dir = os.path.join(home_dir, 'Downloads')
        if os.path.exists(downloads_dir):
            common_dirs.append({
                'path': downloads_dir,
                'name': 'Downloads'
            })
        
        # Add the current working directory
        common_dirs.append({
            'path': os.getcwd(),
            'name': 'Current Working Directory'
        })
        
        return jsonify({
            'success': True,
            'directories': common_dirs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting directories: {str(e)}'
        })

@app.route('/create_directory', methods=['POST'])
def create_directory():
    """Create a new directory in a specified path"""
    data = request.json
    parent_path = data.get('parent_path', '')
    new_dir_name = data.get('new_dir_name', '')
    
    if not parent_path or not new_dir_name:
        return jsonify({
            'success': False,
            'message': 'Parent path and directory name are required'
        })
    
    try:
        # Create full path
        new_dir_path = os.path.join(parent_path, new_dir_name)
        
        # Check if directory already exists
        if os.path.exists(new_dir_path):
            return jsonify({
                'success': False,
                'message': 'Directory already exists'
            })
        
        # Create the directory
        os.makedirs(new_dir_path)
        
        return jsonify({
            'success': True,
            'path': new_dir_path,
            'message': f'Directory "{new_dir_name}" created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating directory: {str(e)}'
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)