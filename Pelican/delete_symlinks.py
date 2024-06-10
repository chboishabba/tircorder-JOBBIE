import os

symlink_dir = "output/symlinks"

# Check if the symlink directory exists
if os.path.exists(symlink_dir):
    # List all files in the symlink directory
    for item in os.listdir(symlink_dir):
        item_path = os.path.join(symlink_dir, item)
        # Check if the item is a symlink
        if os.path.islink(item_path):
            print(f"Removing symlink: {item_path}")
            os.unlink(item_path)
else:
    print(f"Directory {symlink_dir} does not exist.")

