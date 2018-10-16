"""
    This program constantly expects an SMS of a particular format
    The SMS can be know about the laboratory schedule and
    Also to do the laboratory booking for teachers and students.
"""

"""
    This program will be in the server
    e.g For checking schedule
    "Mon Schedule"
    e.g For booking appointment
    "dd/mm/yyyy 02:00 - 04:00 FE14A125", "dd/mm/yyyy 02:00 - 04:00 work/class"
"""
from .pysms import Modem
import os, sys, re, socket, json
import calendar, datetime
from django.db.models import Q
from booking.models import WeekDaySchedule, BookedDates, StaffBookings, StudentBookings, Students, Staff
from time import sleep

messageToSend = "LABORATORY SCHEDULE FOR {}\n"

weekdays = {
    "mon" : ("Monday", 0),
    "tue" : ("Tuesday", 1),
    "wed" : ("Wednesday", 2),
    "thu" : ("Thursday", 3),
    "fri" : ("Friday", 4),
    "sat" : ("Saturday", 5),
    "sun" : ("Sunday", 6),
}



def processMessage(message):
    # convert the whole message into lower case for the sake of case insensitive
    message = message.lower()

    # check if user is requesting for a schedule 
    if "schedule" in message:
        # the message is requiring the laboratory schedule
        day = message.split(" ")[0]

        if day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            qs = WeekDaySchedule.objects.filter(Q(weekDay=weekdays[day][1]) & Q(maxBookingsReached=False))
            message = messageToSend.format(weekdays[day][0].upper())
            for query in qs:
                qs1 = BookedDates.objects.filter(period=qs)
                # indicate if the period is completely free or not
                if qs1:
                    message = message + str(query.fromTime) + " to " + str(query.toTime) + " (" + str(qs1[0].numberOfBookings) + ")\n"
                else:
                    message = message + str(query.fromTime) + " to " + str(query.toTime) + " (FREE)\n"

            return ("request-schedule", message) 

        else: 
            return None
    
    matchobj = re.match(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}) - (\d{2}:\d{2}) (.*)", message)

    if matchobj is not None:
        date = matchobj.group(1)
        fromTime = matchobj.group(2)
        toTime = matchobj.group(3)
        reason = matchobj.group(4)

        print(matchobj.group())
        
        return ("request-booking", date, fromTime, toTime, reason)
    else:
        return None
                
def authenticateUser(phoneNumber, reason, sentBy):
    if sentBy == "Student":
        qs = Students.objects.filter(Q(phoneNumber=phoneNumber.replace("+237", "")) & Q(matricule=reason.upper()))
        if qs:
            return True
        return False
    if sentBy == "Staff":
        qs = Staff.objects.filter(phoneNumber=phoneNumber.replace("+237", ""))
        if qs:
            return True
        return False

def formatSMS(msg, start_count):
    global msg_list         # making it global since it has to be eddited in function
    if len(msg) <= start_count: 
        msg_list.append(msg.strip("\n").strip(" ")) # append the message like that if it less than 140 chars
        return           
    if msg[start_count] != " " or msg[start_count] != "\n":  # testing if we are on a newline or a space
        for i in range(start_count+1, len(msg)):    # keep looping until you find a newline or a space char
            if msg[i] == " " or msg[i] == "\n":  
                msg_list.append(msg[0: i].strip("\n").strip(" "))
                return formatSMS(msg[i+1:], 140)
            else:
                pass
    else:
        return formatSMS(msg[start_count+1:], 140)  # if we fell on a space of newline we can continue recursively

#imei = "352097049615198" #orange
#imei = "356342046273666" #mtn
imei = "867567021321977" #gsm module A6

#smsc = "+237679000002" #mtn
smsc = "+237699900929" #orange

smsDestination = "695120166"

expectedSource = smsDestination


