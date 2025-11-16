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
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas as pdfcanvas
import smtplib
from email.message import EmailMessage
import mimetypes

# --------------------- Configuration ---------------------
ICON_FOLDER = 'icons'
PDF_FOLDER = 'reports'
DB_FILENAME = 'store.db'

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
    # New Table : Items
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
    # New Table : Users
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
    # New Table : Sales
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            product_code TEXT,
            product_price REAL,
            product_profit REAL,
            product_total REAL,
            client_name TEXT
            client_cnic TEXT
            sale_date TEXT
    )
    """)
     # New table : store details
    cur.execute("""
        CREATE TABLE IF NOT EXISTS store_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            address TEXT,
            email TEXT,
            contact TEXT,
            created_at TEXT
    )""")
    # New table : purchase
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_code TEXT,
            quantity INTEGER DEFAULT 0,
            purchase_price REAL DEFAULT 0.0,
            total_price REAL DEFAULT 0.0,
            supplier_name TEXT,
            supplier_contact TEXT,
            purchase_date TEXT
        )
    """)
        # New Table : User Privileges
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_privileges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            can_view_sales INTEGER DEFAULT 0,
            can_edit_sales INTEGER DEFAULT 0,
            can_view_purchase INTEGER DEFAULT 0,
            can_edit_purchase INTEGER DEFAULT 0,
            can_manage_users INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')


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
    def __init__(self, user_id):
        super().__init__()
        self.title('🛒 Store Management')
        self.geometry('800x500')
        self.configure(bg="#F5F5F5")
        self.user_id = user_id

        # fetch privileges
        self.privileges = self.load_privileges()

        # Top buttons
        btn_frame = tk.Frame(self, bg="#F5F5F5")
        btn_frame.pack(fill='x', padx=10, pady=8)

        tk.Button(btn_frame, text='➕ Add Item', command=self.open_add_window).pack(side='left')
        tk.Button(btn_frame, text='🖋 Edit Selected', command=self.open_edit_window).pack(side='left', padx=6)
        tk.Button(btn_frame, text='🗑 Delete Selected', command=self.delete_selected).pack(side='left', padx=6)
        tk.Button(btn_frame, text='View Selected', command=self.open_view_window).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Refresh', command=self.refresh_tree).pack(side='left', padx=6)
        tk.Button(btn_frame, text= '👱‍♂️ User Management', command=self.open_user_panel, bg="#9C27B0", fg="white").pack(side='left', padx=6)
        # Sale button (only if allowed)
        if self.privileges["can_view_sales"]:
            tk.Button(btn_frame, text='🎁 Sale Panel', command=self.open_sale_panel, bg="#2196F3", fg="white").pack(side='left', padx=6)
        # Purchase button
        if self.privileges["can_view_purchase"]:
            tk.Button(btn_frame, text="🛒Purchase Panel", bg="#9C27B0", fg="white", command=lambda: PurchaseWindow(self)).pack(side="left", padx=6)
         # User Privileges button (Admin Only)
        if self.privileges["can_manage_users"]:
            tk.Button(btn_frame, text='User Privileges', command=self.open_privileges_panel, bg="#6A1B9A", fg="white").pack(side='left', padx=6)
        tk.Button(btn_frame, text='Logout', command=self.logout, bg='#f44336', fg='white').pack(side='right')

        # Search
        search_frame = tk.Frame(self)
        search_frame.pack(fill='x', padx=10)
        tk.Label(search_frame, text='🔍 Search:').pack(side='left')
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

     def load_privileges(self):
        conn = sqlite3.connect("store.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_privileges WHERE user_id=?", (self.user_id,))
        data = cur.fetchone()
        conn.close()

        if data:
            return {
                "can_view_sales": bool(data[2]),
                "can_edit_sales": bool(data[3]),
                "can_view_purchase": bool(data[4]),
                "can_edit_purchase": bool(data[5]),
                "can_manage_users": bool(data[6]),
            }
        else:
            return {"can_view_sales": 0, "can_edit_sales": 0, "can_view_purchase": 0, "can_edit_purchase": 0, "can_manage_users": 0}


    def open_user_panel(self):
        UserWindow(self)

    def open_sale_panel(self):
        SaleWindow(self)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()  # main window close
            login = LoginWindow()
            login.mainloop()

    def open_privileges_panel(self):
        UserPrivilegesPanel(self)


