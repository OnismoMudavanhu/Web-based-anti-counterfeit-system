from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, jsonify
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import json
import datetime
import time
import uuid
import pygal

#for api
import pymysql
from flask import jsonify
#from db_config import mysql
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)

# config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'brandprotector'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init
mysql =MySQL(app)

@app.route('/home')
def dashboard():
    return render_template('home.html')

#register class
class RegisterForm(Form):
    name = StringField('Name:', [validators.DataRequired(),validators.Length(min=1, max=50)])
    username = StringField('Username:', [validators.DataRequired(),validators.Length(min=4, max=255)])
    email = StringField('Email:',[validators.Length(min=6, max=50),validators.Email(), validators.DataRequired()])
    password = PasswordField('Password:', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password:',[validators.DataRequired()])

#register 

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        form = RegisterForm(request.form)
        if request.method =='POST' and form.validate():
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data))

            

            # Create cursor
            cur = mysql.connection.cursor()
            # execute query
            cur.execute("INSERT INTO users(name, email,username,password) VALUES(%s,%s,%s,%s )",(name, email, username, password))

            # commit to db
            mysql.connection.commit()

            # close connection
            cur.close()

            flash('You are now registered and can login','success')

            return redirect(url_for('login'))
        return render_template('register.html', form=form)
    except Exception as e:
        print(e)
        return not_found()

