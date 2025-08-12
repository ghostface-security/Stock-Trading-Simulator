Deployment Guide: Stock Trading Simulator on Raspberry Pi
This guide details how to deploy the Stock Trading Simulator Flask application on a Raspberry Pi, configure it as a systemd service, and expose it publicly using ngrok.
1. Prerequisites
Before you begin, ensure you have the following:
 * Hardware:
   * Raspberry Pi (Model 3, 4, or 5 recommended for performance)
   * SD Card (minimum 16GB, 32GB+ recommended)
   * Raspberry Pi Power Supply
   * Another computer with SSH client (e.g., PuTTY on Windows, built-in terminal on Linux/macOS)
 * Software (on your computer):
   * Raspberry Pi Imager (or similar tool to flash OS to SD card)
 * Software (on Raspberry Pi - will be installed):
   * Raspberry Pi OS Lite (64-bit recommended for server deployments)
   * Python 3 and pip
   * venv (Python virtual environment)
   * systemd (for service management, comes with OS)
   * ufw (Uncomplicated Firewall)
   * ngrok (for public tunneling)
2. Raspberry Pi Initial Setup
 * Flash Raspberry Pi OS:
   * Download Raspberry Pi OS Lite (64-bit)
   * Use Raspberry Pi Imager to flash the OS to your SD card.
   * Crucially, use the Imager's advanced options (Ctrl+Shift+X or cog icon) to:
     * Enable SSH
     * Set a strong password for the pi user (e.g., 16+ characters, mixed case, numbers, symbols).
     * Configure Wi-Fi (if not using Ethernet).
 * Boot and Connect:
   * Insert the SD card into your Raspberry Pi and power it on.
   * Find your Pi's IP address on your local network (check your router's connected devices or use nmap).
   * SSH into your Pi from your computer:
     ssh pi@<Raspberry_Pi_IP_Address>

     (e.g., ssh pi@192.168.1.100)
 * Update and Upgrade:
   sudo apt update && sudo apt upgrade -y

 * Install ufw (Uncomplicated Firewall):
   sudo apt install ufw -y

   * Configure UFW rules:
     sudo ufw allow ssh        # Allow SSH (port 22)
sudo ufw allow 5000/tcp   # Allow your Flask app (port 5000)
sudo ufw enable           # Enable the firewall (confirm with 'y')
sudo ufw status verbose   # Verify rules

3. Application Deployment
 * Clone the Repository:
   Navigate to your home directory and clone your project:
   cd ~
git clone https://github.com/ghostface-security/Stock-Trading-Simulator.git && cd Stock-Trading-Simulator

 * Create and Activate Virtual Environment:
   python3 -m venv venv
source venv/bin/activate

 * Install Dependencies:
   pip install -r requirements.txt

   (Ensure your requirements.txt is up-to-date with Flask, Flask-SQLAlchemy, Flask-Bcrypt, Flask-WTF, APScheduler, etc.)
 * Update app.py for Production:
   Open app.py for editing:
   nano app.py

   Find the app.run() line near the bottom:
   app.run(debug=True, port=5000, use_reloader=False)
   Change debug=True to debug=False for security in a public deployment:
   app.run(debug=False, port=5000, use_reloader=False)
   Save and exit (Ctrl+X, then Y, then Enter).
4. Running the Application with systemd
Using systemd ensures your application starts automatically on boot and recovers from crashes.
 * Create a Startup Script (start_website.sh):
   Create a new file in your project root:
   nano start_website.sh

   Paste the following content:
   #!/bin/bash
cd /home/pi/Stock-Trading-Simulator
source venv/bin/activate
exec python3 app.py

   Save and exit.
 * Make the Script Executable:
   chmod +x start_website.sh

 * Create a systemd Service File:
   sudo nano /etc/systemd/system/stock-trading-sim.service

   Paste the following content:

[Unit]
Description=Stock Trading Simulator Flask Application
After=network.target
[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/Stock-Trading-Simulator
ExecStart=/home/pi/Stock-Trading-Simulator/start_website.sh
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

   Save and exit.
 * Enable and Start the Service:
   sudo systemctl daemon-reload           # Reload systemd to recognize new service
sudo systemctl enable stock-trading-sim.service # Enable service to start on boot
sudo systemctl start stock-trading-sim.service  # Start the service now

 * Verify Service Status and Logs:
   sudo systemctl status stock-trading-sim.service
sudo journalctl -u stock-trading-sim.service -f

   You should see active (running) and the Flask application's startup logs.
5. Exposing with ngrok
ngrok creates a secure tunnel from your local Flask app to a public URL.
 * Install ngrok:
   curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok -y

 * Authenticate ngrok:
   * Go to ngrok.com and create an account.
   * Copy your Authtoken from your ngrok dashboard.
   * On your Raspberry Pi, run:
     ngrok authtoken <YOUR_NGROK_AUTHTOKEN>

 * Start the ngrok Tunnel:
   ngrok http 5000

   This will display a public URL (e.g., https://xxxx-yyyy-zzzz.ngrok-free.app) that tunnels to your Flask application running on port 5000. Keep this terminal window open.
6. Important Notes
 * ngrok is for development/testing: The free ngrok tunnel changes every time you restart it. For a permanent public URL, you'd need a paid ngrok plan or a custom domain with a reverse proxy (like Nginx/Apache).
 * Security: This deployment guide includes basic security measures (UFW, secure password hashing, CSRF). For a production application, further hardening (e.g., HTTPS with Certbot, more robust logging, intrusion detection) would be necessary.
 * Database: The application uses SQLite, which is file-based. While the database file is moved out of web-accessible paths, for high-traffic or multi-user production apps, a dedicated database server (like PostgreSQL or MySQL) is generally recommended.
