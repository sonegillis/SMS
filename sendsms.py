import socket
import json
from threading import Thread
from queue import Queue
from .pysms import Modem

q = Queue(maxsize=0)

mtn_key_imei = "356342046273666"

orange_key_imei = "352097049615198"

msg_list = []

mtn_smsc = "+237679000002" #mtn
orange_smsc = "+237699900929" #orange


# this method will determine if the phone number is an 
# for example either MTN or ORANGE
# It'll return 0 for MTN, 1 for ORANGE
# It can be modified when another network is needed
def numberTypePredict(tel):
    # will use these codes to differentiate between MTN numbers and 
    # ORANGE numbers so as the send the sms with the right modem
    orange_prefix_codes = [69,656,655,657]
    mtn_prefix_codes = [67,650,651,652,653,654]

    if int(tel[0:2]) in mtn_prefix_codes or int(tel[0:3]) in mtn_prefix_codes:
        return 0

    if int(tel[0:2]) in orange_prefix_codes or int(tel[0:3]) in orange_prefix_codes:
        return 1
    
    else:
        return None
    
# this method will determine if the message is longer than 150 characters
# the function will split the message ensuring that longer messages can
# be sent in a more organised format
# it can be better by using multipart SMS which is beyond the scope of 
# this function 

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

def sendMessage(q):
    global msg_list
    while(1):
        if not q.empty():
            print("Got data")
            data = q.get()
            message = data["message"]
            phoneNumber = data["phoneNumber"]
            number_type = numberTypePredict(phoneNumber.replace("+237",""))
            print(number_type)
            formatSMS(message, 140)

            if number_type == 0:        # mtn number found; use MTN modem
                mtn = Modem(mtn_key_imei)
                if mtn.isConnectedToPort():
                    print("Connected to Port")
                    if mtn.modemInit():
                        for msg in msg_list:
                            print("#################")
                            print(msg)
                            print("##################")
                            mtn.sendSMS_PDU(mtn_smsc, phoneNumber, msg)
                            msg_list = []
                            
                    else:
                        pass # return HttpResponse("MTN modem has to be changed", status=404)  # has to be changed because we need modem
                                                                                        # supporting GSM mode
                else:
                    print("Not connected to port")
                    pass # return HttpResponse("MTN modem not detected", status=404)           # the modem is possibly not connected
            if number_type == 1:                                                        # orange number found; use Orange modem
                orange = Modem(orange_key_imei)
                if orange.isConnectedToPort():
                    if orange.modemInit():
                        print(msg_list)
                        for msg in msg_list:
                            print("#################")
                            print(msg)
                            print("##################")
                            orange.sendSMS_PDU(orange_smsc, phoneNumber, msg)
                            msg_list = []
                    else:
                        print("Orange modem has to be change")
                        pass # return HttpResponse("Orange modem has to be changed", status=404) # same reason as above
                else:
                    print("Orange modem not detected")
                    pass # return HttpResponse("Orange modem not detected", status=404)    # same reason as above


def receiveMessage(conn, q):
    data = conn.recv(2048).decode("utf-8")
    data = json.loads(data)
    q.put(data)
    conn.close()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(("127.0.0.1", 10000))

s.listen(5)

t1 = Thread(target=sendMessage, args=(q,))
t1.start()

while(1):
    conn, addr = s.accept()
    t2 = Thread(target=receiveMessage, args=(conn, q))
    t2.start()