# login
@app.route('/', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            # Get Form Fields
            username = request.form['username']
            password_candidate = request.form['password']

            # create cursor
            cur = mysql.connection.cursor()

            # Get user by username
            result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

            if result > 0:
                # Get stored hash
                data = cur.fetchone()
                password = data['password']
                #thinking of using it to fill created_by field in products table
                admin_id = data['ID']
                # compare passwords
                if sha256_crypt.verify(password_candidate, password):
                    # passed
                    session['logged_in'] =True
                    session['username'] = username
                    session['ID'] = admin_id

                    flash('You are now logged in as '+ session['username'], 'success')
                    # to check if i managed to get the user id flash(admin_id,'success')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid login'
                    return render_template('login.html', error=error)

                    # close conn
                    cur.close()
            else:
                error = 'Username not found'
                return render_template('login.html', error = error)
                
        return render_template('login.html')
    except Exception as e:
        print(e)
        return not_found()

@app.route('/logout')
def logout():
    #session.pop('username',None)
    flash('You logged out', 'success')
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/insert', methods=['GET', 'POST'])
def insert():
    try:
        if request.method == 'POST':

            flash('data inserted successfully','success')

            #prod_id = request.form['prod_id']
            package_no = request.form['package_no']
            name = request.form['name']
            descr = request.form['descr']
            price = request.form['price']
            created_by = session['ID']#request.form['created_by']
            #date_created = request.form['date_created']
            _prod_id= uuid.uuid4()

            # create cursor
            cur = mysql.connection.cursor()

            cur.execute("INSERT INTO products(prod_id, package_no, name, descr, price, created_by) VALUES(%s,%s,%s,%s,%s,%s)",(_prod_id,package_no,name,descr,price,created_by))
            mysql.connection.commit()
            return redirect(url_for('products'))
        else:
            return not_found()
    except Exception as e:
        print(e)
        return not_found()
        
@app.route('/update', methods = ['POST', 'GET'])
def update():
    try:
        
        if request.method == 'POST':
            prod_id = request.form['prod_id']
            package_no = request.form['package_no']
            name = request.form['name']
            descr = request.form['descr']
            price = request.form['price']
            #created_by = request.form['created_by']
            #date_created = request.form['date_created']

            sql = "UPDATE products SET prod_id=%s, package_no=%s,name=%s, descr=%s, price=%s WHERE prod_id=%s"
            arg = (prod_id,package_no,name,descr,price,prod_id)

            cur = mysql.connection.cursor()        
            cur.execute(sql, arg )
            mysql.connection.commit()
            
            flash("successfully updated",'success')

            return redirect(url_for('products'))
        else:
            return not_found()
    except Exception as e:
        print(e)
        return not_found()

 


@app.route('/delete/<string:prod_id>', methods=['GET', 'POST'])
def delete(prod_id):
    try:
        flash("data deleted successfully","success")
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM products WHERE prod_id = %s", (prod_id,))
        mysql.connection.commit()
        return redirect(url_for("products"))
    except Exception as e:
        print(e)
        return not_found() 


@app.route('/products')
def products():
    try:
        cur=mysql.connection.cursor()
        cur.execute("SELECT * FROM products")        
        data = cur.fetchall()        
        cur.close()

        return render_template('products.html', products = data)
    except Exception as e:
        print(e)
        return not_found()

@app.route('/insertCus', methods=['POST','GET'])
def insertCus():
    if request.method == 'POST':


        name = request.form['name']
        email = request.form['email']
        phone_no = request.form['phone_no']
        dob = request.form['dob']
        location = request.form['location']
        #date_checked = request.form['date_checked']
        prod_id = request.form['prod_id']
        

        cur = mysql.connection.cursor()
        #check if product is there in products table
        qry = "SELECT * FROM products WHERE prod_id=%s"
        result = cur.execute(qry,[prod_id])
        
        if result > 0:
            #check if product is there in customers table
            qryy = "SELECT * FROM customers WHERE prod_id=%s"
            res = cur.execute(qryy,[prod_id])
            #if  product is there in table customers it means its a second check hence refill
            if res > 0:
                typee = "refill"

                sql = "INSERT INTO refill(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                arg = (name, email, phone_no, dob, location, prod_id, typee)
                cur.execute(sql, arg)
                mysql.connection.commit()

                flash("successfully inserted refill",'success')

                return redirect(url_for('customers'))
            #if  product is not there in table customers it means its a 1st check hence genuine
            else:

                typee = "genuine"

                sql = "INSERT INTO customers(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                arg = (name, email, phone_no, dob, location, prod_id, typee)
                cur.execute(sql, arg)
                mysql.connection.commit()

                flash("successfully inserted genuine",'success')

                return redirect(url_for('customers'))
        #if  product is not there in table products it means its an invalid product hence counterfeit
        else:

            typee = "countrft"

            sql = "INSERT INTO counterfeit(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
            arg = (name, email, phone_no, dob, location, prod_id, typee)
            cur.execute(sql,arg)
            mysql.connection.commit()

            flash("This is a counterfeit product",'success')

            return redirect(url_for('customers'))

@app.route('/verify_prod', methods=['POST','GET'])
def verifyProd():
    if request.method == 'POST':


        name = request.form['name']
        email = request.form['email']
        phone_no = request.form['phone_no']
        dob = request.form['dob']
        location = request.form['location']
        #date_checked = request.form['date_checked']
        prod_id = request.form['prod_id']
        

        cur = mysql.connection.cursor()
        #check if product is there in products table
        qry = "SELECT * FROM products WHERE prod_id=%s"
        result = cur.execute(qry,[prod_id])
        
        if result > 0:
            #check if product is there in customers table
            qryy = "SELECT * FROM customers WHERE prod_id=%s"
            res = cur.execute(qryy,[prod_id])
            #if  product is there in table customers it means its a second check hence refill
            if res > 0:
                typee = "refill"

                sql = "INSERT INTO refill(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                arg = (name, email, phone_no, dob, location, prod_id, typee)
                data = cur.execute(sql, arg)
                mysql.connection.commit()

                resp = jsonify(data) #("successfully inserted refill")
                resp.status_code =200

                cur.close()

                return resp
            #if  product is not there in table customers it means its a 1st check hence genuine
            else:

                typee = "genuine"

                sql = "INSERT INTO customers(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                arg = (name, email, phone_no, dob, location, prod_id, typee)
                data = cur.execute(sql, arg)
                mysql.connection.commit()

                resp = jsonify(data)#jsonify("successfully inserted genuine")
                resp.status_code =200

                cur.close()

                return resp
        #if  product is not there in table products it means its an invalid product hence counterfeit
        else:

            typee = "countrft"

            sql = "INSERT INTO counterfeit(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
            arg = (name, email, phone_no, dob, location, prod_id, typee)
            cur.execute(sql,arg)
            mysql.connection.commit()

            data ={
                    'message':'This is a counterfeit',
            }

            resp = jsonify(data)#jsonify("This is a counterfeit")
            resp.status_code=200
            return resp

@app.route('/updateCus',methods=['POST','GET'])
def updateCus():
    try:
        if request.method == 'POST':

            check_no = request.form['check_no']
            name = request.form['name']
            email = request.form['email']
            phone_no = request.form['phone_no']
            dob = request.form['dob']
            location = request.form['location']
            #date_checked = request.form['date_checked']
            prod_id = request.form['prod_id']
            typee = request.form['type']

            cur = mysql.connection.cursor()
            sql = "UPDATE customers SET name=%s, email=%s, phone_no=%s, dob=%s, location=%s, prod_id=%s, type=%s WHERE check_no=%s"
            arg = (name,email,phone_no,dob,location,prod_id,typee,check_no)
            cur.execute(sql,arg)
            mysql.connection.commit()

            flash('Successfully Updated','success')
            return redirect(url_for('customers'))
    except Exception as e:
        print(e)
        return not_found()    

@app.route('/deleteCus/<string:check_no>',methods=['POST','GET'])
def deleteCus(check_no):
    try:
        flash("data deleted successfully","success")

        cur = mysql.connection.cursor()

        sql = "DELETE FROM customers WHERE check_no=%s"
        arg = (check_no)

        cur.execute(sql,arg)
        mysql.connection.commit()

        return redirect(url_for('customers'))
    except Exception as e:
        print(e)
        return not_found()        

@app.route('/customers')
def customers():
    try:
        cur=mysql.connection.cursor()

        cur.execute("SELECT * FROM customers")
        data = cur.fetchall()

        cur.close()

        return render_template('customers.html', customers = data)
    except Exception as e:
        print(e)
        return not_found()
    

@app.route('/counterfeit')
def counterfeit():
    try:
        cur = mysql.connection.cursor()
        sql = "SELECT * FROM counterfeit"
        cur.execute(sql)
        data = cur.fetchall()
        cur.close()

        return render_template('counterfeit.html', counterfeits = data)
    except Exception as e:
        print(e)
        return not_found()

@app.route('/refill')
def refill():
    try:
        cur = mysql.connection.cursor()
        sql = "SELECT * FROM refill"
        cur.execute(sql)
        data = cur.fetchall()
        cur.close()

        return render_template('refill.html', refill = data)
    except Exception as e:
        print(e)
        return not_found()

#promotions page
@app.route('/promotions')
def promotions():
    try:
        cur = mysql.connection.cursor()
        sql = "SELECT*FROM promotions"
        querry = "SELECT phone_no, count(*) as Total_Purchase FROM customers GROUP BY phone_no ORDER BY Total_Purchase DESC LIMIT 1"
        cur.execute(sql)
        data = cur.fetchall()
        cur.execute(querry)
        points= cur.fetchall()

        cur.close()
        return render_template('promotions.html', promodata = data, points = points)
    except Exception as e:
        print(e)
        return not_found()
#create promotion page
@app.route('/create_promotion', methods = ['POST','GET'])
def createPromotion():
    try:
        
               
        if request.method == 'POST':
            flash('Promotion created successfully','success')

            _descr = request.form['descr']
            _winner_phone = request.form['winner_phone']
            _points = request.form['points']

            cur = mysql.connection.cursor()
            sql = "INSERT INTO promotions(descr,winner_phone,points) VALUES(%s,%s,%s)"
            arg = (_descr, _winner_phone, _points,)
            cur.execute(sql,arg)
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('promotions'))
    except Exception as e:
        print(e)
        return not_found()
    
