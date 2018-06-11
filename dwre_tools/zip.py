from .sync import cartridges_to_zip, collect_cartridges


def zip_command(filename, directory):
    if directory is None:
        directory = '.'

    cartridges = collect_cartridges(directory)
    zip_file = cartridges_to_zip(cartridges, filename)
    zip_file.seek(0)
    with open(f'{filename}.zip', 'wb') as f:
        f.write(zip_file.read())
