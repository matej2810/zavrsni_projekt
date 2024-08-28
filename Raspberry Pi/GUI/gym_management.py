import tkinter as tk
from tkinter import messagebox
import pymysql
import threading
import time
import os
from dotenv import load_dotenv
from mfrc522 import SimpleMFRC522

load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'gym_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'gym_management')

class GymManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gym Management System")
        self.root.geometry("800x400")

        # Initialize database connection
        self.conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)
        self.cursor = self.conn.cursor()

        # Initialize RFID reader
        self.rfid_reader = SimpleMFRC522()

        self.show_login_screen()

    def show_login_screen(self):
        self.clear_screen()

        login_frame = tk.Frame(self.root)
        login_frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(login_frame, text="Username:").grid(row=0, column=0, pady=5)
        self.username_entry = tk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(login_frame, text="Password:").grid(row=1, column=0, pady=5)
        self.password_entry = tk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        tk.Button(login_frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        sql = "SELECT * FROM admin WHERE username=%s AND password=%s"
        self.cursor.execute(sql, (username, password))
        admin = self.cursor.fetchone()
        if admin:
            self.show_main_screen()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def show_main_screen(self):
        self.clear_screen()

        add_member_frame = tk.Frame(self.root)
        add_member_frame.place(relx=0.5, rely=0.4, anchor='center')

        tk.Label(add_member_frame, text="Name:").grid(row=0, column=0, pady=5)
        self.name_entry = tk.Entry(add_member_frame)
        self.name_entry.grid(row=0, column=1, pady=5)

        tk.Label(add_member_frame, text="RFID Card:").grid(row=1, column=0, pady=5)
        self.rfid_entry = tk.Entry(add_member_frame)
        self.rfid_entry.grid(row=1, column=1, pady=5)

        tk.Label(add_member_frame, text="Role:").grid(row=2, column=0, pady=5)
        self.role_var = tk.StringVar(value="member")
        tk.Radiobutton(add_member_frame, text="Member (3 entries max)", variable=self.role_var, value="member").grid(row=2, column=1, sticky="w")
        tk.Radiobutton(add_member_frame, text="Staff (unlimited entries)", variable=self.role_var, value="staff").grid(row=3, column=1, sticky="w")

        tk.Button(add_member_frame, text="Add Member", command=self.add_member).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(add_member_frame, text="Show Members", command=self.show_members).grid(row=5, column=0, columnspan=2, pady=10)

        tk.Button(add_member_frame, text="Logout", command=self.logout).grid(row=6, column=0, columnspan=2, pady=10)

        # Start a thread to listen for RFID card scans
        self.rfid_thread = threading.Thread(target=self.listen_for_rfid)
        self.rfid_thread.daemon = True
        self.rfid_thread.start()

    def listen_for_rfid(self):
        while True:
            try:
                rfid_uid = self.rfid_reader.read_id()
                self.root.after(0, self.update_rfid_entry, rfid_uid)
            except Exception as e:
                print(f"Error reading RFID: {e}")
                time.sleep(1)

    def update_rfid_entry(self, rfid_uid):
        self.rfid_entry.delete(0, tk.END)
        self.rfid_entry.insert(0, str(rfid_uid))

    def add_member(self):
        name = self.name_entry.get()
        rfid_card = self.rfid_entry.get()
        role = self.role_var.get()

        if name and rfid_card:
            try:
                sql = "INSERT INTO members (name, rfid_card, role) VALUES (%s, %s, %s)"
                self.cursor.execute(sql, (name, rfid_card, role))
                self.conn.commit()
                messagebox.showinfo("Success", "Member added successfully")
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"Error adding member: {e}")
        else:
            messagebox.showwarning("Input error", "Please enter both name and scan the RFID card")

    def show_members(self):
        self.clear_screen()

        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        members_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=members_frame, anchor="nw")

        self.cursor.execute("SELECT id, name, rfid_card, entry_count, role FROM members")
        members = self.cursor.fetchall()

        for idx, member in enumerate(members):
            member_info = f"ID: {member[0]}, Name: {member[1]}, RFID: {member[2]}, Entries: {member[3]}, Role: {member[4]}"
            tk.Label(members_frame, text=member_info).grid(row=idx, column=0, padx=10, pady=5)

            tk.Button(members_frame, text="Remove", command=lambda m_id=member[0]: self.remove_member(m_id)).grid(row=idx, column=1, padx=10, pady=5)
            tk.Button(members_frame, text="Reset Entries", command=lambda m_id=member[0]: self.reset_entries(m_id)).grid(row=idx, column=2, padx=10, pady=5)

        tk.Button(members_frame, text="Back", command=self.show_main_screen).grid(row=len(members), column=0, columnspan=3, pady=10)

        members_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def remove_member(self, member_id):
        confirm = messagebox.askyesno("Confirm Removal", "Are you sure you want to remove this member?")
        if confirm:
            try:
                sql = "DELETE FROM members WHERE id = %s"
                self.cursor.execute(sql, (member_id,))
                self.conn.commit()
                messagebox.showinfo("Success", "Member removed successfully")
                self.show_members()
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"Error removing member: {e}")

    def reset_entries(self, member_id):
        try:
            sql = "UPDATE members SET entry_count = 0 WHERE id = %s"
            self.cursor.execute(sql, (member_id,))
            self.conn.commit()
            messagebox.showinfo("Success", "Entry count reset successfully")
            self.show_members()
        except pymysql.MySQLError as e:
            messagebox.showerror("Error", f"Error resetting entry count: {e}")

    def logout(self):
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def __del__(self):
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = GymManagementApp(root)
    root.mainloop()
