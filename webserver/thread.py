import qrcode
import datetime
import math

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

    if(len(str(acutal_second))<2):
        second_digit = str(first_n_digits(acutal_micro, 1))
        third_digit = str(acutal_minute % 10)
        fourth_digit = str(first_n_digits(acutal_second, 1))
    else:
        second_digit = str(acutal_minute % 10)
        third_digit = str(first_n_digits(acutal_second, 1))
        fourth_digit = str(acutal_second % 10)
    port_number = str(5) + second_digit + third_digit + fourth_digit
    qr_text = "http://" + "192.168.178.41:" + str(port_number)

    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img, port_number
