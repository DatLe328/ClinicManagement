import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(recipient, subject, body):
    email = 'youremail@gmail.com'
    password = 'yourpassword'

    try:
        message = MIMEMultipart()
        message['From'] = email
        message['To'] = recipient
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        # Kết nối SMTP
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(email, password)
        session.sendmail(email, recipient, message.as_string())
        session.quit()
        print(f"Mail sent to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")