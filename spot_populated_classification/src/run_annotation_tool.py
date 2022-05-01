from classes_annotation_tool import LabellingApp
from tkinter import Tk
import glob
import os
import random


def main():
    path = '../data/images/spots'
    paths_list = [f for f in glob.glob("..\\data\\images\\spots\\*\\*.jpg", recursive=True) if os.path.getsize(f) > 0]
    random.shuffle(paths_list)
    print(len(paths_list))

    output_path = "data\\classification_dataset.csv"
    # Create our master object to the Application
    master = Tk()
    # Create our application object
    app = LabellingApp(paths_list, output_path, master=master)
    # Start the mainloop
    app.mainloop()


if __name__ == "__main__":
    main()