# ---------------- RESPONSIVE PURCHASE WINDOW ---------------- #
class PurchaseWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🛒 Purchase Panel (Responsive)")
        self.geometry("1000x600")
        self.minsize(900, 550)
        self.configure(bg="#f5f5f5")
        self.conn = sqlite3.connect(DB_FILENAME)
        self.selected_id = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        self.create_widgets()
        self.load_purchases()

        # Bind resizing
        self.bind("<Configure>", self.on_resize)

    # ---------------- CREATE ALL WIDGETS ---------------- #
    def create_widgets(self):
        # ---------- Input Frame ---------- #
        input_frame = tk.Frame(self, bg="#f5f5f5", bd=2, relief="groove")
        input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        for i in range(2):
            input_frame.columnconfigure(i, weight=1)

        labels = ["Product Name", "Product Code", "Quantity", "Purchase Price", "Supplier Name", "Supplier Contact"]
        self.entries = {}

        for i, text in enumerate(labels):
            tk.Label(input_frame, text=text, bg="white").grid(row=i // 2, column=(i % 2) * 2, padx=10, pady=10, sticky="e")
            e = tk.Entry(input_frame, width=25)
            e.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=10, pady=10, sticky="ew")
            self.entries[text] = e

        # ---------- Buttons ---------- #
        btn_frame = tk.Frame(self, bg="#f5f5f5")
        btn_frame.grid(row=1, column=0, pady=5)
        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)

        tk.Button(btn_frame, text="➕ Add", width=12, bg="#4CAF50", fg="white", command=self.add_purchase).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="✏️ Update", width=12, bg="#2196F3", fg="white", command=self.update_purchase).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="🗑 Delete", width=12, bg="#f44336", fg="white", command=self.delete_purchase).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="🔄 Clear", width=12, bg="#9E9E9E", fg="white", command=self.clear_fields).grid(row=0, column=3, padx=5)

        # ---------- Search Bar ---------- #
        search_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="ridge")
        search_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        search_frame.columnconfigure(1, weight=1)

        tk.Label(search_frame, text="🔍 Search:", bg="white").grid(row=0, column=0, padx=8)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var).grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(search_frame, text="Search", bg="#009688", fg="white", command=self.search_purchase).grid(row=0, column=2, padx=5)
        tk.Button(search_frame, text="Show All", bg="#FF9800", fg="white", command=self.load_purchases).grid(row=0, column=3, padx=5)

        # ---------- Treeview Table ---------- #
        table_frame = tk.Frame(self, bg="white")
        table_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=10)
        self.rowconfigure(5, weight=1)
        self.columnconfigure(0, weight=1)

        cols = ("id", "product_name", "product_code", "quantity", "purchase_price", "total_price", "supplier_name", "supplier_contact", "purchase_date")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.bind("<ButtonRelease-1>", self.select_row)

    # ---------------- ADD PURCHASE ---------------- #
    def add_purchase(self):
        data = {k: e.get().strip() for k, e in self.entries.items()}
        if not data["Product Name"] or not data["Quantity"] or not data["Purchase Price"]:
            messagebox.showwarning("Missing Info", "Please fill Product Name, Quantity, and Purchase Price.")
            return

        total = float(data["Quantity"]) * float(data["Purchase Price"])
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = self.conn.cursor()

        # --- AUTO UPDATE ITEMS TABLE AFTER PURCHASE --- #
        cur.execute("SELECT id, quantity FROM items WHERE name=?", (data["Product Name"],))
        item = cur.fetchone()

        if item:  # item already exists
            new_qty = int(item[1]) + int(data["Quantity"])
            cur.execute("""
            UPDATE items 
            SET quantity=?, price=?, created_at=? 
            WHERE id=?
            """, (new_qty, data["Purchase Price"], date, item[0]))
        else:  # item does not exist → add new
            cur.execute("""
            INSERT INTO items (name, quantity, price, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (data["Product Name"], data["Quantity"], data["Purchase Price"],
            "Auto-added from purchase", date))

        self.conn.commit()


        cur.execute("""
            INSERT INTO purchase (product_name, product_code, quantity, purchase_price, total_price, supplier_name, supplier_contact, purchase_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["Product Name"], data["Product Code"], data["Quantity"], data["Purchase Price"], total,
              data["Supplier Name"], data["Supplier Contact"], date))
        self.conn.commit()
        self.load_purchases()
        self.clear_fields()
        messagebox.showinfo("Success", "✅ Purchase added successfully!")

    # ---------------- LOAD PURCHASES ---------------- #
    def load_purchases(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM purchase ORDER BY id DESC")
        for row in cur.fetchall():
            self.tree.insert("", tk.END, values=row)

    # ---------------- SELECT ROW ---------------- #
    def select_row(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        self.selected_id = values[0]
        keys = list(self.entries.keys())
        for i, k in enumerate(keys):
            self.entries[k].delete(0, tk.END)
            self.entries[k].insert(0, values[i + 1])

    # ---------------- UPDATE PURCHASE ---------------- #
    def update_purchase(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a row to update.")
            return
        data = {k: e.get().strip() for k, e in self.entries.items()}
        total = float(data["Quantity"]) * float(data["Purchase Price"])
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE purchase 
            SET product_name=?, product_code=?, quantity=?, purchase_price=?, total_price=?, supplier_name=?, supplier_contact=?
            WHERE id=?
        """, (data["Product Name"], data["Product Code"], data["Quantity"], data["Purchase Price"],
              total, data["Supplier Name"], data["Supplier Contact"], self.selected_id))
        self.conn.commit()
        self.load_purchases()
        self.clear_fields()
        messagebox.showinfo("Updated", "✅ Purchase updated successfully!")

    # ---------------- DELETE PURCHASE ---------------- #
    def delete_purchase(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a row to delete.")
            return
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this purchase?")
        if confirm:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM purchase WHERE id=?", (self.selected_id,))
            self.conn.commit()
            self.load_purchases()
            self.clear_fields()
            messagebox.showinfo("Deleted", "🗑 Purchase deleted successfully!")

    # ---------------- SEARCH PURCHASE ---------------- #
    def search_purchase(self):
        query = self.search_var.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM purchase
            WHERE product_name LIKE ? OR product_code LIKE ? OR supplier_name LIKE ? OR supplier_contact LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        for row in cur.fetchall():
            self.tree.insert("", tk.END, values=row)

    # ---------------- CLEAR FIELDS ---------------- #
    def clear_fields(self):
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.selected_id = None

    # ---------------- RESPONSIVE TABLE ON RESIZE ---------------- #
    def on_resize(self, event):
        total_width = event.width - 50
        col_width = total_width // len(self.tree["columns"])
        for col in self.tree["columns"]:
            self.tree.column(col, width=col_width)

# --------------------- Sale Panel ---------------------
class SaleWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🎁 Sales Management")
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
        tk.Label(search_frame, text="🔍 Search:").pack(side="left")
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(search_frame, text="Go", command=self.search_sales).pack(side="left", padx=5)
        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(side="left", padx=5)

        # -------- Form Frame --------
        form_frame = tk.Frame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        # Match exactly with sales table columns
        labels = ["Product ID", "Product Code", "Product Price", "Product Profit", "Product Total", "Client Name", "Client CNIC"]

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
        tk.Button(btn_frame, text="Print Receipt", bg="#9C27B0", fg="white", command=self.print_receipt).pack(side="left", padx=5)

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
        # Get values from entries and validate
        try:
            product_id = self.entries["Product ID"].get().strip()
            product_code = self.entries["Product Code"].get().strip()
            product_price = float(self.entries["Product Price"].get().strip())
            product_profit = float(self.entries["Product Profit"].get().strip())
            product_total = float(self.entries["Product Total"].get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Price, Profit, and Total must be valid numbers")
            return
        
        if not product_id or not product_code:
            messagebox.showwarning("Validation", "Product ID and Product Code are required")
            return

        # Add to database
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO sales (product_id, product_code, product_price, product_profit, product_total, client_name, client_cnic, sale_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, product_code, product_price, product_profit, product_total,
            client_name, client_cnic, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # 1. Get product name by product_code from purchase table
        cur.execute("""
            SELECT product_name, quantity 
            FROM purchase 
            WHERE product_code=? 
            ORDER BY id DESC LIMIT 1
            """, (product_code,))

        purchase = cur.fetchone()

        if purchase:
            pname, purchase_qty = purchase

            # decrease 1 item per sale
            new_p_qty = max(0, purchase_qty - 1)
            cur.execute("UPDATE purchase SET quantity=? WHERE product_code=?", 
            (new_p_qty, product_code))

            # now update items table
            cur.execute("SELECT id, quantity FROM items WHERE name=?", (pname,))
            item = cur.fetchone()

            if item:
                new_item_qty = max(0, item[1] - 1)
                cur.execute("UPDATE items SET quantity=? WHERE id=?", 
                (new_item_qty, item[0]))

        self.conn.commit()
        self.load_data()
        self.clear_entries()
        messagebox.showinfo("Success", "Sale added successfully")

    def update_sale(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a row to update")
            return
        
        # Get values from entries and validate
        try:
            product_id = self.entries["Product ID"].get().strip()
            product_code = self.entries["Product Code"].get().strip()
            product_price = float(self.entries["Product Price"].get().strip())
            product_profit = float(self.entries["Product Profit"].get().strip())
            product_total = float(self.entries["Product Total"].get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Price, Profit, and Total must be valid numbers")
            return
        
        if not product_id or not product_code:
            messagebox.showwarning("Validation", "Product ID and Product Code are required")
            return

        # Update database
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE sales 
            SET product_id=?, product_code=?, product_price=?, product_profit=?, product_total=?
            WHERE id=?
        """, (product_id, product_code, product_price, product_profit, product_total, self.selected_id))
        self.conn.commit()
        self.load_data()
        self.clear_entries()
        messagebox.showinfo("Success", "Sale updated successfully")

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
        sel = self.tree.selection()
        if sel:
            selected = self.tree.item(sel[0], "values")
            keys = list(self.entries.keys())
            for i, key in enumerate(keys):
                self.entries[key].delete(0, "end")
                if i < len(selected):
                    self.entries[key].insert(0, selected[i])
            self.selected_id = int(selected[0])


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

    def print_receipt(self):
        # fetch store details
        conn = sqlite3.connect(DB_FILENAME)
        cur = conn.cursor()
        cur.execute("SELECT store_name, address, email, contact FROM store_details ORDER BY id DESC LIMIT 1")
        store = cur.fetchone()
        conn.close()
        
        store_name = store[0] if store else "Store Name"
        store_address = store[1] if store else ""
        store_email = store[2] if store else ""
        store_contact = store[3] if store else ""
        
        # fetch sale items
        cur = self.conn.cursor()
        cur.execute("SELECT product_id, product_code, product_price, product_total FROM sales ORDER BY id DESC")
        sale_items = cur.fetchall()
        
        if not sale_items:
            messagebox.showwarning("No Sales", "No sale items to print receipt")
            return
        
        pdf_filename = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        c = pdfcanvas.Canvas(pdf_path, pagesize=A4)
        w, h = A4
        y = h - 50
        
        # --- Store Info ---
        c.setFont('Helvetica-Bold', 14)
        c.drawString(50, y, store_name)
        y -= 20
        c.setFont('Helvetica', 10)
        c.drawString(50, y, store_address)
        y -= 15
        c.drawString(50, y, f"Email: {store_email} | Contact: {store_contact}")
        y -= 25
        c.drawString(50, y, "-"*70)
        y -= 20
        
        # --- Receipt Header ---
        c.drawString(50, y, "Purchase Receipt")
        y -= 20
        c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 20
        c.drawString(50, y, "-"*70)
        y -= 20
        
        # --- Table Header ---
        c.drawString(50, y, f"{'Product ID':<15}{'Code':<15}{'Price':<15}{'Total':<15}")
        y -= 20
        c.drawString(50, y, "-"*70)
        y -= 20
        
        total_amount = 0
        for pid, code, price, total in sale_items:
            total_amount += total
            c.drawString(50, y, f"{str(pid):<15}{str(code):<15}{str(price):<15}{str(total):<15}")
            y -= 20
            if y < 50:
                c.showPage()
                y = h - 50
        
        # Footer
        c.drawString(50, y, "-"*70)
        y -= 20
        c.drawString(50, y, f"TOTAL AMOUNT: {total_amount}")
        y -= 20
        c.drawString(50, y, f"Printed On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        c.showPage()
        c.save()
        
        messagebox.showinfo("Receipt", f"Receipt generated and saved as PDF:\n{pdf_path}")



# ---------------------- Receipt PrintPanel p----------------------
class ReceiptWindow(tk.Toplevel):
    def __init__(self, parent, sale_items=None):
        """
        sale_items: list of tuples (product_id, product_name, price, quantity)
        """
        super().__init__(parent)
        self.title("🛒 Purchase Receipt")
        self.geometry("600x500")
        self.sale_items = sale_items if sale_items else []

        tk.Label(self, text="Purchase Receipt", font=("Arial", 16, "bold")).pack(pady=10)

        # Receipt Text
        self.txt = tk.Text(self, width=70, height=20)
        self.txt.pack(padx=10, pady=10)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Generate Receipt", bg="#4CAF50", fg="white", command=self.generate_receipt).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Print Receipt", bg="#2196F3", fg="white", command=self.print_receipt).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Close", command=self.destroy, bg="#f44336", fg="white").pack(side='left', padx=5)

    def generate_receipt(self):
        self.txt.delete('1.0', 'end')
        total_amount = 0
        self.txt.insert('end', f"{'Product':<20}{'Qty':<10}{'Price':<10}{'Total':<10}\n")
        self.txt.insert('end', "-"*60 + "\n")
        for pid, name, price, qty in self.sale_items:
            total = price * qty
            total_amount += total
            self.txt.insert('end', f"{name:<20}{qty:<10}{price:<10}{total:<10}\n")
        self.txt.insert('end', "-"*60 + "\n")
        self.txt.insert('end', f"{'Total Amount:':<40}{total_amount}\n")
        self.txt.insert('end', f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def print_receipt(self):
        # Save as PDF
        pdf_filename = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        c = pdfcanvas.Canvas(pdf_path, pagesize=A4)
        w, h = A4
        y = h - 50
        lines = self.txt.get('1.0', 'end').split('\n')
        c.setFont('Courier', 10)
        for line in lines:
            c.drawString(50, y, line)
            y -= 15
            if y < 50:
                c.showPage()
                y = h - 50
        c.showPage()
        c.save()
        messagebox.showinfo("Receipt", f"Receipt saved as PDF: {pdf_path}")


# --------------------- User Management Panel ---------------------

class UserWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("👱‍♂️ User Management Panel")
        self.geometry("800x500")
        self.parent = parent

        # --- Search Bar ---
        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(search_frame, text="🍳 Search User:").pack(side="left")
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        tk.Button(search_frame, text="🔍 Search", command=self.search_user).pack(side="left", padx=5)
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
        # fixed table name from 'user' to 'users'
        cur.execute("SELECT id, name, father, cnic, password, created_at FROM users ORDER BY id DESC")
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
        self.title("➕ Add User" if mode=="add" else "Edit User")
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
        self.title('➕ Add Item' if mode=='add' else 'Edit Item')
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

class UserPrivilegesPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("User Privileges Management")
        self.geometry("600x450")
        self.configure(bg="#F4F4F4")

        tk.Label(self, text="Select User:", bg="#F4F4F4", font=("Arial", 12, "bold")).pack(pady=5)
        self.user_combo = ttk.Combobox(self, width=40)
        self.user_combo.pack(pady=5)
        self.load_users()

        # checkboxes
        self.var_view_sales = tk.IntVar()
        self.var_edit_sales = tk.IntVar()
        self.var_view_purchase = tk.IntVar()
        self.var_edit_purchase = tk.IntVar()
        self.var_manage_users = tk.IntVar()

        frame = tk.Frame(self, bg="#F4F4F4")
        frame.pack(pady=20)

        tk.Checkbutton(frame, text="View Sales", variable=self.var_view_sales, bg="#F4F4F4").grid(row=0, column=0, sticky="w", padx=15)
        tk.Checkbutton(frame, text="Edit Sales", variable=self.var_edit_sales, bg="#F4F4F4").grid(row=0, column=1, sticky="w", padx=15)
        tk.Checkbutton(frame, text="View Purchase", variable=self.var_view_purchase, bg="#F4F4F4").grid(row=1, column=0, sticky="w", padx=15)
        tk.Checkbutton(frame, text="Edit Purchase", variable=self.var_edit_purchase, bg="#F4F4F4").grid(row=1, column=1, sticky="w", padx=15)
        tk.Checkbutton(frame, text="Manage Users (Admin)", variable=self.var_manage_users, bg="#F4F4F4").grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=5)

        # buttons
        tk.Button(self, text="Save Privileges", bg="#4CAF50", fg="white", width=20, command=self.save_privileges).pack(pady=8)
        tk.Button(self, text="Load Privileges", bg="#2196F3", fg="white", width=20, command=self.load_privileges).pack(pady=5)

    def load_users(self):
        conn = sqlite3.connect("store.db")
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users")
        users = cur.fetchall()
        conn.close()
        self.user_map = {u[1]: u[0] for u in users}
        self.user_combo["values"] = [u[1] for u in users]

    def save_privileges(self):
        user_name = self.user_combo.get()
        if not user_name:
            messagebox.showwarning("Warning", "Select a user first.")
            return

        user_id = self.user_map[user_name]
        data = (
            user_id,
            self.var_view_sales.get(),
            self.var_edit_sales.get(),
            self.var_view_purchase.get(),
            self.var_edit_purchase.get(),
            self.var_manage_users.get()
        )

        conn = sqlite3.connect("store.db")
        cur = conn.cursor()
        cur.execute("SELECT id FROM user_privileges WHERE user_id=?", (user_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE user_privileges SET
                    can_view_sales=?, can_edit_sales=?,
                    can_view_purchase=?, can_edit_purchase=?,
                    can_manage_users=?
                WHERE user_id=?""",
                (data[1], data[2], data[3], data[4], data[5], user_id))
        else:
            cur.execute("""
                INSERT INTO user_privileges 
                    (user_id, can_view_sales, can_edit_sales, can_view_purchase, can_edit_purchase, can_manage_users)
                VALUES (?, ?, ?, ?, ?, ?)""", data)
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Privileges updated for {user_name}")

    def load_privileges(self):
        user_name = self.user_combo.get()
        if not user_name:
            messagebox.showwarning("Warning", "Select a user first.")
            return

        user_id = self.user_map[user_name]
        conn = sqlite3.connect("store.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_privileges WHERE user_id=?", (user_id,))
        priv = cur.fetchone()
        conn.close()

        if priv:
            self.var_view_sales.set(priv[2])
            self.var_edit_sales.set(priv[3])
            self.var_view_purchase.set(priv[4])
            self.var_edit_purchase.set(priv[5])
            self.var_manage_users.set(priv[6])
        else:
            self.var_view_sales.set(0)
            self.var_edit_sales.set(0)
            self.var_view_purchase.set(0)
            self.var_edit_purchase.set(0)
            self.var_manage_users.set(0)
            messagebox.showinfo("Info", "No privileges found for this user.")


class ViewWindow(tk.Toplevel):
    def __init__(self, parent, item_id):
        super().__init__(parent)
        self.item_id = item_id
        self.title('💭 View Item')
        self.geometry('450x350')
        row = fetch_item(item_id)
        if not row:
            tk.Label(self, text='😢 Item not found').pack(padx=10, pady=10)
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
        self.title('🔐 Login')
        self.geometry('650x650')
        self.configure(bg='white')

        # Logo (optional)
        ICON_FOLDER = os.path.join(os.getcwd(), 'icons')
        logo_path = os.path.join(ICON_FOLDER, 'app_logo.png')
        if os.path.exists(logo_path):
            logo_img = tk.PhotoImage(file=logo_path)
            tk.Label(self, image=logo_img, bg='white').pack(pady=10)
            self.logo_img = logo_img  # keep reference

        tk.Label(self, text='💂🏻‍♂️ Username', bg='white').pack(pady=5)
        self.username = tk.Entry(self)
        self.username.pack(pady=5)

        tk.Label(self, text='🔐 Password', bg='white').pack(pady=5)
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