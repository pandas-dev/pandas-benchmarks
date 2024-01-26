
import smtplib, ssl
import os
from dotenv import load_dotenv
import socket

if socket.gethostname().startswith('Deas'):
      load_dotenv(dotenv_path="./local_env.yml")
else:
      load_dotenv(dotenv_path="./server_env.yml")

def email(message):
    
    port = 465  # For SSL
    sender_email = "conbenchalert@gmail.com"
    receiver_email = ["deamarialeon@gmail.com"]
    gmail_password=os.getenv("GMAIL_PASSWORD")
    
    # Create a secure SSL context
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login("conbenchalert@gmail.com", gmail_password)
        print(message)
        server.sendmail(sender_email, receiver_email, message)
    
if __name__=="__main__":
    message = """\
        Subject: Hello

        Message sent from conbenchalert."""
    email(message)