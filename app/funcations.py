from datetime import datetime, timedelta
import smtplib
import os
from flask import current_app as app
from flask import  flash,redirect
from .models import Employee, Attendance, Shift_time
from . import db
from os import path
import datetime
import sched
import time
from datetime import datetime, timedelta

import pandas as pd
scheduler = sched.scheduler(time.time, time.sleep)

def send_mail(email, body):
    sender_email = ""
    receiver_email = email
    password = ""
    message = body

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
    print('*****Email sent!*****')
    server.quit()
    
def process_excel_data(file_path):
    if os.path.exists(file_path):
        sheet_names = pd.ExcelFile(file_path).sheet_names

        for sheet_name in sheet_names:
            df = None
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl', skiprows=1)
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd', skiprows=1)
            else:
                print("Unsupported file format")
                return  # Handle unsupported format

            for index, row in df.iterrows():
                shift_type = row['Shift']
                print("Processing: ", shift_type)

                existing_shift = db.session.query(Shift_time).filter_by(shiftType=shift_type).first()
                if not existing_shift:
                    print("Adding new shift")
                    shift = Shift_time(
                        shiftIntime=str(row['S. InTime']),
                        shift_Outtime=str(row['S. OutTime']),
                        shiftType=str(row['Shift']),
                        work_Duration=str(row['Work Duration'])
                    )
                    db.session.add(shift)

        db.session.commit()
    else:
        print("File not found")

def calculate_Attendance():
    employees = Employee.query.all()

    for employee in employees:
        attendance_records = Attendance.query.filter_by(emp_id=employee.id).all()

        for attendance in attendance_records:
            # Extract attendance information
            print("SF: ", attendance.shift)
            shift = Shift_time.query.filter_by(id=1).first()
            print("SHIFT: ", shift)
            inTime = attendance.inTime
            print("IN TIME: ", inTime)
            shiftIntime = shift.shiftIntime
            print("SHIFT INTIME:", shiftIntime)
            shiftOuttime = shift.shift_Outtime

            # Calculate the lateBy time
            lateBy = calculate_time_difference(shiftIntime, inTime)
            
                
            attendance.lateBy = lateBy
            

            if attendance.outTime != "00:00":
                outTime = attendance.outTime

                # Calculate the earlyGoingBy time
                earlyGoingBy = calculate_time_difference(shiftOuttime, outTime)
                if "-" in earlyGoingBy:
                    attendance.earlyGoingBy = "00:00"
                else:
                    attendance.earlyGoingBy = earlyGoingBy

                # Calculate the time duration between inTime and outTime
                time_worked = calculate_time_difference(outTime, inTime)
                print("Time Worked: ", time_worked)
                if "-" in time_worked:
                    attendance.TotalDuration = "00:00"
                else:
                    attendance.TotalDuration = time_worked

                # Calculate the overtime hours
                overtime_hours = calculate_time_difference(outTime, shiftOuttime)
                print("OVER TIME: ", overtime_hours)
                
                
                attendance.overtime = overtime_hours
                print("attendance.overtime: ",attendance.overtime)
                return db.session.commit()
                
            else:
                out_time = datetime.now().strftime("%H:%M")
                earlyGoingBy = calculate_time_difference(out_time, shiftOuttime)
                attendance.earlyGoingBy = earlyGoingBy
                attendance.TotalDuration = calculate_time_difference(inTime, out_time)
                attendance.overtime = "00:00"
'''def calculate_time_difference(time1_str, time2_str):
    # Convert time strings to datetime objects
    time1 = datetime.strptime(time1_str, '%H:%M')
    time2 = datetime.strptime(time2_str, '%H:%M')
    # Find the minimum and maximum time
    # min_time = min(time1, time2)
    # max_time = max(time1, time2)

  
    # Calculate the time difference
    time_difference = time1-time2
    if time_difference.total_seconds() < 0:
        time_difference += datetime.timedelta(days=1)

    # Calculate the total minutes in the time difference
    total_minutes = time_difference.total_seconds() // 60

    # Calculate hours and remaining minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60

    # Format the time difference as H:MM
    formatted_difference = f"{int(hours)}:{int(minutes):02d}"
    return formatted_difference'''

def calculate_time_difference(time1_str, time2_str):
    # Convert time strings to datetime objects
    time1 = datetime.strptime(time1_str, '%H:%M')
    time2 = datetime.strptime(time2_str, '%H:%M')
    
    # Calculate time difference
    time_difference = time2 - time1
    
    # Calculate total minutes
    total_minutes = time_difference.total_seconds() // 60

    # Calculate positive time difference by considering the 24-hour clock
    if total_minutes < 0:
        total_minutes += 24 * 60  # Adding 24 hours' worth of minutes
    
    hours = total_minutes // 60
    minutes = total_minutes % 60

    formatted_difference = f"{int(hours)}:{int(minutes):02d}"
    return formatted_difference

