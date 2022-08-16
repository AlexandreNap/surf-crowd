import glob
import os
import random
import pandas as pd
import shutil
import re


def subsample_between_dates(date_min, date_max, n_max=200, path="images\\spots"):
    orig_files = [f for f in glob.glob(f"{path}\\*\\*.jpg", recursive=True) if os.path.getsize(f) > 0]
    files = [f.replace(f"{path}\\", "").replace("\\", "__") for f in orig_files]
    directory = f"subsample_from_{date_min}_to_{date_max}"
    data = pd.DataFrame({"spot": [re.sub("__.*", "", f) for f in files],
                         "date": [re.sub(".*__", "", f).replace(".jpg", "") for f in files],
                         "file_path": orig_files,
                         "new_path": [f"{directory}\\{f}" for f in files]})
    data['date'] = pd.to_datetime(data.date, format='%Y-%m-%d_%H-%M')
    data = data[(date_min < data.date) & (data.date < date_max)]
    if len(data) > n_max:
        data = data.sample(n_max)

    if not os.path.exists(directory):
        os.makedirs(directory)
    for path, new_path in zip(data.file_path, data.new_path):
        shutil.copyfile(path, new_path)


if __name__ == "__main__":
    subsample_between_dates("2022-06-01", "2022-07-12")
