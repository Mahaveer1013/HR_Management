from flask_login import login_required, login_user, logout_user, current_user
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Login_admin, Employee, Attendance, Shift_time,Backup,LoginEmp
from . import db
import datetime
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError
import time
from datetime import datetime, timedelta
from .funcations import *





auth = Blueprint('auth', __name__)


@auth.route('/admin-login', methods=['POST', 'GET'])
def login():

    admin = Login_admin.query.filter_by(id=1).first()
    if admin:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            dbemail = Login_admin.query.filter_by(email=email).first()
            if dbemail:
                if check_password_hash(dbemail.password, password):
                    login_user(dbemail, remember=True)
                    redirect(url_for('views.admin'))
                    return redirect(url_for('views.admin'))

                else:
                    flash("Incorrect Password", category='error')
            else:
                flash("Incorrect Email")
    else:
        addAdmin = Login_admin(name="Admin", email="vsabarinathan1611@gmail.com", phoneNumber="123456789",
                               password="sha256$idRijyfQJjGQ3s7P$cedf4eb4aaaddab35c3423e31ab70bd5f60fb8b871f18e37ebec2359a818b6db")
        db.session.add(addAdmin)
        db.session.commit()
        print('Created Admin!')
    flash("GIII", category='error')

    return render_template('login.html')


@auth.route('/logut', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/add', methods=['POST', 'GET'])
@login_required
def addemp():
    if request.method == 'POST':
        empid = request.form.get('empid')
        name = request.form.get('name')
        dob = request.form.get('dob')
        workType = request.form.get('worktype')
        phoneNumber = request.form.get('phnumber')
        adharNumber = request.form.get('aadhar')
        wages_per_Day = request.form.get('wages_per_Day')
        gender = request.form.get('gender')
        address = request.form.get('address')
        email = request.form.get('email')
        attendance = request.form.get('attendance')
        shift = request.form.get('shift')
        designation = request.form.get('designation')

        print("Attendance:", attendance)
        print("Shift:", shift)
        print(dob)

        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format for Date of Birth!', 'error')
            return render_template('addemp.html')

        employee = Employee.query.filter_by(id=empid).first()

        if not employee:
            # Create a new employee and add to the database
            new_employee = Employee(
                id=empid,
                email=email,
                name=name,
                dob=dob_date,
                adharNumber=adharNumber,
                address=address,
                gender=gender,
                phoneNumber=phoneNumber,
                workType=workType,
                designation=designation
            )
            db.session.add(new_employee)
            new_user = LoginEmp(email=email,
                                name=name,
                                password=(generate_password_hash(phoneNumber)))
            db.session.add(new_user)
            shiftTime = Shift_time.query.filter_by(shiftType=shift).first()
            if not shiftTime:
                flash("Wrong Shift")
                return ("/")
            else:

                # Create a new attendance record and add to the database
                new_attendance = Attendance(emp_id=empid, shift=shift, attendance=attendance,
                                            shiftIntime=shiftTime.shiftIntime, shift_Outtime=shiftTime.shift_Outtime)
                db.session.add(new_attendance)

            # Commit changes to the database
            db.session.commit()

            flash('Employee added successfully!', 'success')
        else:
            # Employee already exists with the given empid
            flash('Employee with the given ID already exists!', 'error')

    return redirect(url_for('views.admin'))

@auth.route('/attendance', methods=['POST', 'GET'])
@login_required
def attendance():
    if request.method == "POST":
        emp_id = request.form.get('empid')
        emp = Employee.query.filter_by(id=emp_id).first()
        
        if emp:
            wages_per_day = request.form.get('wages')
            in_time = request.form.get('inTime')
            out_time = request.form.get('outTime')
            shift = request.form.get('shift')
            overtime = request.form.get('overTime')
            attendance_status = request.form.get('attendance')
            
            try:
                attend = Attendance.query.filter_by(emp_id=emp.id).first()
                if attend:
                    attend.wages_per_day = wages_per_day
                    attend.inTime = in_time
                    attend.shift = shift
                    attend.outTime = out_time
                    attend.overtime = overtime
                    attend.attendance = attendance_status
                    backup_entry = Backup(

                                emp_id=emp_id,
                                attendance=attend.attendance,
                                wages_per_Day=attend.wages_per_day,
                                inTime=attend.inTime,
                                outTime=attend.outTime,
                                overtime=overtime,
                                shift=shift,
                                shiftIntime=attend.shiftIntime,
                                shift_Outtime=attend.shift_Outtime,
                                TotalDuration=attend.TotalDuration,
                                lateBy=attend.lateBy,
                                earlyGoingBy=attend.earlyGoingBy,
                                punchRecords=attend.punchRecords
                                )
                    
    
# Add and commit the new backup entry
                    db.session.add(backup_entry)
                    
                    
                    db.session.commit()
                    flash("Attendance updated successfully")
                    return redirect('/calculate')
                    
                else:
                    flash("Attendance record not found")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash("An error occurred while updating attendance")
                print("Error:", e)
        else:
            flash("Employee not found")
        
        return redirect('/')
    
    return render_template('attendance.html')

# @db.event.listens_for(Attendance, 'after_update')
# def copy_to_backup_ateend(mapper, connection, target):
#     # Create a new instance of BackupAteend and populate its attributes

#     db.session.commit()