import sqlite3
import random
import shutil
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def get_db_connection():
    # App Engine fix: Copy DB to writable /tmp folder
    if not os.path.exists('/tmp/track_meet.db'):
        shutil.copy('track_meet.db', '/tmp/track_meet.db')

    conn = sqlite3.connect('/tmp/track_meet.db')
    conn.row_factory = sqlite3.Row
    # Requirement 3c: Isolation Level
    conn.execute('PRAGMA journal_mode=WAL') 
    return conn

def init_db():
    """Initializes the database with 20 random athletes and automated ranking."""
    conn = get_db_connection()
    tables = ['Results', 'Entry', 'Meets', 'Events', 'Athletes', 'Teams']
    for table in tables:
        conn.execute(f'DROP TABLE IF EXISTS {table}')

    # Create Tables
    conn.execute("CREATE TABLE Teams (team_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
    conn.execute("CREATE TABLE Athletes (athlete_id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER, name TEXT NOT NULL, age INTEGER, gender TEXT, FOREIGN KEY (team_id) REFERENCES Teams(team_id))")
    conn.execute("CREATE TABLE Events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
    conn.execute("CREATE TABLE Meets (meet_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, meet_date DATE)")
    conn.execute("CREATE TABLE Entry (entry_id INTEGER PRIMARY KEY AUTOINCREMENT, athlete_id INTEGER, event_id INTEGER, meet_id INTEGER, FOREIGN KEY (athlete_id) REFERENCES Athletes(athlete_id), FOREIGN KEY (event_id) REFERENCES Events(event_id), FOREIGN KEY (meet_id) REFERENCES Meets(meet_id))")
    conn.execute("CREATE TABLE Results (result_id INTEGER PRIMARY KEY AUTOINCREMENT, entry_id INTEGER, final_time REAL, FOREIGN KEY (entry_id) REFERENCES Entry(entry_id) ON DELETE CASCADE)")

    # Seed Teams
    teams = [('Purdue Track',), ('Indiana Track',), ('Illinois Track',), ('Michigan Track',), ('Ohio State Track',), ('Wisconsin Track',)]
    conn.executemany("INSERT INTO Teams (name) VALUES (?)", teams)

    # Seed Events 
    events = [('Sprint',), ('Middle Distance',), ('Long Distance',), ('Hurdles',)]
    conn.executemany("INSERT INTO Events (name) VALUES (?)", events)

    # Seed Meets
    meets = [('Big Ten Invite', '2026-04-10'), ('Midwest Classic', '2026-04-18')]
    conn.executemany("INSERT INTO Meets (name, meet_date) VALUES (?, ?)", meets)

    # Seed Athletes 
    first_names = [
    "Alex","Jordan","Taylor","Chris","Morgan","Casey","Riley","Cameron","Jamie","Quinn",
    "Avery","Dakota","Reese","Skyler","Parker","Rowan","Sawyer","Emerson","Finley","Harper",
    "Logan","Hayden","Blake","Kendall","Payton","Charlie","Drew","Elliot","River","Sage",
    "Phoenix","Tatum","Lane","Shawn","Devin","Kai","Micah","Noel","Ari","Shiloh",
    "Tyler","Jesse","Bailey","Spencer","Robin","Frankie","Dakari","Justice","London","Remy"
    ]
    
    last_names = [
    "Johnson","Smith","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts"
    ]
    
    athlete_data = []
    for _ in range(20):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = random.randint(18, 23)
        gender = random.choice(['M', 'F'])
        team_id = random.randint(1, 6)
        athlete_data.append((team_id, name, age, gender))
    
    conn.executemany("INSERT INTO Athletes (team_id, name, age, gender) VALUES (?, ?, ?, ?)", athlete_data)

    # Seed initial results for all 20 athletes across all 4 events 
    for a_id in range(1, 21):
        # added this loop to include Meet 1 and Meet 2
        for m_id in [1, 2]:  
            for e_id in range(1, 5):
                #sprint/hurdles
                if e_id in [1, 4]: base = 10.0 
                # Middle Distance
                elif e_id == 2: base = 110.0
                # Long Distance
                else: base = 300.0                 
                
                # Add a little random variation so times aren't identical between meets
                time = round(base + random.uniform(0.5, 15.0), 2)
                
                cur = conn.execute("INSERT INTO Entry (athlete_id, event_id, meet_id) VALUES (?, ?, ?)", (a_id, e_id, m_id))
                conn.execute("INSERT INTO Results (entry_id, final_time) VALUES (?, ?)", (cur.lastrowid, time))

    # STAGE 3: Optimization Indexes
    # Speeds up the automated ranking report (Requirement 2)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_results_time ON Results(final_time)")
    # Speeds up the age-based filtering report
    conn.execute("CREATE INDEX IF NOT EXISTS idx_athlete_age ON Athletes(age)")
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    # Requirement 2: Automated Ranking via SQL Window Function
    results = conn.execute('''
        SELECT 
            r.result_id, a.name AS athlete_name, e.name AS event_name, m.name AS meet_name, r.final_time,
            RANK() OVER (PARTITION BY en.meet_id, en.event_id ORDER BY r.final_time ASC) as calculated_place
        FROM Results r
        JOIN Entry en ON r.entry_id = en.entry_id
        JOIN Athletes a ON en.athlete_id = a.athlete_id
        JOIN Events e ON en.event_id = e.event_id
        JOIN Meets m ON en.meet_id = m.meet_id
        ORDER BY meet_name, event_name, final_time ASC
    ''').fetchall()
    conn.close()
    return render_template('index.html', results=results)

@app.route('/add_athlete', methods=['GET', 'POST']) # Change: Allow GET and POST
def add_athlete():
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            with conn:
                # Retrieve data from your HTML form
                name = request.form.get('name')
                age = request.form.get('age')
                gender = request.form.get('gender')
                team_id = request.form.get('team_id')

                # STAGE 3: Parameterized query (SQL Injection Protection)
                conn.execute(
                    "INSERT INTO Athletes (name, age, gender, team_id) VALUES (?, ?, ?, ?)",
                    (name, age, gender, team_id)
                )
            return redirect(url_for('index'))
        finally:
            conn.close()
            
    # GET logic: If just loading the page, show the form
    teams = conn.execute('SELECT * FROM Teams').fetchall()
    conn.close()
    return render_template('add_athlete.html', teams=teams)

@app.route('/add_result', methods=['GET', 'POST'])
def add_result():
    conn = get_db_connection()
    if request.method == 'POST':
        try:
            with conn:
                # Use '?' to maintain SQL Injection protection
                cur = conn.execute(
                    'INSERT INTO Entry (athlete_id, event_id, meet_id) VALUES (?, ?, ?)', 
                    (request.form['athlete_id'], request.form['event_id'], request.form['meet_id'])
                )
                conn.execute(
                    'INSERT INTO Results (entry_id, final_time) VALUES (?, ?)', 
                    (cur.lastrowid, request.form['final_time'])
                )
            return redirect(url_for('index'))
        finally:
            conn.close()

    # Requirement 2c: Dynamic UI for dropdowns
    athletes = conn.execute('SELECT * FROM Athletes ORDER BY name ASC').fetchall()
    events = conn.execute('SELECT * FROM Events').fetchall()
    meets = conn.execute('SELECT * FROM Meets').fetchall()
    conn.close()
    return render_template('add_result.html', athletes=athletes, events=events, meets=meets)

@app.route('/edit_result/<int:id>', methods=['GET', 'POST'])
def edit_result(id):
    conn = get_db_connection()
    if request.method == 'POST':
        final_time = request.form['final_time']
        # STAGE 3: Parameterized UPDATE query
        conn.execute('UPDATE Results SET final_time = ? WHERE result_id = ?', (final_time, id))        
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    # GET logic: Load the current data into the form
    result = conn.execute('SELECT * FROM Results WHERE result_id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit_result.html', result=result)

@app.route('/delete_result/<int:id>')
def delete_result(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Results WHERE result_id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/filter_athletes')
def filter_athletes():
    # Default to min 18 and max 25 
    min_age = request.args.get('min_age', 18) 
    max_age = request.args.get('max_age', 25) 
    conn = get_db_connection()
    athletes = conn.execute('SELECT a.*, t.name as team_name FROM Athletes a JOIN Teams t ON a.team_id = t.team_id WHERE age BETWEEN ? AND ?', (min_age, max_age)).fetchall()
    conn.close()
    
    # Send the ages back to the template
    return render_template('athlete_report.html', athletes=athletes, min_age=min_age, max_age=max_age)

if __name__ == '__main__':
    init_db() 
    app.run(debug=True, host='0.0.0.0', port=8080)