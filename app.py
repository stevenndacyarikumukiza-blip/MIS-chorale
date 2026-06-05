from flask import Flask, render_template, request, redirect
import pymysql
import os
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ===============================
# UPLOAD FOLDER
# ===============================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ===============================
# DATABASE CONNECTION
# ===============================
def db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="chorale_mis",
        cursorclass=pymysql.cursors.DictCursor
    )


# ===============================
# DASHBOARD
# ===============================
@app.route("/")
def dashboard():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM abanyamuryango")
    total = cur.fetchone()["total"]

    conn.close()

    return render_template("dashboard.html", total=total)


# ===============================
# MEMBERS
# ===============================
@app.route("/abanyamuryango")
def members():

    search = request.args.get("search")

    conn = db()
    cur = conn.cursor()

    if search:
        cur.execute("""
            SELECT * FROM abanyamuryango
            WHERE amazina LIKE %s OR nimero LIKE %s
            ORDER BY id DESC
        """, ("%" + search + "%", "%" + search + "%"))
    else:
        cur.execute("SELECT * FROM abanyamuryango ORDER BY id DESC")

    data = cur.fetchall()
    conn.close()

    return render_template("members.html", data=data)


@app.route("/add_member")
def add_member():
    return render_template("add_member.html")


@app.route("/save_member", methods=["POST"])
def save_member():

    conn = db()
    cur = conn.cursor()

    amazina = request.form.get("amazina")
    igitsina = request.form.get("igitsina")
    itariki_yamavuko = request.form.get("itariki_yamavuko")
    indangamuntu = request.form.get("indangamuntu")
    telefoni = request.form.get("telefoni")
    email = request.form.get("email")
    aderesi = request.form.get("aderesi")
    department = request.form.get("department")
    inshingano = request.form.get("inshingano")
    ijwi_aririmba = request.form.get("ijwi_aririmba")
    itariki_yinjiye = request.form.get("itariki_yinjiye")
    yarabatijwe = request.form.get("yarabatijwe")
    uwo_guhamagara = request.form.get("uwo_guhamagara")
    telefoni_yumuryango = request.form.get("telefoni_yumuryango")

    nimero = "CHR-" + (telefoni[-4:] if telefoni else "0000")

    photo = request.files.get("photo")
    camera_photo = request.form.get("camera_photo")

    filename = None

    if photo and photo.filename != "":
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    elif camera_photo and "," in camera_photo:
        filename = f"{nimero}.png"
        image_data = camera_photo.split(",")[1]

        with open(os.path.join(app.config["UPLOAD_FOLDER"], filename), "wb") as f:
            f.write(base64.b64decode(image_data))

    cur.execute("""
        INSERT INTO abanyamuryango (
            nimero, amazina, igitsina, itariki_yamavuko,
            indangamuntu, telefoni, email, aderesi,
            department, inshingano, ijwi_aririmba,
            itariki_yinjiye, status, yarabatijwe,
            uwo_guhamagara, telefoni_yumuryango, ifoto
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s)
    """, (
        nimero, amazina, igitsina, itariki_yamavuko,
        indangamuntu, telefoni, email, aderesi,
        department, inshingano, ijwi_aririmba,
        itariki_yinjiye, "Active", yarabatijwe,
        uwo_guhamagara, telefoni_yumuryango, filename
    ))

    conn.commit()
    conn.close()

    return redirect("/abanyamuryango")


