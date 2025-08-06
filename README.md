# Stock-Trading-Simulator

Stock-Trading-Simulator is a web application that simulates a personal banking and stock market trading platform. It provides users with a secure environment to manage their funds, transfer money to other users, and engage in simulated stock trading with real-time price updates.
Features

    Secure User Management: Features secure user registration and login with robust password hashing. A "Forgot Password" function allows users to securely reset their credentials using a unique, one-time token.

    Banking Dashboard:

        Deposits & Withdrawals: Easily add or remove funds from your account.

        Peer-to-Peer Transfers: Transfer money to other registered users within the platform.

        Transaction History: View a complete history of all recent banking activities, including deposits, withdrawals, and transfers.

    Fee System:

        Small, transparent fees are automatically applied to withdrawals and all stock trades (purchases and sales).

        All collected fees are systematically stored in a dedicated, non-loginable Global_Exchange account.

    Dynamic Stock Market Simulation:

        The platform provides a marketplace with simulated stock prices for popular companies (e.g., AAPL, GOOG, MSFT, AMZN, TSLA, NFLX, SBUX, NKE, KO).

        Stock prices are updated automatically every 60 seconds to mimic real-world market fluctuations.

        Users can buy and sell shares, with real-time effects on their account balance and portfolio.

        A personal portfolio tracks all stock holdings, displaying their current value and calculating the profit/loss percentage.

    Modern User Interface: The application is designed to be modern, clean, and fully responsive, ensuring a seamless experience across all screen sizes.

Security Enhancements

This project has undergone significant security hardening to make it more robust, especially for deployment as a public web server. Key enhancements include:

    Secure Password Hashing: Upgraded from SHA-256 to Flask-Bcrypt, an industry-standard, adaptive hashing algorithm that incorporates unique salts for each password, greatly increasing resistance to brute-force and rainbow table attacks.

    CSRF (Cross-Site Request Forgery) Protection: Implemented Flask-WTF with CSRFProtect to prevent malicious requests originating from other websites.

    Secure Password Reset Links: Modified the password reset functionality to ensure sensitive tokens are no longer displayed in the user's browser, instead logging them securely on the server side.

    Secure Database File Location: The SQLite database file (database.db) has been moved to a non-web-accessible directory (/instance/database.db), preventing direct public access to sensitive user data.

    Network Firewall (UFW) Configuration: Instructions and configuration for setting up a firewall on the Raspberry Pi to limit incoming connections to only essential services (SSH and the web application port), significantly reducing the network attack surface.

Technologies Used

    Backend:

        Python: The core programming language for the application logic.

        Flask: A lightweight web framework used to build the application's routes and structure.

        Flask-SQLAlchemy: An Object-Relational Mapper (ORM) that simplifies database interactions with SQLite.

        APScheduler: A task-scheduling library that powers the periodic, automatic updates of stock prices.

        Flask-Bcrypt: Used for robust and irreversible password hashing.

        Flask-WTF: Provides CSRF protection for web forms.

    Frontend:

        HTML: Provides the fundamental structure of all web pages.

        CSS: Styles the application with a clean, professional, and visually appealing aesthetic.

        JavaScript: Handles client-side logic, including the dynamic display of stock prices and portfolio values without requiring a page refresh.

    Database:

        SQLite: A lightweight, file-based database used to store all user data, transaction records, and stock information.

Installation & Local Development

To get the project up and running on your local machine for development:

    Clone the repository:

    git clone https://github.com/ghostface-security/Stock-Trading-Simulator.git
    cd Stock-Trading-Simulator

    Set up a virtual environment:
    It's a best practice to use a virtual environment to manage dependencies.

    python3 -m venv venv
    # On macOS/Linux
    source venv/bin/activate
    # On Windows
    venv\Scripts\activate

    Install dependencies:
    Use pip to install all the required libraries listed in requirements.txt.

    pip install -r requirements.txt

    Run the application:
    The application will automatically create the SQLite database file and start the stock price updates when launched.

    python3 app.py

    The application will now be running on http://127.0.0.1:5000.

Deployment to Raspberry Pi (Public Web Server)

For detailed instructions on deploying this application to a Raspberry Pi as a public web server, including systemd service setup, firewall configuration, and ngrok tunneling, please refer to the dedicated deployment guide:

    DEPLOYMENT.md

Usage

    Register: Navigate to the home page and create a new user account. If you forget your password, the "Forgot Password?" feature is available on the login page.

    Log In: Use your new credentials to log in. You'll be taken to the Banking Dashboard.

    Banking: On the Banking Dashboard, you can add or remove funds, and transfer money to other users. You can also view a detailed transaction history.

    Stock Market: Go to the Stock Market page to view real-time prices, buy and sell shares, and track your personal investment portfolio and its performance.
