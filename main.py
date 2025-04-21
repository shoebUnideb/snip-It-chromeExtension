#!/usr/bin/env python3
import argparse
import os
import time
import glob
from datetime import datetime
import utils

def main():
    parser = argparse.ArgumentParser(description='Take periodic screenshots using OpenCV and save them to a PDF only')
    parser.add_argument('-q', '--quality', type=str, default='720p',
                        help='Screenshot quality (480p, 720p, 1080p, 2k, 4k) (default: 720p)')
    parser.add_argument('-r', '--rate', type=int, default=10, 
                        help='Screenshot interval in seconds (default: 10)')
    parser.add_argument('-d', '--duration', type=int, default=1800,
                        help='Total duration in seconds (default: 1800, i.e., 30 minutes)')
    parser.add_argument('-o', '--output', type=str, default='myPDFs',
                        help='Output directory for PDF file (default: myPDFs directory)')
    parser.add_argument('-n', '--name', type=str, default=None,
                        help='Custom name for the PDF file (default: screenshots_TIMESTAMP.pdf)')
    args = parser.parse_args()
    
    # Validate quality parameter
    valid_qualities = ['480p', '720p', '1080p', '2k', '4k']
    if args.quality not in valid_qualities:
        print(f"Error: Invalid quality setting. Must be one of: {', '.join(valid_qualities)}")
        return
    
    # Create output folder if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Create a temporary directory for screenshots
    temp_dir = utils.create_temp_directory()
    print(f"Using temporary directory for screenshots: {temp_dir}")
    
    # Check for manual screenshots directory from environment variable
    manual_screenshots_dir = os.environ.get('MANUAL_SCREENSHOTS_DIR')
    
    # Calculate number of screenshots to take
    num_screenshots = args.duration // args.rate
    
    print(f"Starting screenshot capture with quality: {args.quality}")
    print(f"Capture settings: {num_screenshots} screenshots at {args.rate} second intervals")
    print(f"Total duration: {args.duration} seconds ({args.duration/60:.1f} minutes)")
    print(f"Output PDF will be saved to: {args.output}")
    if manual_screenshots_dir:
        print(f"Manual screenshots will be included from: {manual_screenshots_dir}")
    print("Press Ctrl+C to stop the capture early")
    
    screenshot_files = []
    capture_interrupted = False
    
    try:
        # Take initial screenshot
        filepath = utils.take_screenshot_opencv(temp_dir, quality=args.quality)
        if filepath:
            screenshot_files.append(filepath)
        
        # Take remaining screenshots at the specified interval
        for i in range(1, num_screenshots):
            try:
                time.sleep(args.rate)
                filepath = utils.take_screenshot_opencv(temp_dir, quality=args.quality)
                if filepath:
                    screenshot_files.append(filepath)
                
                # Display progress
                print(f"Progress: {i+1}/{num_screenshots} screenshots captured")
            except KeyboardInterrupt:
                capture_interrupted = True
                break
            except Exception as e:
                print(f"Error during capture: {str(e)}")
                continue
    
    except KeyboardInterrupt:
        capture_interrupted = True
        print("\nScreenshot capture interrupted by user")
    except Exception as e:
        print(f"\nError during capture: {str(e)}")
    
    # Collect manual screenshots if available
    manual_files = []
    if manual_screenshots_dir and os.path.exists(manual_screenshots_dir):
        manual_files = glob.glob(os.path.join(manual_screenshots_dir, "screenshot_*.png"))
        if manual_files:
            print(f"Found {len(manual_files)} manual screenshots to include in PDF")
    
    # Combine automatic and manual screenshots
    all_screenshots = screenshot_files + manual_files
    
    # Create PDF from captured screenshots
    if all_screenshots:
        # Create PDF filename
        if args.name:
            pdf_filename = args.name if args.name.endswith('.pdf') else f"{args.name}.pdf"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"screenshots_{timestamp}.pdf"
        
        pdf_path = os.path.join(args.output, pdf_filename)
        success = utils.create_pdf_with_fpdf(all_screenshots, pdf_path)
        
        if success:
            print(f"PDF saved to: {os.path.abspath(pdf_path)}")
            print(f"Total screenshots in PDF: {len(all_screenshots)} ({len(screenshot_files)} automatic, {len(manual_files)} manual)")
        else:
            print("Failed to create PDF")
    else:
        print("No screenshots were taken, no PDF created.")
    
    # Clean up - remove temporary directory and all screenshots
    print("Cleaning up temporary files...")
    utils.cleanup_temp_directory(temp_dir)
    print("Cleanup complete.")

if __name__ == "__main__":
    main()