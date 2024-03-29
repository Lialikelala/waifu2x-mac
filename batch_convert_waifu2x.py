import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import logging

# Setup basic logging
logging.basicConfig(filename='waifu2x_error.log', level=logging.ERROR)

def process_image(input_path, output_path, image_type, scale_factor, noise_level):
    try:
        command = [
            'waifu2x', 
            '--type', image_type, 
            '--scale', scale_factor, 
            '--noise', noise_level, 
            '-i', str(input_path), 
            '-o', str(output_path)
        ]
        subprocess.run(command, check=True)
        print(f"Processed: {input_path} -> {output_path}")
    except Exception as e:
        error_msg = f"Error processing {input_path}: {e}"
        print(error_msg)
        logging.error(error_msg)

def main(source_dir, destination_dir=None, max_workers=4, image_type='a', scale_factor='1', noise_level='1'):
    extensions = {".png", ".jpg"}     # Set of extensions to process
    source_path = Path(source_dir)
    dest_path = Path(destination_dir) if destination_dir else source_path.parent / f"{source_path.name}-waifu-ed"

    # Ensure the source directory exists and is a directory
    if not source_path.exists() or not source_path.is_dir():
        print("Source directory does not exist or is not a directory.")
        sys.exit(1)

    # Check for .jpg/.png files before proceeding
    if not any(source_path.rglob("*.[pj][np]g")):  
        print(f"Warning: No .jpg or .png images found in '{source_path}'.")
        sys.exit(1)

    os.makedirs(dest_path, exist_ok=True)

    print(f"Processing images in '{source_dir}'...")

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
       for i, file_path in enumerate(source_path.rglob("*.[pj][np]g"), start=1):
            if file_path.suffix.lower() in extensions:
                relative_path = file_path.relative_to(source_path)
                output_path = dest_path / relative_path.with_suffix(".png")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Pass Waifu2x options to the process_image function
                futures.append(executor.submit(process_image, file_path, output_path, image_type, scale_factor, noise_level))

        # Wait for all futures to complete

    for future in as_completed(futures):
        future.result()  # This will re-raise any exception that occurred in the thread
        print(f"Processed {i} out of {len(futures)} images...", end="\r", flush=True)

    print("\nProcessing complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python3 batch_convert_waifu2x.py <source_directory> [<destination_directory>] [<max_workers>] [--type a|p] [--scale 1|2] [--noise 0-4]")
        print("\nOptions:")
        print("  <source_directory>        Directory containing images to process")
        print("  <destination_directory>   (Optional) Directory where processed images will be saved")
        print("  <max_workers>             (Optional) Number of worker threads to use for processing images")
        print("  --type a|p                Image type: 'a' for anime or 'p' for photo (default: a)")
        print("  --scale 1|2               Scale factor: '1' for no scaling, '2' for double the size (default: 2)")
        print("  --noise 0-4               Noise reduction level: 0 (none) to 4 (maximum) (default: 3)")
        print("\nExample:")
        print("  python3 script.py ./images ./processed_images 4 --type a --scale 2 --noise 2")
        print("Options and examples have been provided for better understanding.\n")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    destination_dir = None
    max_workers = 4  # Default value
    image_type = 'a'  # Default to 'anime'
    scale_factor = '1'  # Default scale
    noise_level = '1'  # Default noise reduction level (0-4)

    # Parse optional command-line arguments
    args = sys.argv[2:]  # Remaining arguments after the script name and source directory
    for i, arg in enumerate(args):
        if "--type" == arg:
            image_type = args[i + 1] if i + 1 < len(args) else image_type
        elif "--scale" == arg:
            scale_factor = args[i + 1] if i + 1 < len(args) else scale_factor
        elif "--noise" == arg:
            noise_level = args[i + 1] if i + 1 < len(args) else noise_level
        elif arg.isdigit() and destination_dir is None:  # First digit argument is max_workers
            max_workers = int(arg)
        elif destination_dir is None:  # First non-flag argument is destination directory
            destination_dir = arg
        elif arg.isdigit():  # Second digit argument (if any) updates max_workers
            max_workers = int(arg)

    if not destination_dir:
        destination_dir = f"{source_dir}-waifu-ed"

    main(source_dir, destination_dir, max_workers, image_type, scale_factor, noise_level)


