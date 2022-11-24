import requests

def download(url):
    get_response = requests.get(url)
    file_name = url.split("/")[-1]
    with open("server/compiler/" + file_name, "wb") as out_file:
        out_file.write(get_response.content)
    
base_url = "https://raw.githubusercontent.com/Bergschaf/Pyduino/main/compiler/"
files_to_download = [
    "compiler.py",
    "utils.py",
    "variables.py",
    "error.py",
    "builtin_functions.py",
    "constants.py"]

for file in files_to_download:
    download(base_url + file)
