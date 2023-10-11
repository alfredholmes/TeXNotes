import os
from pathlib import Path

def get_files(dir_name, extension=""):
    files = list(Path(dir_name).rglob(f"*{extension}"))
    files = [f for f in files if '/.' not in str(f)]
    return files

def get_rendered_dates(extension='pdf', files=None):
    if files is None:
        files = get_files('notes', '.tex')

    files = [f'{str(f)[:-4]}.{extension}' for f in files]
    pdfs = [extension + '/' + 'notes/'.join(str(f).split('notes/')[1:]) for f in files]
    dates = {pdf: os.path.getmtime(pdf) for pdf in pdfs}
    print(dates)
    


