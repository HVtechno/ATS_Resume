import threading
import webview
from app import app

def start_flask():
    print("Starting Flask server...")
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    webview.create_window("ATS Resume Analyzer", "http://127.0.0.1:5000", width=1000, height=800)
    webview.start(gui='qt', http_server=True)