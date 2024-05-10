import os
import json

def generate_json_for_images(directory, output_file):
    # Define the default attributes for each image
    default_attributes = {
        "scale": 0.4,
        "margin": 3,
        "text_scale": 1
    }

    # Dictionary to store the image data
    image_data = {}

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".png"):
                # Construct the file path
                file_path = os.path.join(root, file)
                # Store the attributes for each PNG file
                image_data[file] = default_attributes.copy()

    # Write the dictionary to a JSON file
    with open(output_file, "w") as json_file:
        json.dump(image_data, json_file, indent=4)

    print(f"JSON file '{output_file}' has been created with image attributes.")

# Example usage
directory_path = '/home/c/Documents/BROWN, John - Chart as Images'  # Replace with the path to your directory
output_json_file = 'output.json'           # Name of the JSON file to create
generate_json_for_images(directory_path, output_json_file)

