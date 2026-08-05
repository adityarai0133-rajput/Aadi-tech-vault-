import os, hashlib, sys, webbrowser, threading
from flask import Flask, render_template, request, redirect, session, send_from_directory
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Kivy Framework Imports for EXE & APK
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

def resource_path(relative_path):
    try: 
        base_path = sys._MEIPASS
    except Exception: 
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=resource_path('templates'))
app.secret_key = os.urandom(32)

# Mobile vs Desktop Storage Path Resolver
if 'ANDROID_ARGUMENT' in os.environ:
    # Android External Public Storage Path
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
    from android.storage import primary_external_storage_path
    VAULT_DIR = os.path.join(primary_external_storage_path(), "Aadi_Vault")
else:
    # Desktop Standard Path
    VAULT_DIR = "Aadi_Vault"

PWD_FILE = os.path.join(VAULT_DIR, "shadow.txt")
KEY_FILE = os.path.join(VAULT_DIR, "master.key")

if not os.path.exists(VAULT_DIR): 
    os.makedirs(VAULT_DIR, exist_ok=True)

def get_aes_key():
    if not os.path.exists(KEY_FILE):
        key = os.urandom(32)
        with open(KEY_FILE, "wb") as f: 
            f.write(key)
        return key
    with open(KEY_FILE, "rb") as f: 
        return f.read()

def clean_vault():
    """Temporary UNLOCKED files ko delete karne ke liye taaki speed bani rahe"""
    if os.path.exists(VAULT_DIR):
        for f in os.listdir(VAULT_DIR):
            if f.startswith("UNLOCKED_"):
                try: 
                    os.remove(os.path.join(VAULT_DIR, f))
                except: 
                    pass

@app.route('/')
def index():
    if not os.path.exists(PWD_FILE): 
        return render_template('index.html', mode="setup")
    if 'auth' not in session: 
        return render_template('index.html', mode="login")
    
    clean_vault()
    files = [f for f in os.listdir(VAULT_DIR) if f.endswith('.aadi')]
    return render_template('index.html', mode="dashboard", files=files)

@app.route('/gatekeeper', methods=['POST'])
def gatekeeper():
    user_input = request.form.get('master_key_field')
    if not user_input: 
        return redirect('/')
    
    hashed = hashlib.sha256(user_input.encode()).hexdigest()
    
    if not os.path.exists(PWD_FILE):
        with open(PWD_FILE, "w") as f: 
            f.write(hashed)
        return redirect('/')
    
    with open(PWD_FILE, "r") as f:
        if f.read().strip() == hashed:
            session['auth'] = True
            session.permanent = True
            return redirect('/')
            
    return render_template('index.html', mode="login", error="INVALID KEY!")

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    if 'auth' not in session: 
        return redirect('/')
    file = request.files.get('file')
    if file:
        name = file.filename.replace("UNLOCKED_", "").replace(".aadi", "")
        key = get_aes_key()
        cipher = AES.new(key, AES.MODE_CBC)
        data = file.read()
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        
        with open(os.path.join(VAULT_DIR, name + ".aadi"), "wb") as f:
            f.write(cipher.iv + ct_bytes)
    return redirect('/')

@app.route('/decrypt/<filename>')
def decrypt_file(filename):
    if 'auth' not in session: 
        return redirect('/')
    file_path = os.path.join(VAULT_DIR, filename)
    if not os.path.exists(file_path): 
        return redirect('/')

    key = get_aes_key()
    with open(file_path, "rb") as f:
        iv, data = f.read(16), f.read()
    
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        pt = unpad(cipher.decrypt(data), AES.block_size)
        
        temp_name = "UNLOCKED_" + filename.replace(".aadi", "")
        temp_path = os.path.join(VAULT_DIR, temp_name)
        
        with open(temp_path, "wb") as f: 
            f.write(pt)
        return send_from_directory(VAULT_DIR, temp_name, as_attachment=True)
    except:
        return "Error in Decryption!"

@app.route('/logout')
def logout():
    clean_vault()
    session.clear()
    return redirect('/')

def start_flask_server():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

# Kivy Application UI Container
class AadiTechVaultApp(App):
    def build(self):
        self.title = "Aadi Tech Vault"
        
        # Start Flask Backend Engine in Background Thread
        threading.Thread(target=start_flask_server, daemon=True).start()

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        status_label = Label(
            text="[b]Aadi Tech Vault Core Engine Active[/b]\n\nServer running locally at:\nhttp://127.0.0.1:5000",
            markup=True,
            halign="center"
        )
        
        open_btn = Button(
            text="Open Vault Interface",
            size_hint=(1, 0.2),
            background_color=(0.1, 0.6, 0.9, 1)
        )
        open_btn.bind(on_press=lambda instance: webbrowser.open('http://127.0.0.1:5000/'))

        layout.add_widget(status_label)
        layout.add_widget(open_btn)
        
        return layout

if __name__ == '__main__':
    AadiTechVaultApp().run()
