import io
import zipfile
import os


def directory_to_zip(directory, filename):
    zip_file_io = io.BytesIO()
    try:
        zip_file = zipfile.ZipFile(zip_file_io, "w", compression=zipfile.ZIP_DEFLATED)
    except NotImplementedError:
        zip_file = zipfile.ZipFile(zip_file_io, "w")

    for (dirpath, dirnames, filenames) in os.walk(directory):
        basepath = os.path.relpath(dirpath, directory)
        for fname in filenames:
            zip_file.write(os.path.join(dirpath, fname), os.path.join(filename, basepath, fname))
    zip_file.close()
    zip_file_io.seek(0)
    return zip_file_io
