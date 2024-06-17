import urllib.parse
import os

def generate_html_dangling_item(file_symlink, is_audio):
    file_name = os.path.basename(file_symlink)
    encoded_file_symlink = urllib.parse.quote(file_name)
    if is_audio:
        return f"<li>{file_name}</li>"
    else:
        return f"<li>{file_name}</li>"

