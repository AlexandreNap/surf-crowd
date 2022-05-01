from classes_annotation_tool import LabellingApp
from tkinter import Tk
import glob
import os
import random
import pandas as pd


def main():
    paths_list = pd.read_csv("../data/smaller_crops_512x512.csv").image_file.tolist()
    paths_list = ["..\\data\\images_512x512\\" + path for path in paths_list]
    random.shuffle(paths_list)
    print(len(paths_list))

    output_path = "..\\data\\classification_dataset_smaller_crops_512x512.csv"
    # Create our master object to the Application
    master = Tk()
    # Create our application object
    app = LabellingApp(paths_list, output_path, master=master)
    # Start the mainloop
    app.mainloop()


if __name__ == "__main__":
    main()