# ===============================
# ATTENDANCE (Uko Bitabira)
# ===============================
@app.route("/attendance")
def attendance():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.id,
            s.ubwoko,
            s.izina_event,
            s.itariki,
            m.amazina,
            a.status
        FROM attendance a

        JOIN attendance_sessions s
            ON a.session_id = s.id

        JOIN abanyamuryango m
            ON a.member_id = m.id

        ORDER BY s.itariki DESC
    """)

    attendances = cur.fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        attendances=attendances
    )
# ===============================
# SAVE ATTENDANCE
# ===============================
@app.route("/save_attendance", methods=["POST"])
def save_attendance():

    ubwoko = request.form.get("ubwoko")
    izina_event = request.form.get("izina_event")
    itariki = request.form.get("itariki")
    ibisobanuro = request.form.get("ibisobanuro")

    conn = db()
    cur = conn.cursor()

    # 1. Bika session
    cur.execute("""
        INSERT INTO attendance_sessions
        (
            ubwoko,
            izina_event,
            itariki,
            ibisobanuro
        )
        VALUES (%s,%s,%s,%s)
    """, (
        ubwoko,
        izina_event,
        itariki,
        ibisobanuro
    ))

    conn.commit()

    # 2. Fata ID ya session imaze kubikwa
    session_id = cur.lastrowid

    # 3. Fata abanyamuryango bose
    cur.execute("""
        SELECT id
        FROM abanyamuryango
    """)

    members = cur.fetchall()

    # 4. Bika attendance ya buri muntu
    for member in members:

        member_id = member["id"]

        status = request.form.get(
            f"status_{member_id}"
        )

        if status:

            cur.execute("""
                INSERT INTO attendance
                (
                    session_id,
                    member_id,
                    status,
                    ibisobanuro
                )
                VALUES (%s,%s,%s,%s)
            """, (
                session_id,
                member_id,
                status,
                ""
            ))

    conn.commit()
    conn.close()

    return redirect("/attendance")

# ===============================
# ADD ATTENDANCE (Kwandika Abitabiriye)
# ===============================
@app.route("/add_attendance")
def add_attendance():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nimero, amazina, ijwi_aririmba, ifoto
        FROM abanyamuryango
        ORDER BY amazina
    """)

    members = cur.fetchall()

    conn.close()

    return render_template("add_attendance.html", members=members)

# ===============================
# CONTRIBUTIONS (IMISANZU)
# ===============================
@app.route("/imisanzu")
def imisanzu():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            i.id,
            i.ubwoko_umusanzu,
            i.ukwezi,
            i.umwaka,
            i.amafaranga,
            i.igihe,
            m.amazina
        FROM imisanzu i
        JOIN abanyamuryango m
        ON i.member_id = m.id
        ORDER BY i.id DESC
    """)

    contributions = cur.fetchall()

    conn.close()

    return render_template("contributions.html", contributions=contributions)
# ===============================
# DELETE CONTRIBUTION
# ===============================
@app.route("/delete_contribution/<int:id>")
def delete_contribution(id):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM imisanzu
        WHERE id=%s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/imisanzu")


# ===============================
# ADD CONTRIBUTION
# ===============================
@app.route("/add_contribution")
def add_contribution():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, amazina
        FROM abanyamuryango
        ORDER BY amazina
    """)

    members = cur.fetchall()

    conn.close()

    return render_template("add_contribution.html", members=members)


# ===============================
# SAVE CONTRIBUTION
# ===============================
@app.route("/save_contribution", methods=["POST"])
def save_contribution():

    member_id = request.form.get("member_id")
    ubwoko_umusanzu = request.form.get("ubwoko_umusanzu")
    ukwezi = request.form.get("ukwezi")
    umwaka = request.form.get("umwaka")
    amafaranga = request.form.get("amafaranga")
    uburyo_kwishyura = request.form.get("uburyo_kwishyura")
    nimero_transisiyo = request.form.get("nimero_transisiyo")
    ibisobanuro = request.form.get("ibisobanuro")
    igihe = request.form.get("igihe")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO imisanzu (
            member_id,
            ubwoko_umusanzu,
            ukwezi,
            umwaka,
            amafaranga,
            uburyo_kwishyura,
            nimero_transisiyo,
            ibisobanuro,
            igihe
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        member_id,
        ubwoko_umusanzu,
        ukwezi,
        umwaka,
        amafaranga,
        uburyo_kwishyura,
        nimero_transisiyo,
        ibisobanuro,
        igihe
    ))

    conn.commit()
    conn.close()

    return redirect("/imisanzu")
# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)