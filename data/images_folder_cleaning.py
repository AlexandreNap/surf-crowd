import glob
import os
import shutil
from PIL import Image
import logging


def clean_images(path="images\\spots"):
    logging.info('Started')
    files = [f for f in glob.glob(f"{path}\\*\\*.jpg", recursive=True) if os.path.getsize(f) > 0]
    null_files = [f for f in glob.glob(f"{path}\\*\\*.jpg", recursive=True) if f not in files]
    logging.debug(len(null_files))

    for f in null_files:
        os.remove(f)

    size_files = [os.path.getsize(f) for f in files]

    # get images having exactly the same size then previous image (high chance of being the same image)
    duplicated_idx = []
    previous_size = -1
    for i, size in enumerate(size_files):
        if size == previous_size:
            duplicated_idx.append(i)
        previous_size = size

    logging.debug(duplicated_idx)

    logging.info("Removing duplicates ...")
    logging.debug(len(files))
    for idx in sorted(duplicated_idx, reverse=True):
        os.remove(files[idx])
        del files[idx]
    logging.debug(len(files))

    logging.info("verifying each images and removing bad ones...")
    for filename in files:
        if filename.endswith('.jpg'):
            try:
                img = Image.open(filename)  # open the image file
                img.verify()  # verify that it is, in fact an image
            except (IOError, SyntaxError) as e:
                print(filename)
                os.remove(filename)

    logging.info("Zipping files")
    shutil.make_archive(path, 'zip', path)
    logging.info("Finished")


if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    clean_images("buffer")
