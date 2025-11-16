# Store Management Desktop App (single-file)
# Features:
# - SQLite database for items (insert, update, delete, fetch)
# - Tkinter GUI with separate windows for Add/Edit/View
# - Generate PDF report when item is saved (ReportLab)
# - Send email with the generated PDF attached (smtplib + EmailMessage)

# IMPORTANT:
# - Fill your SMTP settings in the SEND_EMAIL_CONFIG dictionary below.
# - Install required packages: reportlab
#   pip install reportlab

# How to run:
# 1. Save this file as store_app.py inside your project folder.
# 2. (Optional) Create a virtualenv and activate it.
# 3. pip install reportlab
# 4. python store_app.py

# This is a minimal, ready-to-run example. Customize UI, DB fields, styling, and email behavior as needed.

# Author: Generated for user request

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdfcanvas
import smtplib
from email.message import EmailMessage
import mimetypes

# --------------------- Configuration ---------------------
DB_FILENAME = 'store.db'
PDF_FOLDER = 'reports'

# Configure your SMTP settings here
SEND_EMAIL_CONFIG = {
    'smtp_server': 'smtp.example.com',
    'smtp_port': 587,
    'username': 'your_email@example.com',
    'password': 'your_email_password',
    'from_email': 'your_email@example.com',
    # default recipient, can be changed at runtime
    'to_email': 'recipient@example.com'
}

# Create folders if missing
os.makedirs(PDF_FOLDER, exist_ok=True)

# --------------------- Database functions ---------------------
def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        price REAL DEFAULT 0.0,
        description TEXT,
        created_at TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        father TEXT NOT NULL,
        cnic TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    ''')
    ccur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            product_code TEXT,
            product_price REAL,
            product_profit REAL,
            product_total REAL,
            sale_date TEXT,
            saler_name TEXT,
            saler_cnic TEXT
    )
    """)
    conn.commit()
    conn.close()


def insert_item(name, quantity, price, description):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('''INSERT INTO items (name, quantity, price, description, created_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (name, quantity, price, description, datetime.now().isoformat()))
    conn.commit()
    item_id = cur.lastrowid
    conn.close()
    return item_id


def update_item(item_id, name, quantity, price, description):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('''UPDATE items SET name=?, quantity=?, price=?, description=? WHERE id=?''',
                (name, quantity, price, description, item_id))
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()


def fetch_all_items():
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, quantity, price, description, created_at FROM items ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_item(item_id):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('SELECT id, name, quantity, price, description, created_at FROM items WHERE id=?', (item_id,))
    row = cur.fetchone()
    conn.close()
    return row

# --------------------- PDF generation ---------------------

def generate_pdf_for_item(item):
    # item is a tuple (id, name, quantity, price, description, created_at)
    item_id, name, quantity, price, description, created_at = item
    filename = f"item_{item_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(PDF_FOLDER, filename)

    c = pdfcanvas.Canvas(path, pagesize=A4)
    w, h = A4
    margin = 50
    y = h - margin

    c.setFont('Helvetica-Bold', 16)
    c.drawString(margin, y, f"Item Report — ID: {item_id}")
    y -= 30

    c.setFont('Helvetica', 12)
    c.drawString(margin, y, f"Name: {name}")
    y -= 20
    c.drawString(margin, y, f"Quantity: {quantity}")
    y -= 20
    c.drawString(margin, y, f"Price: {price}")
    y -= 20
    c.drawString(margin, y, f"Created at: {created_at}")
    y -= 30

    c.setFont('Helvetica', 11)
    c.drawString(margin, y, "Description:")
    y -= 16

    text_obj = c.beginText(margin, y)
    text_obj.setFont('Helvetica', 10)
    if description:
        for line in description.split('\n'):
            text_obj.textLine(line)
    else:
        text_obj.textLine('(No description)')
    c.drawText(text_obj)

    c.showPage()
    c.save()
    return path

# --------------------- Email sending ---------------------

def send_email_with_attachment(to_email, subject, body, attachment_path, config=SEND_EMAIL_CONFIG):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = config['from_email']
        msg['To'] = to_email
        msg.set_content(body)

        # attach file
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(attachment_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(attachment_path))

        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
        return True, ''
    except Exception as e:
        return False, str(e)

# --------------------- GUI ---------------------

class StoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Store Management')
        self.geometry('800x500')

        # Top buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=8)

        tk.Button(btn_frame, text='Add Item', command=self.open_add_window).pack(side='left')
        tk.Button(btn_frame, text='Edit Selected', command=self.open_edit_window).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Delete Selected', command=self.delete_selected).pack(side='left', padx=6)
        tk.Button(btn_frame, text='View Selected', command=self.open_view_window).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Refresh', command=self.refresh_tree).pack(side='left', padx=6)
        tk.Button(btn_frame, text='User Management', command=self.open_user_panel, bg="#9C27B0", fg="white").pack(side='left', padx=6)
        tk.Button(btn_frame, text='Sale Panel', command=self.open_sale_panel, bg="#2196F3", fg="white").pack(side='left', padx=6)
        tk.Button(btn_frame, text='Logout', command=self.logout, bg='#f44336', fg='white').pack(side='right')

        # Search
        search_frame = tk.Frame(self)
        search_frame.pack(fill='x', padx=10)
        tk.Label(search_frame, text='Search:').pack(side='left')
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var).pack(side='left', fill='x', expand=True, padx=6)
        tk.Button(search_frame, text='Go', command=self.search_items).pack(side='left')

        # Treeview for items
        cols = ('id', 'name', 'quantity', 'price', 'created_at')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Name')
        self.tree.heading('quantity', text='Quantity')
        self.tree.heading('price', text='Price')
        self.tree.heading('created_at', text='Created At')
        self.tree.column('id', width=50)
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.refresh_tree()

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = fetch_all_items()
        for r in rows:
            self.tree.insert('', 'end', values=(r[0], r[1], r[2], r[3], r[5]))

    def search_items(self):
        q = self.search_var.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = fetch_all_items()
        for r in rows:
            if q == '' or q in str(r[1]).lower() or q in str(r[4] or '').lower():
                self.tree.insert('', 'end', values=(r[0], r[1], r[2], r[3], r[5]))

    def get_selected_item_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def open_add_window(self):
        ItemWindow(self, mode='add')

    def open_edit_window(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            messagebox.showwarning('Select', 'Please select an item first')
            return
        ItemWindow(self, mode='edit', item_id=item_id)

    def open_view_window(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            messagebox.showwarning('Select', 'Please select an item first')
            return
        ViewWindow(self, item_id)

    def delete_selected(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            messagebox.showwarning('Select', 'Please select an item first')
            return
        if messagebox.askyesno('Confirm', 'Are you sure you want to delete the selected item?'):
            delete_item(item_id)
            self.refresh_tree()
            messagebox.showinfo('Deleted', 'Item deleted')

    def open_user_panel(self):
        UserWindow(self)

    def open_sale_panel(self):
        SaleWindow(self)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()  # main window close
            login = LoginWindow()
            login.mainloop()



# --------------------- Sale Panel ---------------------

class SaleWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sales Management")
        self.geometry("1000x600")
        self.conn = sqlite3.connect(DB_FILENAME)
        self.selected_id = None

        # GUI
        self.create_widgets()
        self.load_data()


    def create_widgets(self):
        # -------- Search Entry --------
        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(search_frame, text="Go", command=self.search_sales).pack(side="left", padx=5)
        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(side="left", padx=5)

        # -------- Form Frame --------
        form_frame = tk.Frame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        labels = ["Product ID","Product Code","Price","Profit","Total","Saler Name","Saler CNIC"]
        self.entries = {}
        for i, lbl in enumerate(labels):
            tk.Label(form_frame, text=lbl).grid(row=0, column=i, padx=5)
            entry = tk.Entry(form_frame, width=12)
            entry.grid(row=1, column=i, padx=5)
            self.entries[lbl] = entry

        # -------- Buttons --------
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="Add Sale", bg="#4CAF50", fg="white", command=self.add_sale).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update", bg="#2196F3", fg="white", command=self.update_sale).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#f44336", fg="white", command=self.delete_sale).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)

        # -------- Treeview --------
        cols = ("id","product_id","product_code","product_price","product_profit","product_total","sale_date","saler_name","saler_cnic")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        for col in cols:
            self.tree.heading(col, text=col.replace("_"," ").title())
            self.tree.column(col, width=100)
        self.tree.bind("<ButtonRelease-1>", self.select_row)

    # ---------- CRUD ----------
    def add_sale(self):
        vals = [self.entries[key].get().strip() for key in self.entries]
        if not vals[0] or not vals[1]:
            messagebox.showwarning("Validation", "Product ID and Product Code required")
            return
        try:
            price = float(vals[2])
            profit = float(vals[3])
            total = float(vals[4])
        except:
            messagebox.showwarning("Validation", "Price, Profit, Total must be numbers")
            return
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO sales (product_id, product_code, product_price, product_profit, product_total, sale_date, saler_name, saler_cnic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (vals[0], vals[1], price, profit, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), vals[5], vals[6]))
        self.conn.commit()
        self.load_data()
        self.clear_entries()

    def update_sale(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a row to update")
            return
        vals = [self.entries[key].get().strip() for key in self.entries]
        try:
            price = float(vals[2])
            profit = float(vals[3])
            total = float(vals[4])
        except:
            messagebox.showwarning("Validation", "Price, Profit, Total must be numbers")
            return
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE sales SET product_id=?, product_code=?, product_price=?, product_profit=?, product_total=?, saler_name=?, saler_cnic=?
            WHERE id=?
        """, (vals[0], vals[1], price, profit, total, vals[5], vals[6], self.selected_id))
        self.conn.commit()
        self.load_data()
        self.clear_entries()

    def delete_sale(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a row to delete")
            return
        if messagebox.askyesno("Confirm", "Delete selected sale?"):
            cur = self.conn.cursor()
            cur.execute("DELETE FROM sales WHERE id=?", (self.selected_id,))
            self.conn.commit()
            self.load_data()
            self.clear_entries()

    # ---------- Treeview ----------
    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM sales ORDER BY id DESC")
        for row in cur.fetchall():
            self.tree.insert("", tk.END, values=row)
        self.selected_id = None

    def select_row(self, event):
        try:
            selected = self.tree.item(self.tree.selection()[0], "values")
            keys = list(self.entries.keys())

            for i, key in enumerate(keys):
                self.entries[key].delete(0, "end")
            if i < len(selected):
                self.entries[key].insert(0, selected[i])
        except Exception as e:
            print("Select row error:", e)


    # ---------- Search ----------
    def search_sales(self):
        q = self.search_var.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM sales ORDER BY id DESC")
        for row in cur.fetchall():
            # search all fields except id
            if q == "" or any(q in str(f).lower() for f in row[1:]):
                self.tree.insert("", tk.END, values=row)

    def clear_search(self):
        self.search_var.set("")
        self.load_data()

    def clear_entries(self):
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.selected_id = None

# --------------------- User Management Panel ---------------------

class UserWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("User Management Panel")
        self.geometry("800x500")
        self.parent = parent

        # --- Search Bar ---
        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(search_frame, text="Search User:").pack(side="left")
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        tk.Button(search_frame, text="Search", command=self.search_user).pack(side="left", padx=5)
        tk.Button(search_frame, text="Refresh", command=self.refresh_table).pack(side="left")

        # --- Table ---
        cols = ("id", "name", "father", "cnic", "password", "created_at")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=100)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Buttons ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="Add User", command=self.add_user, bg="#4CAF50", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit User", command=self.edit_user, bg="#2196F3", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete User", command=self.delete_user, bg="#f44336", fg="white").pack(side="left", padx=5)

        self.refresh_table()

    def refresh_table(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = sqlite3.connect(DB_FILENAME)
        cur = conn.cursor()
        cur.execute("SELECT id, name, father, cnic, password, created_at FROM user ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def search_user(self):
        query = self.search_var.get().strip().lower()
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = sqlite3.connect(DB_FILENAME)
        cur = conn.cursor()
        cur.execute("SELECT id, name, father, cnic, password, created_at FROM user")
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            if (query in str(row[1]).lower() or query in str(row[2]).lower() or
                query in str(row[3]).lower() or query in str(row[4]).lower() or query in str(row[5]).lower()):
                self.tree.insert("", "end", values=row)

    def get_selected_user_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a user first")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def add_user(self):
        UserForm(self, mode="add")

    def edit_user(self):
        uid = self.get_selected_user_id()
        if uid:
            UserForm(self, mode="edit", user_id=uid)

    def delete_user(self):
        uid = self.get_selected_user_id()
        if not uid:
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this user?"):
            conn = sqlite3.connect(DB_FILENAME)
            cur = conn.cursor()
            cur.execute("DELETE FROM user WHERE id=?", (uid,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Deleted", "User deleted successfully")
            self.refresh_table()


class UserForm(tk.Toplevel):
    def __init__(self, parent, mode="add", user_id=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.user_id = user_id
        self.title("Add User" if mode=="add" else "Edit User")
        self.geometry("400x400")

        tk.Label(self, text="Name").pack(anchor="w", padx=10, pady=(10,0))
        self.name_var = tk.StringVar()
        tk.Entry(self, textvariable=self.name_var).pack(fill="x", padx=10)

        tk.Label(self, text="Father Name").pack(anchor="w", padx=10, pady=(10,0))
        self.father_var = tk.StringVar()
        tk.Entry(self, textvariable=self.father_var).pack(fill="x", padx=10)

        tk.Label(self, text="CNIC").pack(anchor="w", padx=10, pady=(10,0))
        self.cnic_var = tk.StringVar()
        tk.Entry(self, textvariable=self.cnic_var).pack(fill="x", padx=10)

        tk.Label(self, text="Password").pack(anchor="w", padx=10, pady=(10,0))
        self.password_var = tk.StringVar()
        tk.Entry(self, textvariable=self.password_var, show="*").pack(fill="x", padx=10)

        tk.Button(self, text="Save", command=self.save_user, bg="#4CAF50", fg="white").pack(pady=10)
        tk.Button(self, text="Cancel", command=self.destroy).pack()

        if self.mode == "edit" and self.user_id:
            self.load_user()

    def load_user(self):
        conn = sqlite3.connect(DB_FILENAME)
        cur = conn.cursor()
        cur.execute("SELECT name, father, cnic, password FROM user WHERE id=?", (self.user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            self.name_var.set(row[0])
            self.father_var.set(row[1])
            self.cnic_var.set(row[2])
            self.password_var.set(row[3])

    def save_user(self):
        name = self.name_var.get().strip()
        father = self.father_var.get().strip()
        cnic = self.cnic_var.get().strip()
        password = self.password_var.get().strip()
        if not name or not password:
            messagebox.showwarning("Validation", "Name and Password are required")
            return
        conn = sqlite3.connect(DB_FILENAME)
        cur = conn.cursor()
        if self.mode == "add":
            cur.execute("INSERT INTO user (name, father, cnic, password, created_at) VALUES (?, ?, ?, ?, ?)",
                        (name, father, cnic, password, datetime.now().isoformat()))
        else:
            cur.execute("UPDATE user SET name=?, father=?, cnic=?, password=? WHERE id=?",
                        (name, father, cnic, password, self.user_id))
        conn.commit()
        conn.close()
        self.parent.refresh_table()
        self.destroy()
        messagebox.showinfo("Success", f"User {'added' if self.mode=='add' else 'updated'} successfully")



class ItemWindow(tk.Toplevel):
    def __init__(self, parent, mode='add', item_id=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.item_id = item_id
        self.title('Add Item' if mode=='add' else 'Edit Item')
        self.geometry('400x350')

        tk.Label(self, text='Name').pack(anchor='w', padx=10, pady=(10,0))
        self.name_var = tk.StringVar()
        tk.Entry(self, textvariable=self.name_var).pack(fill='x', padx=10)

        tk.Label(self, text='Quantity').pack(anchor='w', padx=10, pady=(10,0))
        self.qty_var = tk.IntVar(value=0)
        tk.Entry(self, textvariable=self.qty_var).pack(fill='x', padx=10)

        tk.Label(self, text='Price').pack(anchor='w', padx=10, pady=(10,0))
        self.price_var = tk.DoubleVar(value=0.0)
        tk.Entry(self, textvariable=self.price_var).pack(fill='x', padx=10)

        tk.Label(self, text='Description').pack(anchor='w', padx=10, pady=(10,0))
        self.desc_txt = tk.Text(self, height=5)
        self.desc_txt.pack(fill='both', padx=10, pady=(0,10))

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=6)
        tk.Button(btn_frame, text='Save', command=self.save).pack(side='left')
        tk.Button(btn_frame, text='Cancel', command=self.destroy).pack(side='left', padx=6)

        if mode == 'edit' and item_id:
            self.load_item()

    def load_item(self):
        row = fetch_item(self.item_id)
        if row:
            _, name, quantity, price, description, _ = row
            self.name_var.set(name)
            self.qty_var.set(quantity)
            self.price_var.set(price)
            self.desc_txt.delete('1.0', 'end')
            self.desc_txt.insert('1.0', description or '')

    def save(self):
        name = self.name_var.get().strip()
        try:
            quantity = int(self.qty_var.get())
        except Exception:
            quantity = 0
        try:
            price = float(self.price_var.get())
        except Exception:
            price = 0.0
        description = self.desc_txt.get('1.0', 'end').strip()

        if not name:
            messagebox.showwarning('Validation', 'Name is required')
            return

        if self.mode == 'add':
            new_id = insert_item(name, quantity, price, description)
            messagebox.showinfo('Saved', f'Item saved with ID {new_id}')
            # generate pdf
            item = fetch_item(new_id)
            pdf_path = generate_pdf_for_item(item)
            # ask for recipient
            to_email = simpledialog.askstring('Email', 'Enter recipient email to send report (leave blank to skip):', parent=self)
            if to_email:
                ok, err = send_email_with_attachment(to_email, f'Item Report - {name}', 'Attached the item report', pdf_path)
                if ok:
                    messagebox.showinfo('Email', 'Report sent successfully')
                else:
                    messagebox.showerror('Email Error', f'Failed to send email: {err}')

        else:
            update_item(self.item_id, name, quantity, price, description)
            messagebox.showinfo('Updated', 'Item updated')
            item = fetch_item(self.item_id)
            pdf_path = generate_pdf_for_item(item)
            to_email = simpledialog.askstring('Email', 'Enter recipient email to send report (leave blank to skip):', parent=self)
            if to_email:
                ok, err = send_email_with_attachment(to_email, f'Item Report - {name}', 'Attached the item report', pdf_path)
                if ok:
                    messagebox.showinfo('Email', 'Report sent successfully')
                else:
                    messagebox.showerror('Email Error', f'Failed to send email: {err}')

        self.parent.refresh_tree()
        self.destroy()


class ViewWindow(tk.Toplevel):
    def __init__(self, parent, item_id):
        super().__init__(parent)
        self.item_id = item_id
        self.title('View Item')
        self.geometry('450x350')
        row = fetch_item(item_id)
        if not row:
            tk.Label(self, text='Item not found').pack(padx=10, pady=10)
            return
        _, name, quantity, price, description, created_at = row

        tk.Label(self, text=f'Name: {name}', anchor='w').pack(fill='x', padx=10, pady=(10,0))
        tk.Label(self, text=f'Quantity: {quantity}', anchor='w').pack(fill='x', padx=10)
        tk.Label(self, text=f'Price: {price}', anchor='w').pack(fill='x', padx=10)
        tk.Label(self, text=f'Created at: {created_at}', anchor='w').pack(fill='x', padx=10, pady=(0,10))

        tk.Label(self, text='Description:', anchor='w').pack(fill='x', padx=10)
        txt = tk.Text(self, height=8)
        txt.pack(fill='both', padx=10, pady=(0,10))
        txt.insert('1.0', description or '')
        txt.config(state='disabled')

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=6)
        tk.Button(btn_frame, text='Generate PDF', command=lambda: self.gen_pdf(row)).pack(side='left')
        tk.Button(btn_frame, text='Send Email', command=lambda: self.ask_and_send(row)).pack(side='left', padx=6)

    def gen_pdf(self, row):
        path = generate_pdf_for_item(row)
        messagebox.showinfo('PDF', f'PDF generated: {path}')

    def ask_and_send(self, row):
        path = generate_pdf_for_item(row)
        to_email = simpledialog.askstring('Email', 'Enter recipient email to send report (leave blank to cancel):', parent=self)
        if to_email:
            ok, err = send_email_with_attachment(to_email, f'Item Report - {row[1]}', 'Attached the item report', path)
            if ok:
                messagebox.showinfo('Email', 'Report sent successfully')
            else:
                messagebox.showerror('Email Error', f'Failed to send email: {err}')

# GUI Classes with icons
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Login')
        self.geometry('350x250')
        self.configure(bg='white')

        # Logo (optional)
        ICON_FOLDER = os.path.join(os.getcwd(), 'icons')
        logo_path = os.path.join(ICON_FOLDER, 'app_logo.png')
        if os.path.exists(logo_path):
            logo_img = tk.PhotoImage(file=logo_path)
            tk.Label(self, image=logo_img, bg='white').pack(pady=10)
            self.logo_img = logo_img  # keep reference

        tk.Label(self, text='Username', bg='white').pack(pady=5)
        self.username = tk.Entry(self)
        self.username.pack(pady=5)

        tk.Label(self, text='Password', bg='white').pack(pady=5)
        self.password = tk.Entry(self, show='*')
        self.password.pack(pady=5)

        tk.Button(self, text='Login', command=self.check_login,
                  bg='#4CAF50', fg='white').pack(pady=10)

    def check_login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()

        # simple demo login (you can connect it to your DB)
        if u == "admin" and p == "1234":
            messagebox.showinfo("Success", "Login successful!")
            self.destroy()
            app = StoreApp()
            app.mainloop()
        else:
            messagebox.showerror("Error", "Invalid username or password")


def check_login(self):
    u = self.username.get()
    p = self.password.get()
    if verify_user(u, p):
        self.destroy()
        app = StoreApp()
        app.mainloop()
    else:
        messagebox.showerror('Error', 'Invalid credentials')


# --------------------- Run ---------------------

if __name__ == '__main__':
    init_db()
    app = LoginWindow()
    # app = StoreApp()
    app.mainloop()