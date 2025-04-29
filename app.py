from flask import Flask,render_template,flash,redirect,request,send_from_directory,url_for, send_file
import mysql.connector, os
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img 
from keras.preprocessing import image
from tensorflow.keras.models import load_model
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='foods'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
                values = (name, email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered! Please go to login section")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email.lower() == "admin@gmail.com":
            if password.lower() == "admin":
                return redirect("/admin_home")
            else:
                return render_template('login.html', message= "Invalid Password!!")
        
        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password.upper() == password__data[0][0]:
                global user_email
                user_email = email

                return redirect("/home")
            return render_template('home.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')

@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')

@app.route('/add_recipie', methods = ["GET", "POST"])
def add_recipie():
    if request.method == "POST":
        r_name = request.form['r_name']
        myfile = request.files['image']
        ingredients = request.form['ingredients']
        procedure = request.form['procedure']
        video_link = request.form['video_link']

        fn = myfile.filename
        mypath = os.path.join('static/images/', fn)
        myfile.save(mypath)
 
        query = "INSERT INTO recipies(`name`, `image`, `ingredients`, `making_procedure`, `video`) VALUES (%s, %s, %s, %s, %s)"
        values = (r_name, mypath, ingredients, procedure, video_link)
        executionquery(query, values)
        return render_template('add_recipie.html', message = "Sucessfully added!")
    return render_template('add_recipie.html')

@app.route('/view_recipie', methods = ["GET", "POST"])
def view_recipie():
    if request.method == "POST":
        id = request.form['id']
        query = "SELECT * FROM recipies WHERE id = %s"
        values = (id, )
        data = retrivequery1(query, values)
        return render_template('view_recipie.html', data = data)

    query = "SELECT * FROM recipies"
    data = retrivequery2(query)
    return render_template('view_recipie.html', datas = data)



@app.route('/update_recipie', methods = ["POST"])
def update_recipie():
    id = request.form['id']
    r_name = request.form['r_name']
    myfile = request.files['image']
    ingredients = request.form['ingredients']
    procedure = request.form['procedure']
    video_link = request.form['video_link']
    alt = request.form['alt']

    if myfile:
        fn = myfile.filename
        mypath = os.path.join('static/images/', fn)
        myfile.save(mypath)
    else:
        mypath = alt

    query = "SELECT * FROM recipies WHERE id = %s"
    values = (id, )
    data = retrivequery1(query, values)

    query = "UPDATE recipies SET name = %s, image = %s, ingredients = %s, making_procedure = %s, video = %s WHERE id = %s"
    values = (r_name, mypath, ingredients, procedure, video_link, id)
    executionquery(query, values)

    query = "SELECT * FROM recipies"
    data = retrivequery2(query)
    return render_template('view_recipie.html', datas = data, message = "Successfully Updated!")



@app.route('/delete_recipie', methods = ["POST"])
def delete_recipie():
    id = request.form['id']

    query = "DELETE FROM recipies WHERE id = %s"
    values = (id, )
    executionquery(query, values)

    query = "SELECT * FROM recipies"
    data = retrivequery2(query)
    return render_template('view_recipie.html', datas = data, message = "Successfully Deleted!!")


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        myfile = request.files['image']
        fn = myfile.filename
        mypath = os.path.join('static/user_images/', fn)
        myfile.save(mypath)

        classes=["burger","butter_naan","chai","chapati",
                 "chole_bhature","dal_makhani","dhokla","fried_rice",
                 "idli","jalebi","kaathi_rolls","kadai_paneer",
                 "kulfi","masala_dosa","momos","paani_puri", "pakode",
                 "pav_bhaji","pizza","samosa"]
        
        model=load_model("final_cnn.h5")
        test_img=image.load_img(mypath,target_size=(224,224))
        test_img=image.img_to_array(test_img)
        test_img = np.expand_dims(test_img, axis=0)
        test_img=test_img/255.0
        
        # Perform prediction
        prediction = model.predict(test_img)
        result=classes[np.argmax(prediction)]
        print(11111111, result)
        name = result.upper()

        query = "SELECT * FROM recipies WHERE UPPER(name) = %s"
        values = (name, )
        data = retrivequery1(query, values)

        if data:
            prediction = data
        else:
            prediction = "Unknown"

        return render_template('upload.html', path = mypath, prediction = prediction)
    return render_template('upload.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        text = request.form['text']
        name = text.upper()

        query = "SELECT * FROM recipies WHERE UPPER(name) = %s"
        values = (name, )
        data = retrivequery1(query, values)
        print(11111111111111, data)
        if data:
            prediction = data
        else:
            prediction = "Unknown"

        return render_template('search.html', prediction = prediction)
    return render_template('search.html')



if __name__ == '__main__':
    app.run(debug = True)