#highest selling product
@app.route('/sales')
def sales():
    cur = mysql.connection.cursor()
    #cur.execute("SELECT prod_id, count(*) as Sales FROM customers GROUP BY prod_id ORDER BY Sales DESC" )
    #SELECT products.name , count(products.prod_id) as Sales FROM customers LEFT JOIN products ON customers.prod_id = products.prod_id WHERE type='genuine' GROUP BY products.name ORDER BY Sales DESC;
    cur.execute("SELECT products.name , count(products.prod_id) as Sales FROM customers LEFT JOIN products ON customers.prod_id = products.prod_id WHERE type='genuine' GROUP BY products.name ORDER BY Sales DESC" )
        
    data = cur.fetchall()
    #creating barcchart object from the pygal lib
    chart = pygal.Bar()
    #setting x-axis and y-axis. To add the sales on y and i will read the sales as a list from Json
    sales_list = [x['Sales'] for x in data]
    #similarly we read the name from the JSON data object as a list
    [x['name'] for x in data]
    #Assign the X axis and Y axis data to the chart object.
    chart.add('Product Sales', sales_list)
    chart.x_labels = [x['name'] for x in data]
    #render svg image
    chart.render_to_file('static/images/bar_chart.svg')
    img_url = 'static/images/bar_chart.svg?cache=' + str(time.time())

    cur.close()
    return render_template('reports.html', genuine = data, image_url = img_url)

#Highest sales---search by name
#SELECT products.name , count(products.prod_id) as Sales FROM customers LEFT JOIN products ON customers.prod_id = products.prod_id WHERE products.name='Acetaminophen' GROUP BY products.name;
@app.route('/filterName', methods = ['POST','GET'])
def filterName():
    try:
        
        if request.method == 'POST':
            _name = request.form['name']

            cur = mysql.connection.cursor()

            cur.execute("SELECT products.name as name , count(products.prod_id) as Sales FROM customers LEFT JOIN products ON customers.prod_id = products.prod_id WHERE products.name=%s GROUP BY products.name", (_name,))
            data = cur.fetchall()
            cur.close

            return render_template('searchsales.html', data= data)
        else:
            
            return not_found()

    except Exception as e:
        print(e)
    
