from datetime import datetime, timedelta
import smtplib
import schedule
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
            shift = Shift_time.query.filter_by(shiftType=attendance.employee.shift).first()
            inTime = attendance.inTime
            shiftIntime = shift.shiftIntime
            shiftOuttime = shift.shift_Outtime

            # Calculate the lateBy time
            lateBy = calculate_time_difference(shiftIntime, inTime)
            attendance.lateBy = lateBy

            if attendance.outTime != "00:00":
                outTime = attendance.outTime

                # Calculate the earlyGoingBy time
                #
                earlyGoingBy = calculate_time_difference(outTime, shiftOuttime)
                if "-" in earlyGoingBy:
                    attendance.earlyGoingBy = "00:00"
                else:
                    attendance.earlyGoingBy = earlyGoingBy

                # Calculate the time duration between inTime and outTime
                time_worked = calculate_time_difference(outTime, inTime)
                if "-" in time_worked:
                    attendance.TotalDuration = "00:00"
                else:
                    attendance.TotalDuration = time_worked

                # Calculate the overtime hours
                overtime_hours = calculate_time_difference(shiftOuttime, outTime)
                attendance.overtime = overtime_hours
            else:
                out_time = datetime.now().strftime("%H:%M")
                earlyGoingBy = calculate_time_difference(out_time, shiftOuttime)
                attendance.earlyGoingBy = earlyGoingBy
                attendance.TotalDuration = calculate_time_difference(inTime, out_time)
                attendance.overtime = "00:00"
            
            # Commit the changes for each attendance record
            db.session.commit()




def calculate_time_difference(time1_str, time2_str):
    # Convert time strings to datetime objects (without seconds)
    time_format = '%H:%M'
    time1 = datetime.strptime(time1_str, time_format)
    time2 = datetime.strptime(time2_str, time_format)
    
    # Calculate time difference in seconds
    time_difference_seconds = (time2 - time1).total_seconds()
    print("TEST:",time_difference_seconds)
    
    # Convert seconds to hours and minutes
    total_minutes = time_difference_seconds // 60
    total_hours = total_minutes // 60
    minutes = total_minutes % 60

    formatted_difference = f"{int(total_hours)}:{int(minutes):02d}"
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


# def schedule_function(emp_id):
#     schedule.every(2).days.do(count_attendance_and_update_shift,emp_id)

# schedule_function(emp_id)




def count_attendance_and_update_shift(emp_id):
    # Get the employee's attendance records
    employee = Employee.query.get(emp_id)
    if employee:
        attendance_count = len(employee.attendances)
        print(attendance_count)
        
        # Update the shift if the attendance count is 6
        if attendance_count == 2:

            shifts = ['8G', '8A', '8C', '8B', 'GS', '12A', '12B', '10A']
            current_shift_index = shifts.index(employee.shift)
            new_shift_index = (current_shift_index + 1) % len(shifts)
            employee.shift = shifts[new_shift_index]
            db.session.commit()
        
        return attendance_count()
    else:
        return 0
    
# def schedule_function(emp_id):
#     schedule.every(2).days.at("00:00").do(count_attendance_and_update_shift, emp_id)

# schedule_function(emp_id)

# while schedule.get_jobs():
#     schedule.run_pending()
#     time.sleep(1)

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
    



# def attend_excel_data(file_path):
#     if os.path.exists(file_path):
#         sheet_names = pd.ExcelFile(file_path).sheet_names

#         for sheet_name in sheet_names:
#             df = None
#             if file_path.lower().endswith('.xlsx'):
#                 df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
#             elif file_path.lower().endswith('.xls'):
#                 df = pd.read_excel(file_path, sheet_name, engine='xlrd')
#             else:
#                 print("Unsupported file format")
#                 return  # Handle unsupported format

#             for index, row in df.iterrows():
#                 empid = row['emp_id']
#                 print("Processing: ", empid)
#                 date=pd.to_datetime(row['date']) if pd.notna(row['date']) else None
#                 existing_emp = db.session.query(Employee).filter_by(id=empid).first()
#                 if  existing_emp:
                    
#                     if str(row['intime']) =="00:00" and str(row['outtime'])== "00:00":
                            
#                             existing_emp.emp_id=empid,
#                             existing_emp.inTime=str(row['intime']),
#                             existing_emp.shift_Outtime=str(row['outtime']),
#                             existing_emp.shiftType=existing_emp.attendances.shift,
#                             existing_emp.attendance='Absent',
#                             existing_emp.date=date
                        
                        
#                     else:
                                      
#                             existing_emp.emp_id=empid,
#                             existing_emp.inTime=str(row['intime']),
#                             existing_emp.shift_Outtime=str(row['outtime']),
#                             existing_emp.shiftType=existing_emp.attendances.shift,
#                             existing_emp.attendance='Present',
#                             existing_emp.date=date
                        
                       
                        

      
#     else:
#         print("File not found")


def addemployee(file_path):
    if os.path.exists(file_path):
        _, file_extension = os.path.splitext(file_path)
        
        if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
            sheet_names = pd.ExcelFile(file_path).sheet_names
        elif file_extension.lower() == '.csv':
            sheet_names = [None]  # For CSV, we don't need sheet names
        else:
            return print("Unsupported file format")

        data_to_insert = []

        for sheet_name in sheet_names:
            if file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name, engine='openpyxl')
                else:
                    df = pd.read_excel(file_path, engine='openpyxl')
            elif file_extension.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                return print("Unsupported file format")

            for index, row in df.iterrows():
                empid = row['emp_id']
                print("Processing: ", empid)
                dob = pd.to_datetime(row['dob']) if pd.notna(row['dob']) else None

                existing_emp = db.session.query(Employee).filter_by(id=empid).first()
                if not existing_emp:
                    data_to_insert.append({
                        'id': empid,
                        'name': row['name'],
                        'dob': dob,
                        'designation': row['designation'],
                        'workType': row['workType'],
                        'email': row['email'],
                        'phoneNumber': row['phoneNumber'],
                        'adharNumber': row['adharNumber'],
                        'gender': row['gender'],
                        'address': row['address'],
                        'shift': row['shift']
                    })
                else:
                    print(f"Employee with ID {empid} already exists.")

        if data_to_insert:
            db.session.bulk_insert_mappings(Employee, data_to_insert)
            db.session.commit()
            print("Data added successfully.")
        else:
            print("No new data to add.")
    else:
        print("File not found")


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
                date = pd.to_datetime(row['date']) if pd.notna(row['date']) else None
                existing_emp = db.session.query(Employee).filter_by(id=empid).first()
                if existing_emp:
                    attendance_status = 'Absent' if str(row['intime']) == "00:00" and str(row['outtime']) == "00:00" else 'Present'
                    shift_type = None
                  
                        # Assuming you want to access the first attendance record's shift
                    shift_type = existing_emp.shift
                    shitfTime=  Shift_time.query.filter_by(shiftType=existing_emp.shift).first()
                    attendance = Attendance(
                        emp_id=empid,
                        inTime=str(row['intime']),
                        outTime=str(row['outtime']),
                        shiftType=shift_type,
                        attendance=attendance_status,
                        date=date,
                        shiftIntime=shitfTime.shiftIntime,
                        shift_Outtime=shitfTime.shift_Outtime,
                        
                        
                        
                    )
                    db.session.add(attendance)

        db.session.commit()
    else:
        print("File not found")

def delete_all_employees():
    try:
        db.session.query(Employee).delete()
        db.session.commit()
        print("All employee data deleted successfully.")
    except Exception as e:
        db.session.rollback()
        print("An error occurred:", str(e))

