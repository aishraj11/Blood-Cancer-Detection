# import os
# import numpy as np
# from flask import Flask, request, render_template, flash, send_from_directory
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing import image
# from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_preprocess
# # If you use SqueezeNet with custom preprocessing, you can adjust here

import os
import numpy as np
from flask import Flask, request, render_template, send_from_directory, url_for,flash
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input
import mysql.connector
mydb = mysql.connector.connect(host='localhost', user='root', password='', port='3307', database='blood_cancer')
cur = mydb.cursor()
app = Flask(__name__)
app.secret_key = 'your-secret-key-2025-change-me'





@app.route('/')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template('about.html')




# ─── LOGIN ───────────────────────────────────────────────────────────────
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['psw']
        sql = "SELECT * FROM user_registration WHERE Email=%s and Password=%s"
        val = (email, password)
        cur = mydb.cursor()
        cur.execute(sql, val)
        results = cur.fetchall()
        mydb.commit()
        if len(results) >= 1:
            return render_template('loginhomepage.html', msg='success')
        else:
            return render_template('login.html', msg='fail')
    return render_template('login.html')


# ─── REGISTER ────────────────────────────────────────────────────────────
@app.route("/Register", methods=['GET', 'POST'])
def Register():
    if request.method == "POST":
        fname = request.form['firstname']
        lname = request.form['lastname']
        email = request.form['email']
        pwd = request.form['psw']
        cpsw = request.form['cpsw']
        mno = request.form['mobile']
        sql = "select email from user_registration where  email='%s'" % (email)
        cur.execute(sql)
        data = cur.fetchall()
        mydb.commit()
        data = [j for i in data for j in i]
        if pwd==cpsw:
            if data == []:
                sql = "insert into user_registration(first_name,last_name,email,password,mobile_number) values(%s,%s,%s,%s,%s)"
                val = (fname, lname, email, pwd, mno)
                print(val)
                print(sql)
                cur.execute(sql, val)
                mydb.commit()
                cur.close()
                flash("Account created Successully", "success")
                return render_template('login.html')
            else:
                flash("Details already Exists", "warning")
                return render_template('register.html')
        else:
            flash("Password and Confirm Password not same","warning")
            return render_template('Register.html')

    return render_template('Register.html')

@app.route("/loginhomepage")
def loginhomepage():
    return render_template('loginhomepage.html')


# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Model setup - change path/model as needed
MODEL_PATH = 'models/vgg16.h5'          # ← your actual model path
model = load_model(MODEL_PATH)
preprocess_function = preprocess_input   # VGG16 preprocessing

classes = ['Benign', 'Pro', 'Early', 'Pre']  # ← match your model's output order

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    prediction = None
    confidence = None
    image_url = None
    error = None

    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'No file part'
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'No selected file'
            elif file and allowed_file(file.filename):
                filename = file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                try:
                    # Load and preprocess
                    img = image.load_img(filepath, target_size=(224, 224))
                    img_array = image.img_to_array(img)
                    img_array = preprocess_function(img_array)
                    img_array = np.expand_dims(img_array, axis=0)

                    # Predict
                    preds = model.predict(img_array)
                    pred_idx = np.argmax(preds[0])
                    prediction = classes[pred_idx]
                    confidence = round(float(preds[0][pred_idx]) * 100, 2)

                    # Image URL for display in template
                    image_url = url_for('uploaded_file', filename=filename)

                except Exception as e:
                    error = f'Error processing image: {str(e)}'
            else:
                error = 'Invalid file type. Only PNG, JPG, JPEG allowed.'

    return render_template(
        'predict.html',
        prediction=prediction,
        confidence=confidence,
        image_url=image_url,
        error=error
    )

if __name__ == '__main__':
    app.run(debug=True)