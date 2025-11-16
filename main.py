import tkinter as tk
import json
import pickle
from tkinter import ttk, messagebox
import sqlite3

root = tk.Tk()
root.title("Clinic Management")
root.geometry("1000x700")
file = open('New Text Document (2).txt','rb')
pickle.load(file)
file.close()
root.mainloop()