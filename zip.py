import shutil
import os

def zip_folder(folder_path, output_path):
    base_dir = os.path.basename(folder_path)
    parent_dir = os.path.dirname(folder_path)

    shutil.make_archive(output_path, 'zip', parent_dir, base_dir)

    print(f'Folder "{folder_path}" has been zipped as "{output_path}.zip"')

zip_folder('./download', 'download')
