import io
import zipfile
import os


def directory_to_zip(directory, filename):
    zip_file_io = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_file_io, "w")

    for (dirpath, dirnames, filenames) in os.walk(directory):
        if directory[-1] == "/" or directory[-1] == "\\":
            offset = 0
        else:
            offset = 1
        basepath = dirpath[len(directory)+offset:]
        for fname in filenames:
            zip_file.write(os.path.join(dirpath, fname), os.path.join(filename, basepath, fname))
    zip_file.close()
    return zip_file_io
