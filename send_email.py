import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from passwords import get_email_address

to_email = get_email_address()  # Не хочу светить email адреса
from_email = 'from_python@modis.ru'
SMTP_SERVER = 'smtp.modis.ru'


def send_email(subject, text, result):
    msg = MIMEMultipart('alternative')

    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ', '.join(to_email)
    html = f"""\
    <html>
        <head></head>
        <body>
        <pre>
{result}<br>
{text}
        </pre>    
        </body>
    </html>
    """

    part2 = MIMEText(html, 'html')
    msg.attach(part2)
    s = smtplib.SMTP(SMTP_SERVER)
    s.sendmail(from_email,to_email,msg.as_string())

    s.close()
    #s.quit()

