import glob
import os
import random
import pandas as pd
import shutil


def main():
    df = pd.read_csv("..\\spot_populated_classification\\data\\classification_dataset.csv")
    df = df[df['class'] == 1.0]
    print(df)
    paths_list = df.path.apply(lambda x: x[8:]).tolist()
    random.shuffle(paths_list)
    print(len(paths_list))
    if not os.path.exists("surf_only_images"):
        os.makedirs("surf_only_images")
    for path in paths_list:
        shutil.copyfile(path, "surf_only_images\\" + path[7:].replace("\\", "_"))


if __name__ == "__main__":
    main()
