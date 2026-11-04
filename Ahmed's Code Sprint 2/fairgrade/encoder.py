import base64

def encode64(text):
    return base64.b64encode(text.encode()).decode()

def decode64(text):
    return base64.b64decode(text.encode()).decode()
