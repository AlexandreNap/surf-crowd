import os
from tkinter import *
from PIL import Image, ImageTk
import pandas as pd
import time


class LabellingApp(Frame):
    def __init__(self, paths_list, output_path, continue_labelling=True, master=None):
        super().__init__(master)
        self.master = master
        self.output_path = output_path
        if os.path.exists(self.output_path) and continue_labelling:
            self.df = pd.read_csv(self.output_path)
        else:
            self.df = pd.DataFrame({"path": [],
                                    "class": []})

        self.paths_list = [path for path in paths_list if path not in self.df.path.tolist()]
        self.current_list_index = -1

        self.annotated_this_session = 0
        self.total_annotated = self.df.shape[0]
        self.remaining_to_annotate = len(self.paths_list)
        self.total_to_annotate = self.total_annotated + self.remaining_to_annotate
        self.start_time = time.time()
        self.session_time = 0

        # setting up a tkinter canvas
        self.width = 1600
        self.height = 800
        self.w = Canvas(self.master, width=self.width, height=self.height)
        self.w.pack()

        self.current_path = None
        self.image = None
        self.annotation_stats = None
        self.current_annotation = None

        self.w.bind("<Button 1>", self.positive_result)
        self.w.bind("<Button 3>", self.negative_result)
        self.w.bind("<space>", self.positive_result2)
        self.w.bind("f", self.negative_result2)
        self.positive_button = Button(self.master, text="There is at least a surfer\nleft_click\nspace_bar key",
                                      command=self.positive_result)
        self.positive_button.pack()
        self.positive_button.place(relx=0., rely=1., anchor=SW)

        self.negative_button = Button(self.master, text="There is no surfer\nright click\nf key",
                                      command=self.negative_result)
        self.negative_button.pack()
        self.negative_button.place(relx=0.09, rely=1., anchor=SW)

        self.quit_button = Button(self.master, text="Quit",
                                  command=self.save_and_quit)
        self.quit_button.pack()
        self.quit_button.place(relx=0.16, rely=1., anchor=SW)

        self.new_image()

    def show_image(self):
        file_path = self.current_path
        try:
            original = Image.open(file_path)
        except Exception:
            print(Exception)
            self.update_annotation_stats()
            return -1
        else:
            original = original.resize((self.width, self.height))  # resize image
            self.image = ImageTk.PhotoImage(master=self.master, image=original)
            self.w.create_image(0, 0, image=self.image, anchor="nw")
            return 0

    def update_annotation_stats(self):
        self.annotated_this_session += 1
        self.total_annotated += 1
        self.remaining_to_annotate -= 1
        self.session_time = time.time() - self.start_time

    def show_annotation_stats(self):
        if hasattr(self, 'annotation_stats'):
            self.w.delete(self.annotation_stats)
        self.annotation_stats = self.w.create_text(10, 10,
                                                   text=f"Annotated this session : {self.annotated_this_session}\n"
                                                   f"Remaining_to_annotate : {self.remaining_to_annotate}\n"
                                                   f"Session time : {self.session_time}\n"
                                                   f"Mean annotation duration : "
                                                   f"{(self.session_time/self.annotated_this_session):.2f}",
                                                   fill="black", font='Helvetica 15 bold', anchor='nw')

    def new_image(self):
        self.current_list_index += 1
        if self.current_list_index < len(self.paths_list):
            self.current_path = self.paths_list[self.current_list_index]
            if self.show_image() != -1:
                if self.annotated_this_session != 0:
                    self.show_annotation_stats()
            else:
                self.new_image()
        else:
            self.master.destroy()

    def positive_result(self, event):
        self.current_annotation = 1
        self.annotate()
        self.update_annotation_stats()
        self.new_image()

    def negative_result(self, event):
        self.current_annotation = 0
        self.update_annotation_stats()
        self.annotate()
        self.new_image()

    def positive_result2(self):
        self.current_annotation = 1
        self.annotate()
        self.update_annotation_stats()
        self.new_image()

    def negative_result2(self):
        self.current_annotation = 0
        self.update_annotation_stats()
        self.annotate()
        self.new_image()

    def annotate(self):
        self.df = pd.concat([self.df, pd.DataFrame([{'path': self.current_path,
                                                     'class': self.current_annotation
                                                     }])], ignore_index=True)

    def save_res(self):
        self.df.to_csv(self.output_path, index=False)

    def save_and_quit(self):
        self.save_res()
        self.master.destroy()