#highest selling location
@app.route('/location_sales')
def locationSales():

    cur = mysql.connection.cursor()

    cur.execute("SELECT location, count(*) as Total_sales FROM customers  GROUP BY location ORDER BY Total_sales DESC ")

    data = cur.fetchall()

    #creating barcchart object from the pygal lib
    chart = pygal.Bar()
    #setting x-axis and y-axis. To add the sales on y and i will read the sales as a list from Json
    location_sales_list = [x['Total_sales'] for x in data]
    #similarly we read the name from the JSON data object as a list
    [x['location'] for x in data]
    #Assign the X axis and Y axis data to the chart object.
    chart.add('Location Sales', location_sales_list)
    chart.x_labels = [x['location'] for x in data]
    #render svg image
    chart.render_to_file('static/images/bar_chart_loc.svg')
    img_url = 'static/images/bar_chart_loc.svg?cache=' + str(time.time())

    cur.close()
    return render_template('location_sales.html', refill = data, image_url = img_url)
#search by location
@app.route('/filterLocation', methods = ['POST', 'GET'])
def filterLocation():
    if request.method == 'POST':
        location = request.form['location']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT location, count(*) as Total_sales FROM customers where location=%s", (location,))
        data =  cur.fetchall()
        cur.close()

        return render_template('searchlocation.html', loc = data)

#most counterfeited product/ reports
@app.route('/counterfeit_sales',methods=['POST','GET'])
def fake():
    
    cur = mysql.connection.cursor()
    sql = "SELECT prod_id, count(*) as Total_conterfeits FROM refill GROUP BY prod_id ORDER BY Total_conterfeits DESC"
    #"SELECT * FROM counterfeit"
    cur.execute(sql)

    data = cur.fetchall()

    #creating barcchart object from the pygal lib
    chart = pygal.Bar()
    #setting x-axis and y-axis. To add the sales on y and i will read the sales as a list from Json
    counterfeit_sales_list = [x['Total_conterfeits'] for x in data]
    #similarly we read the name from the JSON data object as a list
    [x['prod_id'] for x in data]
    #Assign the X axis and Y axis data to the chart object.
    chart.add('Counterfeit graph', counterfeit_sales_list)
    chart.x_labels = [x['prod_id'] for x in data]
    #render svg image
    chart.render_to_file('static/images/bar_chart_cou.svg')
    img_url = 'static/images/bar_chart_cou.svg?cache=' + str(time.time())

    cur.close()
        

    return render_template('fake.html', fake = data, image_url = img_url)

@app.route('/refill_by_name', methods = ['GET','POST'])
def refillbyName():
    if request.method == 'POST':
        _name = request.form['name']
        

        cur = mysql.connection.cursor()
        cur.execute("SELECT products.name as name , count(products.prod_id) as Sales FROM refill LEFT JOIN products ON refill.prod_id = products.prod_id WHERE products.name=%s", (_name,))

        data = cur.fetchall()
        cur.close()

        return render_template('refill_by_name.html', data = data)

#invalid products
@app.route('/invalid' ,methods=['POST','GET'])
def invalid():
    
    cur = mysql.connection.cursor()
    sql = "SELECT prod_id, count(*) as Total_Invalid FROM counterfeit GROUP BY prod_id ORDER BY Total_Invalid DESC"
    #"SELECT * FROM counterfeit"
    cur.execute(sql)

    data = cur.fetchall()

    #creating barcchart object from the pygal lib
    chart = pygal.Bar()
    #setting x-axis and y-axis. To add the sales on y and i will read the sales as a list from Json
    invalid_sales_list = [x['Total_Invalid'] for x in data]
    #similarly we read the name from the JSON data object as a list
    [x['prod_id'] for x in data]
    #Assign the X axis and Y axis data to the chart object.
    chart.add('invalid graph', invalid_sales_list)
    chart.x_labels = [x['prod_id'] for x in data]
    #render svg image
    chart.render_to_file('static/images/bar_chart_inv.svg')
    img_url = 'static/images/bar_chart_inv.svg?cache=' + str(time.time())

    cur.close()
        

    return render_template('invalid.html', invalid = data, image_url = img_url)
