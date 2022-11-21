import qrcode
import datetime
import math
import ctypes
import random

def first_n_digits(num, n):
    return num // 10 ** (int(math.log(num, 10)) - n + 1)


def qr_generator():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=4,
    )
    acutal_time = datetime.datetime.now()
    acutal_minute = acutal_time.minute
    acutal_second = acutal_time.second
    acutal_micro = acutal_time.microsecond
    try:
        print("generate port")
        second_digit = str(acutal_minute % 10)
        third_digit =  int(str(acutal_second)[:1])
        fourth_digit = int(str(acutal_micro)[:1])

    except:
        second_digit = 0
        third_digit = 5
        fourth_digit = 0

    port_number = str(5) + str(second_digit) + str(third_digit) + str(fourth_digit)

    name_for_hash = 'photo'+ str(random.randint(0, 10))
    # if hash is wanted uncommetn the next three lines
    #hash_num = '/' + str(ctypes.c_size_t(hash(name_for_hash)).value)#positive hash
    #print("hash_num: ", hash_num)
    qr_text = "http://" + "10.42.0.1:" + str(port_number)# + hash_num

    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img, port_number#, hash_num