# here i expect to receive 
data = {}
orange = Modem(imei)
if orange.isConnectedToPort():
    print("Connected to Port")
    if orange.modemInit():
        while 1:
            print("Waiting For SMS......")
            phoneNumber, receiveDate, incommingSMS = orange.receiveLiveSMS()
            print("Received Message from: ", phoneNumber)
            print("Received Message On: ", receiveDate)
            print("Received Message: ", incommingSMS)
            processedMessage = processMessage(incommingSMS)

            print(processedMessage)

            if processedMessage == None:
                print("Invalid Message")
                print("Message Discarded")
                print("Message cannot be processed")
                continue

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("localhost", 10000))

            data = {
                "message" : "",
                "phoneNumber": ""
            }


            if processedMessage[0] == "request-booking":
                reason = processedMessage[4]
                if reason in ("work", "class"):
                    if not authenticateUser(phoneNumber, reason, "Staff"):
                        print("Invalid Message")
                        print("Message Discarded")
                        print("Staff cannot be authenticated")

                        data["message"] = "Sorry!!! You cannot be authenticated as a STAFF. Don't try again until you are authenticate"
                        data["phoneNumber"] = phoneNumber
                        
                        s.sendall(json.dumps(data).encode("utf-8"))
                        s.close()

                        continue

                else:
                    if not authenticateUser(phoneNumber, reason, "Student"):
                        print("Invalid Message")
                        print("Message Discarded")
                        print("Student cannot be authenticated")

                        data["message"] = "Sorry!!! You cannot be authenticated as a STUDENT. Don't try again until you are authenticate"
                        data["phoneNumber"] = phoneNumber
                        
                        s.sendall(json.dumps(data).encode("utf-8"))
                        s.close()

                        continue

                

                date = datetime.datetime.strptime(processedMessage[1], "%d/%m/%Y")
                hour, minute = processedMessage[2].split(":")
                fromTime = datetime.time(int(hour), int(minute), 0)
                hour, minute = processedMessage[3].split(":")
                toTime = datetime.time(int(hour), int(minute), 0)


                weekDay = calendar.weekday(date.year, date.month, date.day)
            
                qs = WeekDaySchedule.objects.filter(Q(weekDay=weekDay) & Q(fromTime=fromTime) & Q(toTime=toTime))

                if datetime.datetime.now() > date or date.year != datetime.datetime.now().year:
                    print("Invalid Message")
                    print("Message Discarded")
                    print("Date or time of booking is not valid")

                    data["message"] = "Sorry!!! Invalid Booking Date"
                    data["phoneNumber"] = phoneNumber
                        
                    s.sendall(json.dumps(data).encode("utf-8"))
                    s.close()
                    continue

                
                # Checking if the schedule requested by the user is among that given by the laboratory
                if qs:             
                    qs1 = BookedDates.objects.filter(Q(date=date) & Q(period_id=qs[0].id))
                    # Checking if the date has been booked
                    if qs1:
                        # Checking if the the datetime already has max bookings
                        if qs1.count() < qs[0].maxBookings:
                            if reason in ("work", "class"):
                                if reason == "work":
                                    qs1.update(numberOfBookings = qs1[0].numberOfBookings + 1)
                                    data["message"] = "Dear Sir/Madam, Your work from {} to {} on {} in the Lab has been booked successfully\nThanks".format(fromTime, toTime, str(date))
                                if reason == "class":
                                    qs1.update(numberOfBookings = qs[0].maxBookings)
                                    data["message"] = "Dear Sir/Madam, Your class from {} to {} on {} in the has been booked successfully\nThanks"

                                staff = Staff.objects.get(phoneNumber=phoneNumber.replace("+237",""))
                                StaffBookings(
                                    period_id = qs[0].id,
                                    staff = staff,
                                    reason = reason.upper(),
                                ).save()

                                data["phoneNumber"] = phoneNumber
                        
                                s.sendall(json.dumps(data).encode("utf-8"))
                                s.close()
                            else:
                                student = Students.objects.get(matricule=reason.upper())
                                StudentBookings(
                                    period_id = qs[0].id,
                                    student = student
                                ).save()
                                data["message"] = "Dear Sir/Madam, Your work from {} to {} on {} in the Lab has been booked successfully\nThanks".format(fromTime, toTime, str(date))
                                data["phoneNumber"] = phoneNumber
                                s.sendall(json.dumps(data).encode("utf-8"))
                                s.close()

                                qs1.update(numberOfBookings = qs1[0].numberOfBookings + 1)
                            
                        else:
                            data["message"] = "Sorry!!! This period has already reached it maximum number of bookings"
                            data["phoneNumber"] = phoneNumber
                        
                            s.sendall(json.dumps(data).encode("utf-8"))
                            s.close()
                            print("This period has arrived its maximum")
                            # sending message informing of schedule already reached its max
                            pass
                    else:
                        print("This date period has not been booked by anybody yet")
                        # Save if that date has never been booked
                        qs2 = BookedDates(
                            date = date,
                            period_id = qs[0].id,
                            numberOfBookings = 1
                        )

                        if reason in ("work", "class"):
                            if reason == "work":
                                qs2.numberOfBookings = 1
                                data["message"] = "Dear Sir/Madam, Your work from {} to {} on {} in the Lab has been booked successfully\nThanks".format(fromTime, toTime, str(date))
                            if reason == "class":
                                data["message"] = "Dear Sir/Madam, Your work from {} to {} on {} in the Lab has been booked successfully\nThanks".format(fromTime, toTime, str(date))
                                qs2.numberOfBookings = qs[0].maxBookings

                            staff = Staff.objects.get(phoneNumber=phoneNumber)
                            StaffBookings(
                                period_id = qs[0].id,
                                staff = staff,
                                reason = reason.upper()
                            ).save()

                            data["phoneNumber"] = phoneNumber
                            s.sendall(json.dumps(data).encode("utf-8"))
                            s.close()

                        else:
                            student = Students.objects.get(matricule=reason.upper())
                            StudentBookings(
                                period_id = qs[0].id,
                                student = student,
                            ).save()
                            data["message"] = "Dear Sir/Madam, Your work from {} to {} on {} in the Lab has been booked successfully\nThanks".format(fromTime, toTime, str(date))
                            data["phoneNumber"] = phoneNumber
                        qs2.save()

                else:
                    data["message"] = "Sorry!!! Invalid Booking Date"
                    data["phoneNumber"] = phoneNumber
                        
                    s.sendall(json.dumps(data).encode("utf-8"))
                    s.close()
                    print("Schedule Selected is not valid")
                    # send message informing of not valid schedule
                    pass
                            

                print(qs)

            
            if processedMessage[0] == "request-schedule":
                print("Here")
                data["message"] = processedMessage[1]
                data["phoneNumber"] = phoneNumber
                
                s.sendall(json.dumps(data).encode("utf-8"))
                s.close()
                # send the schedule to the number that sent the message
                pass
            

else:
    print("Modem cannot connect to port")