#search by id in invalid
@app.route('/search_invalid', methods = ['GET','POST'])
def searchInvalid():
    if request.method == 'POST':
        _prod_id = request.form['prod_id']
        

        cur = mysql.connection.cursor()
        cur.execute("SELECT prod_id, count(*) as Total_Invalid FROM counterfeit where prod_id=%s", (_prod_id,))

        data = cur.fetchall()
        cur.close()

        return render_template('search_invalid.html', data = data)

# API for json get
@app.route('/get_products', methods = ['GET'])
def getProduct():
    try:
        if request.method == 'GET':
            cur = mysql.connection.cursor()
            sql = "SELECT*FROM products"
            cur.execute(sql)
            rows = cur.fetchall()

            resp=jsonify(rows)
            resp.status_code = 200
            return resp
        else:
            return not_found()
            
    except Exception as e:
        print(e)
    finally:
        cur.close()
    
#API for insert json(add customer-verification of product by customer)
@app.route('/add_customer', methods = ['POST'])
def addCustomer():
    try:
        _name = request.form['name']
        _email = request.form['email']
        phonee = request.form['phone_no']
        _phone_no = '+263'+phonee
        _dob = request.form['dob']
        _location = request.form['location']
        #date_checked = request.form['date_checked']
        _prod_id = request.form['prod_id']
        #_typee = "refill"

        if request.method == 'POST':
            #checking if product is there in products table
            cur = mysql.connection.cursor()

            sql = "SELECT*FROM products where prod_id=%s"
            arg = (_prod_id,)
            rows= cur.execute(sql,arg)
            
            

            resp = jsonify('User found in products!')
            resp.status_code = 200

            if rows > 0:

                #either refill or genuine since the prod is there in products
                #get name and id from table
                data = cur.fetchone()
                product_name = data['name']
                product_id = data['prod_id']
                created_date = data['date_created']               

                sql = "SELECT*FROM customers WHERE prod_id=%s"
                arg = (_prod_id,)
                row_cus = cur.execute(sql,arg)

                resp = jsonify('User found in customers!')
                resp.status_code = 200

                if row_cus > 0:
                    #refill
                    _typee = "refill"

                    sql = "INSERT INTO refill(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                    arg = (_name, _email, _phone_no, _dob, _location, _prod_id, _typee)
                    cur.execute(sql,arg)
                    mysql.connection.commit()

                    resp = jsonify('Product name: '+product_name+'\nProduct id: '+product_id+'\nCreated on:'+str(created_date)+'\n\nSorry, the product have been used before.\n Buy a genuine product to be safe & enter our promotion')
                    resp.status_code = 200

                    cur.close()
                    
                    return resp

                else:
                    #genuine
                    _typee = "genuine"

                    sql = "INSERT INTO customers(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                    arg = (_name, _email, _phone_no, _dob, _location, _prod_id, _typee)
                    cur.execute(sql,arg)

                    mysql.connection.commit()

                    resp = jsonify('Product name: '+product_name+'\nProduct id: '+product_id+'\n\nCongrats, the product is genuine.\n You have been selected to compete in our promotion')
                    resp.status_code = 200

                    cur.close()
                    
                    return resp
            else:
                #counterfeit
                _typee = "cntrfeit"
                sql = "INSERT INTO counterfeit(name, email, phone_no, dob, location, prod_id, type) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                arg = (_name, _email, _phone_no, _dob, _location, _prod_id, _typee)
                cur.execute(sql,arg)

                mysql.connection.commit()

                resp = jsonify('Sorry, the product is invalid!\nBuy a genuine product to be safe and enter our promotions.')
                resp.status_code = 200

                cur.close()
                
                                
                return resp
        else:
            return not_found()

    except Exception as e:
        print(e)
        return jsonify('user not added')
    finally:
        cur.close()

#API for insert json(add pharmacist-verification of package by pharmacist)
@app.route('/verify_package', methods = ['POST'])
def verifyPackage():
    try:
        _package_no = request.form['package_no']

        if request.method == 'POST':
            cur = mysql.connection.cursor()

            sql = "SELECT*FROM products WHERE package_no=%s"
            arg = (_package_no,)
            rows = cur.execute(sql,arg)

            if rows > 0:
                #package found
                resp = jsonify('Congrats, genuine package\nYou are advised to accept this package.')
                resp.status_code = 200
                return resp

            else:
                #fake  
                resp = jsonify('Sorry, the package is a counterfeit\nYou are advised not to accept this package and report it to the supplier.')
                resp.status_code = 200
                return resp       
                
        
    except Exception as e:
        print(e)
        return not_found()
        


#error handler
@app.errorhandler(404)
def not_found(error = None):
    
    message='Not Found '+request.url

    resp = message
    

    return resp

		
		
if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True,host='0.0.0.0')

