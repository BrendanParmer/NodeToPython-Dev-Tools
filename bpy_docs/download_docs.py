import os
import urllib.request
import zipfile

def download_and_extract_zip(url, extract_to="."):
    headers_ = {'User-Agent': 'Mozilla/5.0'}

    req = urllib.request.Request(url, headers = headers_)

    with urllib.request.urlopen(req) as response:
        zip_filename = os.path.basename(url)
        with open(zip_filename, 'wb') as zip_file:
            zip_file.write(response.read())

        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            extract_dir = os.path.dirname(extract_to)
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            zip_ref.extractall(extract_to)

        os.remove(zip_filename)

if __name__ == "__main__":
    versions = [(3, i) for i in range(0, 7)]
    versions += [(4, i) for i in range(0, 2)]

    for version in versions:
        url = f"https://docs.blender.org/api/{version[0]}.{version[1]}/blender_python_reference_{version[0]}_{version[1]}.zip"
        bpy_docs_path = os.path.dirname(os.path.realpath(__file__))
        download_and_extract_zip(url, f"{bpy_docs_path}/{version[0]}.{version[1]}/")