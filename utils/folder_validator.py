import os

def validate_output_folder(path):
    if not path or not isinstance(path, str):
        return None

    path = os.path.abspath(path)

    # If it doesn't exist, try to create it
    # if not os.path.exists(path):
    #     try:
    #         os.makedirs(path)
    #     except Exception as e:
    #         return False, f"Cannot create folder:\n{e}"

    # Check if it is really a directory
    if not os.path.isdir(path):
        raise TypeError("Given path is not a folder.")

    # Check write permission
    try:
        test_file = os.path.join(path, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except PermissionError:
        raise PermissionError("Folder is not writable:.")

    return path
