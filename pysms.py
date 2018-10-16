"""
    ==========================================================================================
    ****Program Description:    This class will implement the ability to send and receive SMS
                                with a modem connected to the computer and to a network.
                                This code will run on linux and windows operating systems
                                This code will run with just python version 3 and above
    ==========================================================================================
    ****Written By:             Mekolle Sone Gillis Ekeh Junior
    ==========================================================================================
    ****Developement Start:     07/06/2018
    ==========================================================================================
    ****Websites That Assisted: http://www.spallared.com/old_nokia/nokia/smspdu/smspdu.htm--1
                                http://mobiletidings.com/2009/02/18/combining-sms-messages/--2
    ==========================================================================================
                                                                                             """


# Array with the default 7 bit alphabet
# @ = 0 = 0b00000000, a = 97 = 0b1100001, etc
# Alignment is purely an attempt at readability
SEVEN_BIT_ALPHABET_ARRAY = (
    '@', '£', '$', '¥', 'è', 'é', 'ù', 'ì', 'ò', 'Ç', '\n', 'Ø', 'ø', '\r','Å', 'å',
    '\u0394', '_', '\u03a6', '\u0393', '\u039b', '\u03a9', '\u03a0','\u03a8', '\u03a3', '\u0398', '\u039e',
    '€', 'Æ', 'æ', 'ß', 'É', ' ', '!', '"', '#', '¤', '%', '&', '\'', '(', ')','*', '+', ',', '-', '.', '/', 
    '0', '1', '2', '3', '4', '5', '6', '7','8', '9', 
    ':', ';', '<', '=', '>', '?', '¡', 
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'Ä',                                                                  'Ö', 
                                                                     'Ñ',                               'Ü', '§', '¿', 
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 
    'ä',                                                                  'ö', 
                                                                     'ñ',                               'ü', 
    'à')

import platform
import glob
import serial
from time import sleep, time
import re

class SerialPorts():
    def __init__(self, ports=None):
        #ports can be passed in for faster search
        self.ports = ports
        #determine python version and ensure its above version 3
        python_version = int(platform.python_version().split('.')[0])
        if python_version < 3:
            raise Exception("Works with python 3 and above")
        
        #determine OS type and test ports for availability 
        os_type = platform.system()
        if os_type == "Windows":        #Windows ports begin with COM
            if self.ports is None:
                self.ports = ["COM"+port_number for num in range(1, 256)]
            else:
                if not isinstance(self.ports, list):
                    raise Exception("Ports must be a list value")
            
        if os_type == "Linux":          #linux ports begin with dev/tty
            if self.ports is None:
                self.ports = glob.glob("/dev/tty[A-Za-z]*")
    
    #This method will return all the list of all available ports
    
    def availablePorts(self):
        """
            Available ports will open without any error
            hence we place in try/except block
        """
        available_ports = []
        s = None
        
        for port in self.ports:
            try: 
                s = serial.Serial(port)
                s.close()                       #close port first if open
                s.open()
                available_ports.append(port)
                s.close()
            except Exception as e:
                #this can be uncommented for debugging purposes
                #print(e)           
                if s:
                    s.close()
                pass
        available_ports.remove('/dev/ttyprintk')        #this port delays when trying to read from it(still to find out why)
        return available_ports

    #This method will return all the list of all available ports with modems
    
    def availablePortsWithModems(self):
        """
            Available ports with modems will respond to an AT command
            with an OK
        """
        available_ports = self.availablePorts()
        available_ports_with_modems = []
        for port in available_ports:
            s = serial.Serial(port)
            s.baudrate = 9600
            s.timeout = 1
            try:
                s.open()
            except:
                pass
            
            #confirm port is actually open before proceeding
            if s.isOpen():
                command = bytes("AT\r\n", encoding="ascii")
                s.write(command)
                count = 0           #try sending command 10 times
                while(count < 10):
                    reply = self.readIncommingBufferData(s)
                    print("*******")
                    print("AT")
                    print(reply)
                    print("*******")
                    s.flushOutput()
                    if "OK" in reply:
                        s.flushInput()
                        count = 0
                        available_ports_with_modems.append(port)
                        break
                    else:
                        s.write(command)
                        count += 1
                s.close()

        if not len(available_ports_with_modems):
            raise Exception("No ports available with modems")

        return available_ports_with_modems

    
    def readIncommingBufferData(self, s):
        reply = ""
        count = 0

        while(1):
            # problem was occuring here
            # still to check
            try:
                incoming_byte = s.read().decode("ascii") # comment to take care of 
            except:
                try:
                    incoming_byte = s.read().decode("ascii")
                except:
                    pass
                pass
            if not len(incoming_byte):
                print("No incoming data")
                break
        
            reply += incoming_byte
            if "OK" in reply:              # this statement is to avoid delay once an 'OK' has been received
                print(s.read(s.in_waiting))
                break                       # it can be removed to see the delay 

        return reply




    
