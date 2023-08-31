from flask_login import login_required, current_user
from . import db
from .models import Employee,Attendance,Shift_time
from flask import Blueprint, render_template, request, flash, redirect, url_for,jsonify
import json
import datetime

import pandas as pd
from flask import current_app as app
from datetime import datetime, timedelta
import os
from .funcations import *
views = Blueprint('views', __name__)


@views.route('/',methods=['POST','GET'])
@login_required
def admin():
    try:
        inshift = Shift_time.query.filter_by(id=1).first()
        if not inshift:
            file_path = os.path.join(app.config['Excel_FOLDER'], '01-08-23.xls')
            process_excel_data(file_path)  # Call the data processing function
        else:
            print("Shift not found")

    except Exception as e:
        print("Error occurred:", e)
        db.session.rollback()  # Rollback in case of error
    
    # employee =Employee.query.order_by(Employee.id)
    employee =Attendance.query.order_by(Attendance.id)   
    # sihft=Shift_time.query.order_by(Shift_time.id) 
    return render_template('admin.html',employee=employee)

@views.route('/edit', methods=['POST', 'GET'])
@login_required
def empEdit():
    if request.method == 'POST':
        empid = request.form.get('empid')
        name = request.form.get('name')
        dob = request.form.get('dob')
        workType = request.form.get('workType')
        phoneNumber = request.form.get('phoneNumber')
        adharNumber = request.form.get('adharNumber')
        wages_per_Day = request.form.get('wages_per_Day')
        gender = request.form.get('gender')
        address = request.form.get('address')
        dob_date = datetime.strptime(dob, '%Y-%m-%d').date()

        # Query the database for an employee with the given 'empid'
        emp = Employee.query.filter_by(id=empid).first()

        if emp:
            # Update the employee's data with the new information
            emp.name = name
            emp.dob = dob_date
            emp.workType = workType
            emp.phoneNumber = phoneNumber
            emp.adharNumber = adharNumber
            emp.wages_per_Day = wages_per_Day
            emp.gender = gender
            emp.address = address

            # Commit the changes to the database
            db.session.commit()
        else:
            flash('Employee not found!', 'error')

        # Redirect the user to the 'admin' page or route.
    return redirect(url_for('views.admin'))
    
        
@views.route('/delete-emp',methods=['POST'])
@login_required
def delete_employee():
    try:
        data = request.get_json()
        print(data)
        
        if not data or 'EmpId' not in data:
            return jsonify({'error': 'Invalid request data. EmpId is missing.'}), 400

        emp_id = data['EmpId']
        

        # Check if an employee with the given emp_id exists in the database
        employee = Employee.query.filter_by(id=int(emp_id)).first()
        
        attendance=Attendance.query.filter_by(id=int(emp_id)).all()
        for record in attendance:
            db.session.delete(record)

        if employee is None:
            return jsonify({'error': 'Employee not found.'}), 404

        # If the employee is found, delete the record from the database
        db.session.delete(employee)
        
        db.session.commit()

        return jsonify({'message': 'Employee deleted successfully.'}), 200

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

    return "Employee deleted successfully!", 200

   
    
    
@views.route('/profile-view')
@login_required
def profileView():
    try: 
        
        employee =Employee.query.order_by(Employee.id)
        
        
    except Exception as error:
        flash(error)
    current_date = datetime.now().date()
    return render_template('profile.html',employee=employee,current_date=current_date)


@views.route('/calculate',methods=['POST','GET'])
def calculate():
    
    calculate_Attendance()
    # lol=Shift_time.query.filter_by(id=5).first()
    # lol.shiftIntime="14:00"
    # lol.shift_Outtime="22:00"
    # db.session.commit()
    # print(lol.shift_Outtime)
    
    return redirect('/')
            
# @views.route('/getshift',methods=['POST','GET'])
# def get_shift():
#     try:
#         inshift = Shift_time.query.filter_by(id=1).first()
#         if not inshift:
#             file_path = os.path.join(app.config['Excel_FOLDER'], '01-08-23.xls')
#             process_excel_data(file_path)  # Call the data processing function
#         else:
#             print("Shift not found")

#     except Exception as e:
#         print("Error occurred:", e)
#         db.session.rollback()  # Rollback in case of error
    
#     return redirect(url_for('views.viewShift'))  # Redirect to viewShift after processing
    
 # new_shift = Shift_time(shiftIntime="06:00",shift_Outtime="14:00",shiftType="8A",work_Duration="08:00")
    # db.session.add(new_shift)
    # db.session.commit()
    # emp=Attendance.query.get(2)
    # emp.inTime="08:16"
    # emp.outTime="18:56"
    # db.session.commit()
@views.route('/shift')
def viewShift():
    
    records=Shift_time.query.order_by(Shift_time.id)  
    return render_template('shift.html',records=records)

@views.route('/attendance')
def readXl_update_atten():
    try:
        excel_file_path = os.path.join(app.config['Excel_FOLDER'], 'duplicate_data_updated.xlsx')
        print("EXCEL", excel_file_path)
        attend_excel_data(excel_file_path)  # Call the data processing function
        
        db.session.commit()  # Commit the changes
        flash("Employee data updated successfully.", "success")  # Provide a success message
        
    except Exception as e:
        print("Error occurred:", e)
        db.session.rollback() 
        flash("An error occurred while updating employee data.", "error")
    
    return redirect(url_for('views.calculate'))