def update_wages_for_present_employees():
    
    current_date = datetime.datetime.now().date()

  
    employees = Employee.query.filter_by(workType='employee').all()

    for employee in employees:
        
        attendance_for_today = Attendance.query.filter_by(emp_id=employee.id, date=current_date).first()

        if attendance_for_today and attendance_for_today.attendance == 'present':
            # If the employee is present, increase the wages_per_Day by 1 for that day
            employee.wages_per_Day = str(int(employee.wages_per_Day) + 1)

   
    return db.session.commit()


def update_wages_for_present_daily_workers():
    
    current_date = datetime.datetime.now().date()

  
    employees = Employee.query.filter_by(workType='daily').all()

    for employee in employees:
        
        attendance_for_today = Attendance.query.filter_by(emp_id=employee.id, date=current_date).first()

        if attendance_for_today and attendance_for_today.attendance == 'present':
            # If the employee is present, increase the wages_per_Day by 1 for that day
            employee.wages_per_Day = str(int(employee.wages_per_Day) + 1)

   
    return db.session.commit()

def schedule_next_sunday():
    # Calculate the time until the next Sunday
    now = datetime.now()
    days_until_sunday = (6 - now.weekday()) % 7  # Sunday is 6 in the Python datetime weekday representation
    next_sunday = now + timedelta(days=days_until_sunday)

    # Schedule the function to run on the next Sunday at midnight (00:00:00)
    next_sunday_midnight = datetime(next_sunday.year, next_sunday.month, next_sunday.day)
    scheduler.enterabs(time.mktime(next_sunday_midnight.timetuple()), 1, run_for_all_employees, ())

 


def count_attendance_and_update_shift(emp_id):
    # Get the employee's attendance records
    employee = Employee.query.get(emp_id)
    if employee:
        attendance_count = len(employee.attendance)
        
        # Update the shift if the attendance count is 6
        if attendance_count == 6:
            employee.shift = "New Shift Value"  # Replace "New Shift Value" with the appropriate value
            db.session.commit()
        
        return attendance_count
    else:
        return 0
    
def count_attendance_and_update_shift_periodic(emp_id):
    # Replace employee_id_to_check with the actual employee ID you want to check
    attendance_count = count_attendance_and_update_shift(emp_id)
    print(f"Attendance Count for Employee ID {emp_id}: {attendance_count}")



def run_for_all_employees():
    # Assuming Employee is your SQLAlchemy model for employees
    employees = Employee.query.filter_by(workType='employee').all()

    for employee in employees:
        count_attendance_and_update_shift_periodic(employee.id)

    # Schedule the function to run again on the next Sunday
    schedule_next_sunday()



def attend_excel_data(file_path):
    if os.path.exists(file_path):
        sheet_names = pd.ExcelFile(file_path).sheet_names

        for sheet_name in sheet_names:
            df = None
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd')
            else:
                print("Unsupported file format")
                return  # Handle unsupported format

            for index, row in df.iterrows():
                empid = row['emp_id']
                print("Processing: ", empid)
                date=pd.to_datetime(row['date']) if pd.notna(row['date']) else None
                existing_emp = db.session.query(Employee).filter_by(id=empid).first()
                if  existing_emp:
                    
                    if str(row['intime']) =="00:00" and str(row['outtime'])== "00:00":
                            
                            existing_emp.emp_id=empid,
                            existing_emp.inTime=str(row['intime']),
                            existing_emp.shift_Outtime=str(row['outtime']),
                            existing_emp.shiftType=existing_emp.attendances.shift,
                            existing_emp.attendance='Absent',
                            existing_emp.date=date
                        
                        
                    else:
                                      
                            existing_emp.emp_id=empid,
                            existing_emp.inTime=str(row['intime']),
                            existing_emp.shift_Outtime=str(row['outtime']),
                            existing_emp.shiftType=existing_emp.attendances.shift,
                            existing_emp.attendance='Present',
                            existing_emp.date=date
                        
                       
                        

        db.session.commit()
    else:
        print("File not found")


def addemployee(file_path):
    if os.path.exists(file_path):
        sheet_names = pd.ExcelFile(file_path).sheet_names
        

        for sheet_name in sheet_names:
            df = None
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
            elif file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path, sheet_name, engine='xlrd')
            else:
                
                return print("Unsupported file format")  # Handle unsupported format
            
            for index, row in df.iterrows():
                empid = row['emp_id']
                print("Processing: ", empid)
                dob = pd.to_datetime(row['dob']) if pd.notna(row['dob']) else None

                existing_emp = db.session.query(Employee).filter_by(id=empid).first()
                if not existing_emp:
                    # Create and add a new Employee only if it doesn't exist
                    new_employee = Employee(
                        id=empid,  # Assuming emp_id is the primary key
                        name=row["name"],
                        dob=dob,
                        designation=row["designation"],
                        workType=row["workType"],
                        email=row["email"],
                        phoneNumber=row["phoneNumber"],
                        adharNumber=row["adharNumber"],
                        gender=row["gender"],
                        address=row["address"],
                        shift=row["shift"]
                    )
                    db.session.add(new_employee)
                else:
                    print(f"Employee with ID {empid} already exists.")

        db.session.commit()
        print("Data added successfully.")
    else:
        print("File not found")