"""
    To use this class, the developer has to verify the particular device object
    with its IMEI number
                        """
class Modem(SerialPorts):
    def __init__(self, imei, ports=None):
        super().__init__()
        self.imei = imei
        self.s = None
        
    #Testing if the device can be found on any of the available ports
    def isConnectedToPort(self):
        try:
            available_ports_with_modems = self.availablePortsWithModems()
        except:
            return False
        found_modem = False     #Flag used to determine if modem is found to avoid more for loop iterations
        print(available_ports_with_modems)
        for port in available_ports_with_modems:
            s = serial.Serial(port)
            s.timeout = 10
            try:
                s.open()
            except: 
                pass
            if s.isOpen():
                #send to command to retrieve imei number of device connected to that port
                command = bytes('AT+CGSN\r\n', encoding='ascii')
                s.write(command)
                count = 0
                
                while(count < 10):
                    reply = self.readIncommingBufferData(s)
                    print("*******")
                    print("IMEI reply")
                    print(reply)
                    print("*******")
                    s.flush()
                    if self.imei in reply:
                        s.flushInput()
                        count = 0
                        found_modem = True
                        self.s = s
                        break
                    else:
                        s.write(command)
                        count += 1

            if found_modem:     #leave the for loop if the modem has already been found
                break
        
        print(found_modem)
        if found_modem:
            self.s.close()
            return True
        else:
            s.close()
            return False
    
    # here we put code to test for modem connectivity with network
    def modemInit(self):
        # Sets the modem to GSM mode since modem just in case it is a 3G or 4G modem
        # If i removed this then the SMS wasn't going "I DON'T KNOW WHY IT HAPPENED LIKE THAT"
        try:
            self.s.open()
        except:
            pass
        command = bytes('AT+CSCS=\"GSM\"\r\n', encoding='ascii')
        self.s.write(command)
        count = 0
        is_gsm_mode_set = False
        while(count < 10):
            reply = self.readIncommingBufferData(self.s)
            print("*******")
            print("GSM MODE reply")
            print(reply)
            print("*******")
            self.s.flushOutput()
            if "OK" in reply:
                self.s.flushInput()
                count = 0
                is_gsm_mode_set = True
                break
            else:
                count += 1
                self.s.write(command)
        if not is_gsm_mode_set:
            # Could not Set modem to gsm mode. Modem could possibly not support
            # Here modem connects to serial port
            return False
        return True
        
    def sendSMS_PDU(self, smsc_center, dest_num, msg):
        print("""
                 Ensure you have initialised the modem before running this method
                 You can initialise the modem by running "object.modemInit()"
                 Your SMS >>might<< not be sent due to this
                                                                                    """)
        # Set the initial variables
        FIRST_OCTET = "1100" # check website - 2 above
        PROTO_ID = "00" # check website - 2 above
        data_encoding = "00" # check website - 2 above
        SMSC_number = smsc_center # The message centre through which the SMS is sent
        SMSC = "" # How the SMSC is represented once encoded
        SMSC_info_length = 0
        SMSC_length = 0
        SMSC_number_format = "81" # by default, assume that it's in national format - e.g. 67...
        destination_phone_number = dest_num # Where the SMS is being sent
        destination_phone_number_format = "81" # by default, assume that it's in national format - e.g. 67...
        message_text = msg # The message to be sent
        encoded_message_binary_string = "" # The message, as encoded into binary
        encoded_message_octet = "" # individual octets of the message

        if SMSC_number[:1] == '+' : # if the SMSC starts with a + then it is an international number
            SMSC_number_format = "91"; # international
            SMSC_number = SMSC_number[1:len(SMSC_number)] # Strip off the +

        # Odd numbers need to be padded with an "F"
        if len(SMSC_number)%2 != 0 : 
            SMSC_number = SMSC_number + "F"

        # Encode the SMSC number
        SMSC = Modem.semi_octet_to_string(SMSC_number)

        # Calculate the SMSC values
        SMSC_info_length = int((len(SMSC_number_format + "" + SMSC))/2)
        SMSC_length = SMSC_info_length

        # Is the number we're sending to in international format?
        if destination_phone_number[:1] == '+' : # if it starts with a + then it is an international number
            destination_phone_number_format = "91"; # international
            destination_phone_number = destination_phone_number[1:len(destination_phone_number)] # Strip off the +

        # Calculate the destination values in hex (so remove 0x, make upper case, pad with zeros if needed)
        destination_phone_number_length = hex(len(destination_phone_number))[2:3].upper().zfill(2)

        if len(destination_phone_number)%2 != 0 : # Odd numbers need to be padded
            destination_phone_number = destination_phone_number + "F"


        destination = Modem.semi_octet_to_string(destination_phone_number)

        # Size of the message to be delivered in hex (so remove 0x, make upper case, pad with zeros if needed)
        message_data_size = str(hex(len(message_text)))[2:len(message_text)].upper().zfill(2)

        # Go through the message text, encoding each character
        for i in range(0,len(message_text)) : 
            character = message_text[i:i+1] # get the current character
            current = bin(Modem.convert_character_to_seven_bit(character)) # translate into the 7bit alphabet
            character_string = str(current) # Make a string of the binary number. eg "0b1110100
            character_binary_string = character_string[2:len(str(character_string))] # Strip off the 0b
            character_padded_7_bit =  character_binary_string.zfill(7) # all text must contain 7 bits
            # Concatenate the bits
            # Note, they are added to the START of the string
            encoded_message_binary_string = character_padded_7_bit + encoded_message_binary_string 

        # Reverse the string to make it easier to count
        encoded_message_binary_string_reversed = encoded_message_binary_string[::-1]

        # Get each octet into hex
        for i in range(0,len(encoded_message_binary_string_reversed),8) : # from 0 - length, incrementing by 8
            # Get the 8 bits, reverse them back to normal, if less than 8, pad them with 0
            encoded_octet = encoded_message_binary_string_reversed[i:i+8][::-1].zfill(8)
            encoded_octet_hex = hex(int(encoded_octet,2)) # Convert to hex
            
            # Strip the 0x at the start, make uppercase, pad with a leading 0 if needed
            encoded_octet_hex_string = str(encoded_octet_hex)[2:len(encoded_octet_hex)].upper().zfill(2)
            
            # Concatenate the octet to the message
            encoded_message_octet = encoded_message_octet + encoded_octet_hex_string

        # Generate the PDU --> Check website - 2 above
        PDU = str(SMSC_info_length).zfill(2) \
                + str(SMSC_number_format) \
                + SMSC \
                + FIRST_OCTET \
                + str(destination_phone_number_length) \
                + destination_phone_number_format \
                + destination \
                + PROTO_ID \
                + "00AA" \
                + str(message_data_size) \
                + encoded_message_octet
        
        #setting the modem to PDU mode
        command = bytes("AT+CMGF=0\r\n", "ascii")
        self.s.write(command)
        count = 0
        is_pdu_mode_set = False
        while(count < 10):
            reply = self.readIncommingBufferData(self.s)
            print("******")
            print("SMSC reply")
            print(reply)
            print("*****")
            if "OK" in reply:
                self.s.flushInput()
                count = 0
                is_pdu_mode_set = True
                break
            else:
                count += 1
                self.s.write(command)
        if not is_pdu_mode_set:
            self.s.close()
            raise Exception("Could not Set modem to PDU mode. Modem could possibly not support or no SIM is available")

        command = bytes("AT+CMGS=" + str(int((len(PDU)/2) - SMSC_length - 1)) + "\r", "ascii")
        self.s.write(command)
        sleep(0.2)
        self.s.write(bytes(PDU, "ascii")) # Send the PDU
        sleep(0.2)
        self.s.write(bytes("\x1A\r\n", "ascii")) # Submit the PDU

        print(PDU)
        return True
    
    def sendSMS(self, smsc_center, dest_num, msg):
        print("""
                 Ensure you have initialised the modem before running this method
                 You can initialise the modem by running "object.modemInit()"
                 Your SMS >>might<< not be sent due to this
                                                                                    """)
        try:
            self.s.open()
        except:
            pass
        #setting the modem to text Mode
        command = bytes('AT+CMGF=1\r\n', encoding='ascii')
        dest_num = "+237"+dest_num
        self.s.write(command)
        count = 0
        is_text_mode_set = False
        while(count < 10):
            reply = self.readIncommingBufferData(self.s)
            print("******")
            print("SMSC reply")
            print(reply)
            print("*****")
            if "OK" in reply:
                self.s.flushInput()
                count = 0
                is_text_mode_set = True
                break
            else:
                count += 1
                self.s.write(command)
        if not is_text_mode_set:
            self.s.close()
            raise Exception("Could not Set modem to text mode. Modem could possibly not support or no SIM is available")

        #sends the message to the destination
        dest_num_format = "AT+CMGS=\"%s\"\r\n" %dest_num
        dest_num_format = bytes(dest_num_format, encoding="ascii")
        self.s.write(dest_num_format)
        sleep(0.2)

        msg = bytes(msg, encoding='ascii')
        self.s.write(msg)
        sleep(0.2)
        end_msg = bytes("\x1A\r\n", encoding='ascii')  #encoded equivalent of 26 representing the end of the message
        self.s.write(end_msg)
        reply = self.readIncommingBufferData(self.s)
        print("*******")
        print("MSG reply")
        print(reply)
        print("*******")
        is_msg_sent = False

        if "OK" in reply:
            is_msg_sent = True

        self.s.close()

        return is_msg_sent

    @staticmethod
    def semi_octet_to_string(input) :
        """ Takes an octet and returns a string
            e.g if input="2376"
                then output = "3267"
        """
        output = ""
        i=0
        for i in range(0,len(input),2) : # from 0 - length, incrementing by 2
            output = output + str(input)[i+1:i+2] + str(input)[i:i+1]
        return output

    @staticmethod
    def convert_character_to_seven_bit(character) :
        """ Takes a single character.
        Looks it up in the SEVEN_BIT_ALPHABET_ARRAY.
        Returns the position in the array.
        """
        for i in range(0,len(SEVEN_BIT_ALPHABET_ARRAY)) :
            if SEVEN_BIT_ALPHABET_ARRAY[i] == character:
                return i
        return 36 # If the character cannot be found, return a ¤ to indicate the missing character

    def setToTextMode(self):
        command = bytes('AT+CMGF=1\r\n', encoding='ascii')
        self.s.write(command)
        reply = self.readIncommingBufferData(self.s)
        if 'OK' in reply:
            print("Successfully set to text mode")

    
    @staticmethod
    def extractSMS(msg):
        msg = msg.split("\r\n")
        print(msg, "testing 1")
        if len(msg) < 2:
            return None
        print(msg, "testing 2")
        msgProp = msg[0]    # this will contain the properties of the message
        msgInfo = msg[1]    # this will contain the actual message
        print(msg, "testing 3")
        matchobj = re.match(r"\+CMT: \"(?P<phoneNumber>.+)\",,\"(?P<receiveDate>.+)\"", msgProp)
        print(msg, "testing 4")
        return matchobj.group(1), matchobj.group(2), msgInfo
        
    """
        This method is a blocking method
        It will wait until it receives an SMS
    """
    def receiveLiveSMS(self):
        print("""
                 Ensure you have initialised the modem before running this methodd
                 You can initialise the modem by running "object.modemInit()"
                 Your SMS >>might<< not be sent due to this
                                                                                    """)
        try:
            self.s.open()
        except:
            pass

        self.setToTextMode()

        #setting the modem to recieve live SMS
        command = bytes('AT+CNMI=2,2,0,0,0\r\n', encoding='ascii')

        self.s.write(command)
        reply = self.readIncommingBufferData(self.s)
        
        if 'OK' in reply:
            print("Successfully set to receive sms mode")

        sleep(0.5)

        receivedSMS = ""

        while(1):
            while self.s.in_waiting:
                try:
                    receivedSMS += self.s.read(self.s.in_waiting).decode("ascii")
                    sleep(0.5)
                    print(receivedSMS)
                except:
                    print("Exception occurred")
                    pass

            sleep(0.5)
            
            # +CMT will be part of the reply if it really an SMS sent
            cmtIndex = receivedSMS.find("+CMT")

            if cmtIndex != -1:
                extractedSMS = Modem.extractSMS(receivedSMS[cmtIndex:])
                if extractedSMS:
                    return extractedSMS
                else:
                    print("Message not received properly")
                    receivedSMS = ""
        

    

        

            









            

            
