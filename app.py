from flask import Flask, render_template, redirect, url_for, session, request, flash
import sqlite3
import os


UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "tirupathi-finance-secret"

DB_NAME = "database.db"

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
def execute_query(query, params=()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def fetch_query(query, params=()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        mobile1 TEXT,
        mobile2 TEXT,
        role TEXT,
        address TEXT,
        bank_details TEXT,
        username TEXT UNIQUE,
        password TEXT,
        company TEXT,
        photo TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS address (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sub_street TEXT,
        street TEXT,
        area_name TEXT
    );
    """)

    # ✅ Create vehicle_type table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    """)
    
    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        # Admin Login
        if role == "admin" and username == "admin" and password == "1234":
            session["role"] = "admin"
            return redirect(url_for("dashboard"))

        # SKS Login (same username & password)
        elif role == "sks" and username == "admin" and password == "1234":
            session["role"] = "sks"
            return redirect(url_for("sks_dashboard"))

        else:
            flash("Invalid Username or Password")

    return render_template("login.html")

@app.route("/sks")
def sks_dashboard():
    if "role" not in session or session["role"] != "sks":
        return redirect(url_for("login"))

    return render_template("sks_dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/masters")
def masters():
    return render_template("masters.html")


# ---------------- ADDRESS PAGE ----------------


# ---------------- USERS ----------------
@app.route("/users")
def users():
    if "role" not in session:
        return redirect(url_for("login"))
    return render_template("users.html")


@app.route("/users/add", methods=["GET", "POST"])
def add_user():
    if "role" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        # -------- GET FORM DATA --------
        name = request.form.get("name")
        email = request.form.get("email")
        mobile1 = request.form.get("mobile1")
        mobile2 = request.form.get("mobile2")
        role = request.form.get("role")
        address = request.form.get("address")
        bank_details = request.form.get("bank_details")
        username = request.form.get("username")
        password = request.form.get("password")
        company = request.form.get("company")
        inactive = request.form.get("inactive")
        is_active = 0 if inactive else 1

        # -------- PHOTO UPLOAD CODE (ADD HERE) --------
        photo = request.files.get("photo")
        filename = None

        if photo and photo.filename != "":
            filename = photo.filename
            photo.save(os.path.join(UPLOAD_FOLDER, filename))

        # -------- INSERT INTO DATABASE --------
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("""
                    INSERT INTO users
                    (name, email, mobile1, mobile2, role, address,
                     bank_details, username, password, company,
                     photo, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, email, mobile1, mobile2, role, address,
                    bank_details, username, password, company,
                    filename, is_active
                ))

            flash("✅ User added successfully!")

        except sqlite3.IntegrityError:
            flash("❌ Username already exists")

        return redirect(url_for("add_user"))

    return render_template("add_user.html")
@app.route("/users/list")
def user_list():
    if "role" not in session:
        return redirect(url_for("login"))

    limit = request.args.get("limit", 10, type=int)
    search_by = request.args.get("search_by", "name")
    search_text = request.args.get("search_text", "").strip()

    conn = get_db()

    query = """
        SELECT id, name, mobile1, username,
               is_active, password, company
        FROM users
    """

    params = []

    if search_text:
        if search_by == "mobile":
            query += " WHERE mobile1 LIKE ?"
        else:
            query += " WHERE LOWER(name) LIKE LOWER(?)"

        params.append(f"%{search_text}%")

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    users = conn.execute(query, params).fetchall()
    conn.close()

    print("Search Text:", search_text)  # Debug line
    print("Users Found:", len(users))   # Debug line

    return render_template(
        "user_list.html",
        users=users,
        limit=limit,
        search_by=search_by,
        search_text=search_text
    )
@app.route("/users/edit/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    if "role" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        inactive = request.form.get("inactive")
        is_active = 0 if inactive else 1

        # 🔥 GET EXISTING USER
        user = conn.execute("SELECT photo FROM users WHERE id=?", (id,)).fetchone()
        existing_photo = user["photo"]

        # 🔥 HANDLE NEW PHOTO
        photo = request.files.get("photo")
        filename = existing_photo   # default keep old image

        if photo and photo.filename != "":
            filename = photo.filename
            photo.save(os.path.join(UPLOAD_FOLDER, filename))

        # 🔥 UPDATE INCLUDING PHOTO
        conn.execute("""
            UPDATE users SET
            name=?, email=?, mobile1=?, mobile2=?, role=?,
            address=?, bank_details=?, username=?, password=?,
            company=?, photo=?, is_active=?
            WHERE id=?
        """, (
            request.form["name"],
            request.form["email"],
            request.form["mobile1"],
            request.form["mobile2"],
            request.form["role"],
            request.form["address"],
            request.form["bank_details"],
            request.form["username"],
            request.form["password"],
            request.form["company"],
            filename,
            is_active,
            id
        ))

        conn.commit()
        conn.close()

        return "<script>window.parent.location.reload();</script>"

    user = conn.execute(
        "SELECT * FROM users WHERE id=?", (id,)
    ).fetchone()

    conn.close()

    return render_template("add_user.html", user=user)
@app.route("/users/delete/<int:id>")
def delete_user(id):
    if "role" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("user_list"))

@app.route("/save_address", methods=["POST"])
def save_address():
    id = request.form.get("id")
    sub = request.form["substreet"]
    street = request.form["street"]
    area = request.form["area"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if id:  # Update
        cursor.execute("""
            UPDATE address
            SET sub_street=?, street=?, area_name=?
            WHERE id=?
        """, (sub, street, area, id))
    else:  # Insert
        cursor.execute("""
            INSERT INTO address (sub_street, street, area_name)
            VALUES (?, ?, ?)
        """, (sub, street, area))

    conn.commit()
    conn.close()

    return redirect("/address")
@app.route("/address")
def address():
    edit_id = request.args.get("edit_id")
    search_by = request.args.get("search_by", "")
    search_text = request.args.get("search_text", "")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Use dictionary-like rows
    cursor = conn.cursor()

    # 1️⃣ Fetch list of addresses
    query = "SELECT * FROM address"
    params = []

    if search_text:
        if search_by == "area":
            query += " WHERE area_name LIKE ?"
        elif search_by == "sub":
            query += " WHERE sub_street LIKE ?"
        elif search_by == "street":
            query += " WHERE street LIKE ?"

        params.append('%' + search_text + '%')

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # 2️⃣ Fetch edit data if edit_id is provided
    edit_data = None
    if edit_id:
        cursor.execute("SELECT * FROM address WHERE id=?", (edit_id,))
        edit_data_row = cursor.fetchone()
        if edit_data_row:
            edit_data = edit_data_row

    conn.close()

    return render_template(
        "address.html",
        data=rows,
        edit_data=edit_data,
        search_by=search_by,
        search_text=search_text
    )
@app.route("/delete_address/<int:id>")
def delete_address(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM address WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/address")



vehicle_types = []  # Each item: [id, vehicle_type_name]
next_id = 1

@app.route('/vehicle_type', methods=['GET'])
def vehicle_type():
    search_by = request.args.get('search_by', 'vehicle_type')
    search_text = request.args.get('search_text', '')
    edit_id = request.args.get('edit_id')

    edit_data = None
    if edit_id:
        edit_data_rows = fetch_query("SELECT * FROM vehicle_type WHERE id=?", (edit_id,))
        if edit_data_rows:
            edit_data = edit_data_rows[0]

    if search_text:
        data = fetch_query("SELECT * FROM vehicle_type WHERE name LIKE ?", ('%' + search_text + '%',))
    else:
        data = fetch_query("SELECT * FROM vehicle_type")

    return render_template('vehicle_type.html',
                           data=data,
                           edit_data=edit_data,
                           search_by=search_by,
                           search_text=search_text)

@app.route('/save_vehicle_type', methods=['POST'])
def save_vehicle_type():
    vt_id = request.form.get('id')
    vt_name = request.form.get('vehicle_type').strip()

    if vt_id:  # Update existing
        execute_query("UPDATE vehicle_type SET name=? WHERE id=?", (vt_name, vt_id))
    else:  # Add new
        execute_query("INSERT INTO vehicle_type (name) VALUES (?)", (vt_name,))

    return redirect(url_for('vehicle_type'))

@app.route('/delete_vehicle_type/<int:vt_id>', methods=['GET'])
def delete_vehicle_type(vt_id):
    execute_query("DELETE FROM vehicle_type WHERE id=?", (vt_id,))
    return redirect(url_for('vehicle_type'))


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()   # 👈 ADD THIS
    app.run(debug=True, use_reloader=False)