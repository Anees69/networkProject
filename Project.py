from socket import *
import os
import hashlib
import secrets
from urllib.parse import unquote, parse_qs


serverPort = 8099 
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(50)
print('Web Server is ready ...')
sessions = {}

def sendResponse(status, type, extra_headers=None):
    """Send HTTP response headers"""
    if int(status) == 200:
        connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
    elif int(status) == 404:
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
    elif int(status) == 307:
        connectionSocket.send("HTTP/1.1 307 Temporary Redirect\r\n".encode())
    header_line = "Content-Type: " + type + "; charset=utf-8\r\n"
    connectionSocket.send(header_line.encode())
    if extra_headers:
        for header in extra_headers:
            connectionSocket.send((header + "\r\n").encode())
    connectionSocket.send("\r\n".encode())

def Error(ip, port):
    """Send custom 404 error page"""
    sendResponse(404, 'text/html')
    try:
        with open('./html/error404.html', 'r', encoding='utf-8') as f:
            error_page = f.read()
            error_page = error_page.replace('{{IP}}', ip)
            error_page = error_page.replace('{{PORT}}', str(port))
        connectionSocket.send(error_page.encode())
    except:
        # fallback in case file is missing
        
       # ====== Fallback: HTML from code ======
        fallback_page = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error 404</title>
    <style>
        body {{
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background-color: #fafafa;
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        .error-box {{
            border: 2px solid #cc0000;
            padding: 30px;
            border-radius: 10px;
            background-color: #fff0f0;
            max-width: 800px;
            width: 80%;
        }}
        .error-title {{
            font-size: 32px;
            color: #cc0000;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .error-text {{
            color: red;
            font-size: 22px;
            margin-bottom: 25px;
        }}
        .client-info {{
            color: #333;
            font-size: 16px;
            margin: 15px 0;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
            border-left: 4px solid #666;
        }}
        .team-members {{
            color: red;
            font-size: 18px;
            margin: 25px 0;
            line-height: 1.6;
            padding: 15px;
            background-color: #ffeaea;
            border-radius: 8px;
            border-left: 4px solid #cc0000;
        }}
    </style>
</head>

<body>
    <div class="error-box">
        <div class="error-title">Error 404</div>
        <div class="error-text">The file is not found</div>

        <div class="client-info">
            Client IP: {ip}<br>
            Client Port: {port}
        </div>

        <div class="team-members">
            Anis DarHammouda 1230834<br>
            Nancy Samhan 1230926<br>
            Lina Hamad 1231412
        </div>

        <a href="/"
           style="display:inline-block; padding:12px 30px; margin-top:20px;
                  border-radius:8px; text-decoration:none; font-weight:600;
                  background:linear-gradient(135deg,#2c3e50 0%,#4a235a 100%);
                  color:white;">
            Go to Home Page
        </a>
    </div>
</body>
</html>"""

        connectionSocket.send(fallback_page.encode('utf-8'))



def sendErrorPage(title, message, try_again_url=None):
    """Send styled error page from external HTML file"""
    sendResponse(200, 'text/html')
    try:
        with open('./html/custom_error.html', 'r', encoding='utf-8') as f:
            page = f.read()

        if try_again_url:
            buttons_html = f'''
                <a href="{try_again_url}" class="btn btn-primary">Try Again</a>
                <a href="/" class="btn btn-secondary">Go to Home Page</a>
            '''
        else:
            buttons_html = '''
                <a href="/" class="btn btn-primary">Go to Home Page</a>
            '''
        # Replace placeholders
        page = page.replace('{{TITLE}}', title)
        page = page.replace('{{MESSAGE}}', message)
        page = page.replace('{{BUTTONS}}', buttons_html)

        connectionSocket.send(page.encode())

    except Exception as e:
        # fallback if file missing
        connectionSocket.send(
            b"<html><body><h1>Error</h1><p>Something went wrong</p></body></html>"
        )
    
def getCookie(request_headers):
    """Extract session_id from Cookie header"""
    for line in request_headers.split('\n'):
        if line.lower().startswith('cookie:'):
            cookies = line.split(':', 1)[1].strip()
            for cookie in cookies.split(';'):
                cookie = cookie.strip()
                if cookie.startswith('session_id='):
                    return cookie.split('=', 1)[1]
    return None

def isAuthenticated(request_headers):
    """Check if user is authenticated via session cookie"""
    session_id = getCookie(request_headers)
    if session_id and session_id in sessions:
        return True, sessions[session_id]
    return False, None

def usernameExists(username):
    """Check if username already exists in data.txt"""
    if os.path.exists('data.txt'):
        with open('data.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    stored_user = line.split(':', 1)[0]
                    if stored_user == username:
                        return True
    return False


while True:
    files = os.listdir('.')
    files = [f for f in files if os.path.isfile(f)]

    html = []
    if os.path.exists('./html'):
        html = os.listdir('./html')
        html = [f for f in html if os.path.isfile(os.path.join('./html', f))]

    css = []
    if os.path.exists('./css'):
        css = os.listdir('./css')
        css = [f for f in css if os.path.isfile(os.path.join('./css', f))]

    images = []
    if os.path.exists('./images'):
        images = os.listdir('./images')
        images = [f for f in images if os.path.isfile(os.path.join('./images', f))]

    connectionSocket, addr = serverSocket.accept()
    ip = addr[0]
    port = addr[1]
    print('Got connection from', "IP: " + ip + ", Port: " + str(port))
    # receive http request
    sentence = connectionSocket.recv(4096).decode()
    # print full HTTP request on cmd
    print(sentence)
    # split the request to get the request line from user input
    try:
        lines = sentence.split('\n')
        match = lines[0]
        parts = match.split(' ')
        method = parts[0]  # GET or POST
        request = unquote(parts[1])  # URL decode
        print(f"Method: {method}, Request: {request}")
    except Exception as e:
        print("BAD REQUEST", e)
        connectionSocket.close()
        continue

    # Forrrrr task 7
    if request == "/chat":
        sendResponse(307, 'text/html', ["Location: https://chatgpt.com/"])
        connectionSocket.send(b"<html><body><h1>Redirecting to ChatGPT...</h1></body></html>")

    elif request == "/cf":
        sendResponse(307, 'text/html', ["Location: https://www.cloudflare.com/"])
        connectionSocket.send(b"<html><body><h1>Redirecting to Cloudflare...</h1></body></html>")

    elif request == "/rt":
        sendResponse(307, 'text/html', ["Location: https://ritaj.birzeit.edu/"])
        connectionSocket.send(b"<html><body><h1>Redirecting to Ritaj...</h1></body></html>")
    # Forrr Task 9
    elif request == "/register.html":
        if 'register.html' in html:
            with open('./html/register.html', 'r', encoding='utf-8') as reg:
                reg_data = reg.read()
            sendResponse(200, 'text/html')
            connectionSocket.send(reg_data.encode())
        else:
            Error(ip, port)

    #Handling registration POST for Task 9
    elif request == "/register" and method == "POST":
        try:
            # Extract POST data
            body = sentence.split('\r\n\r\n')[1]
            params = parse_qs(body)

            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]

            if username and password:

                # Check if username already exists
                if usernameExists(username):
                    sendErrorPage(
                        "Registration Failed",
                        f"Username '<strong>{username}</strong>' already exists. Please try a different username.",
                        "/register.html"
                    )

                else:
                    # Hash the password using SHA256
                    hashed = hashlib.sha256(password.encode()).hexdigest()

                    # Save to data.txt
                    with open('data.txt', 'a') as f:
                        f.write(f"{username}:{hashed}\n")

                    # Load register success page
                    try:
                        with open('./html/register_success.html', 'r', encoding='utf-8') as f:
                            page = f.read()
                        page = page.replace('{{USERNAME}}', username)
                    except FileNotFoundError:
                        # If HTML file is missing, send 404 error
                        Error(ip, port)
                        connectionSocket.close()
                        continue

                    # Send response
                    sendResponse(200, 'text/html')
                    connectionSocket.send(page.encode())

            else:
                sendErrorPage(
                    "Registration Error",
                    "Missing username or password. Please fill in all fields.",
                    "/register.html"
                )

        except Exception as e:
            print("Registration error:", e)
            Error(ip, port)

    # For task 10
    elif request == "/login.html":
        if 'login.html' in html:
            with open('./html/login.html', 'r', encoding='utf-8') as login:
                login_data = login.read()
            sendResponse(200, 'text/html')
            connectionSocket.send(login_data.encode())
        else:
            Error(ip, port)

    # Handling Login POST for Task 10
    elif request == "/login" and method == "POST":
        try:
            # Extract POST data
            body = sentence.split('\r\n\r\n')[1]
            params = parse_qs(body)

            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]

            # Hash the entered password
            hashed = hashlib.sha256(password.encode()).hexdigest()

            # Check credentials from data.txt
            valid = False
            if os.path.exists('data.txt'):
                with open('data.txt', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            stored_user, stored_hash = line.split(':', 1)
                            if stored_user == username and stored_hash == hashed:
                                valid = True
                                break

            if valid:
                # Generate unique session ID
                session_id = secrets.token_hex(16)

                # Store session in memory
                sessions[session_id] = username

                # Load login success page
                try:
                    with open('./html/login_success.html', 'r', encoding='utf-8') as f:
                        page = f.read()
                    page = page.replace('{{USERNAME}}', username)
                except FileNotFoundError:
                    # If HTML file is missing, send 404 error
                    Error(ip, port)
                    connectionSocket.close()
                    continue  # Skip the rest

                # Send response headers with session cookie
                connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
                connectionSocket.send("Content-Type: text/html; charset=utf-8\r\n".encode())
                connectionSocket.send(f"Set-Cookie: session_id={session_id}; Path=/\r\n".encode())
                connectionSocket.send("\r\n".encode())  # Empty line separating headers and body
                
                connectionSocket.send(page.encode())

            else:
                if usernameExists(username):
                    sendErrorPage(
                        "Login Failed",
                        f"Incorrect password for user '<strong>{username}</strong>'. Please try again.",
                        "/login.html"
                    )
                else:
                    sendErrorPage(
                        "Login Failed",
                        f"Username '<strong>{username}</strong>' not found. Please check your username or register.",
                        "/login.html"
                    )

        except Exception as e:
            print("Login error:", e)
            Error(ip, port)

        #Protected Page for task 10
    elif request == "/protected.html":
            authenticated, username = isAuthenticated(sentence)
            if authenticated:
                if 'protected.html' in html:
                    with open('./html/protected.html', 'r', encoding='utf-8') as prot:
                        prot_data = prot.read()
                    sendResponse(200, 'text/html')
                    connectionSocket.send(prot_data.encode())
                else:
                    sendResponse(200, 'text/html')
                    protected_page = (
                        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
                        '<title>Protected Page</title></head>'
                        '<body style="text-align:center;padding:50px;">'
                        '<h1 style="color:green;">Welcome, ' + username + '!</h1>'
                        '<p>This is a protected page.</p>'
                        '<a href="/">Go to Home</a> | '
                        '<a href="/logout">Logout</a>'
                        '</body></html>'
                    )
                    connectionSocket.send(protected_page.encode())
            else:
                sendErrorPage("Access Denied", 
                            "Please <a href='/login.html' style='color:#2c3e50;'>login</a> first to access this page.",
                            "/login.html")  # Try again goes to login page

    # Logout for task 10
    elif request == "/logout":
        session_id = getCookie(sentence)
        if session_id and session_id in sessions:
            del sessions[session_id]  # Remove session
        # go to home page after logout
        sendResponse(307, 'text/html', ["Location: /", "Set-Cookie: session_id=; Path=/; Max-Age=0"])
        connectionSocket.send(b"<html><body><h1>Logging out...</h1></body></html>")

    # English Version for tttask 1
    elif request == "/" or request == "/index.html" or request == "/main_en.html" or request == "/en" or request == "/html/main_en":
        # Check if user is authenticated
        authenticated, username = isAuthenticated(sentence)
        
        if 'main_en.html' in html:
            with open('./html/main_en.html', 'r', encoding='utf-8') as mainEn:
                mainEn_data = mainEn.read()            
            if authenticated:
                welcome_banner = f'''
            <style>
                body {{
                    padding-top: 70px !important;
                }}
            </style>
            <div style="position: fixed; top: 0; left: 0; right: 0; background: linear-gradient(135deg, #2c3e50 0%, #4a235a 100%); color: white; padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 9999; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 18px; font-weight: 500;">
                    Welcome <strong>{username}</strong> to our tiny webserver
                </div>
                <a href="/logout" style="background: white; color: #2c3e50; padding: 8px 20px; border-radius: 5px; text-decoration: none; font-weight: 600; transition: all 0.3s;">Logout</a>
            </div>
            '''
                if '<body>' in mainEn_data:
                    mainEn_data = mainEn_data.replace('<body>', '<body>' + welcome_banner, 1)
                elif '</head>' in mainEn_data:
                    mainEn_data = mainEn_data.replace('</head>', welcome_banner + '</head>', 1)
            
            sendResponse(200, 'text/html')
            connectionSocket.send(mainEn_data.encode())
        else:
            Error(ip, port)

    # Arabic Version for task 2
    elif request == "/ar" or request == "/main_ar.html" or request == "/html/main_ar":
        # Check if user is authenticated
        authenticated, username = isAuthenticated(sentence)
        
        if 'main_ar.html' in html:
            with open('./html/main_ar.html', 'r', encoding='utf-8') as mainAr:
                mainAr_data = mainAr.read()
            
            if authenticated:
                welcome_banner = f'''
            <style>
                body {{
                    padding-top: 70px !important;
                }}
            </style>
            <div style="position: fixed; top: 0; left: 0; right: 0; background: linear-gradient(135deg, #2c3e50 0%, #4a235a 100%); color: white; padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 9999; display: flex; justify-content: space-between; align-items: center; direction: rtl;">
                <div style="font-size: 18px; font-weight: 500;">
                    مرحباً <strong>{username}</strong> في مساق شبكات الحاسوب، هذا خادم ويب صغير
                </div>
                <a href="/logout" style="background: white; color: #2c3e50; padding: 8px 20px; border-radius: 5px; text-decoration: none; font-weight: 600; transition: all 0.3s;">تسجيل الخروج</a>
            </div>
            '''
                if '<body>' in mainAr_data:
                    mainAr_data = mainAr_data.replace('<body>', '<body>' + welcome_banner, 1)
                elif '</head>' in mainAr_data:
                    mainAr_data = mainAr_data.replace('</head>', welcome_banner + '</head>', 1)
            
            sendResponse(200, 'text/html')
            connectionSocket.send(mainAr_data.encode())
        else:
            Error(ip, port)

    # for the css file task 4
    elif request == "/main.css" or (request.startswith('/') and request.endswith('.css')):
        css_name = request.split('/')[-1]
        if css_name in css:
            with open('./css/' + css_name, 'r', encoding='utf-8') as cssFile:
                css_data = cssFile.read()
            sendResponse(200, 'text/css')
            connectionSocket.send(css_data.encode())
        else:
            Error(ip, port)

    # for images requests tasks 5 & 6
    elif '/images/' in request:
        ob = request.split('/images/')[1]
        obj = './images/' + ob
        if ob in images:
            ext = obj.split('.')[-1].lower()
            if ext in ('jpg', 'jpeg'):
                content_type = 'image/jpeg'
            elif ext == 'png':
                content_type = 'image/png'
            elif ext == 'gif':
                content_type = 'image/gif'
            else:
                content_type = 'application/octet-stream'
            with open(obj, 'rb') as image:
                image_data = image.read()
                sendResponse(200, content_type)
                connectionSocket.send(image_data)
        else:
            Error(ip, port)

    # Other requests: html/css/png/jpg from available files for tasks 3-6
    else:
        try:
            obj = request.split('/')[1] if request.startswith('/') else request
            if (obj in files or obj in html or obj in css or obj in images):
                ext = obj.split('.')[-1].lower()

                if obj in html:
                    obj_path = './html/' + obj
                elif obj in css:
                    obj_path = './css/' + obj
                elif obj in images:
                    obj_path = './images/' + obj
                else:
                    obj_path = obj

                if ext == 'html':
                    sendResponse(200, 'text/html')
                    with open(obj_path, 'r', encoding='utf-8') as file:
                        data = file.read()
                    connectionSocket.send(data.encode())
                elif ext == 'css':
                    sendResponse(200, 'text/css')
                    with open(obj_path, 'r', encoding='utf-8') as file:
                        data = file.read()
                    connectionSocket.send(data.encode())
                elif ext in ('jpg', 'jpeg'):
                    sendResponse(200, 'image/jpeg')
                    with open(obj_path, 'rb') as file:
                        data = file.read()
                    connectionSocket.send(data)
                elif ext == 'png':
                    sendResponse(200, 'image/png')
                    with open(obj_path, 'rb') as file:
                        data = file.read()
                    connectionSocket.send(data)
                elif ext == 'gif':
                    sendResponse(200, 'image/gif')
                    with open(obj_path, 'rb') as file:
                        data = file.read()
                    connectionSocket.send(data)
                else:
                    # default: send as binary
                    sendResponse(200, 'application/octet-stream')
                    with open(obj_path, 'rb') as file:
                        data = file.read()
                    connectionSocket.send(data)
            else:
                Error(ip, port)
        except (IndexError, FileNotFoundError):
            print('File not found or bad request')
            Error(ip, port)

    connectionSocket.close()