import uuid
from smbprotocol.connection import Connection, Dialects
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol import Open, CreateDisposition, CreateOptions, FileAccessMask, FileAttributes, DirectoryAccessMask

server = "desktop-hg6qb3n"
username = "a"
password = "a"
share_name = "Y"  # Make sure the share name does not include the '$' if it is a regular share

# Set up the connection
connection = Connection(uuid.uuid4(), server, 445)
connection.connect(Dialects.SMB_3_1_1)  # Using SMB 3.1.1 dialect for the connection

# Start a session
session = Session(connection, username, password)
session.connect()

# Connect to the tree
tree = TreeConnect(session, f"\\\\{server}\\{share_name}")
tree.connect()

# Define the path to the directory on the share
path = "/__MEDIA/__Transcribing and Recording/2024/Dad Auto Transcriber"  # Adjust path as needed

# Open the directory
directory = Open(tree, path)
directory.create(
    desired_access=DirectoryAccessMask.FILE_LIST_DIRECTORY,
    create_options=CreateOptions.FILE_DIRECTORY_FILE,
    create_disposition=CreateDisposition.FILE_OPEN
)

# List files in the directory
for file_info in directory.query_directory("*"):
    print(file_info.filename)

