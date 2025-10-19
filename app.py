import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g,jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Block, Room, Bed, Person, Payment, Worker,Admin
from config import Config
from sqlalchemy.exc import IntegrityError
# Import for initial setup

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Database setup
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

def get_db_session():
    """Provides a database session for the current request."""
    if not hasattr(g, 'db_session'):
        g.db_session = DBSession()
    return g.db_session

@app.teardown_appcontext
def close_db_session(error):
    """Closes the database session at the end of the request."""
    if hasattr(g, 'db_session'):
        g.db_session.close()

# --- Admin Credentials from config ---
# Use the Config object directly to get admin credentials
#ADMIN_USERNAME = Config.ADMIN_USERNAME
#ADMIN_PASSWORD = Config.ADMIN_PASSWORD
# --- Initial Admin Setup ---
# Check and create the initial admin user if the database is empty
with app.app_context():
    Session = DBSession()
    if Session.query(Admin).count() == 0:
        # NOTE: In a production app, use password hashing (e.g., werkzeug.security)
        default_admin = Admin(
            username=Config.ADMIN_USERNAME, 
            password=Config.ADMIN_PASSWORD
        )
        try:
            Session.add(default_admin)
            Session.commit()
            print("Default admin user created.")
        except IntegrityError:
            Session.rollback()
            print("Admin user already existed (IntegrityError handled).")
    Session.close()

# --- Admin Credentials from config (REMOVED) ---
# Removed hardcoded credentials

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles admin login."""
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('home'))
    
    db_session = get_db_session()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 1. Query the Admin table
        admin_user = db_session.query(Admin).filter_by(username=username).first()
        
        # 2. Check credentials
        if admin_user and admin_user.password == password: # No hashing, direct comparison
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Handles admin password reset."""
    if 'logged_in' not in session or not session['logged_in']:
        flash("You must be logged in to reset the password.")
        return redirect(url_for('login'))

    db_session = get_db_session()
    
    # Assuming only one admin for simplicity, using the default username
    admin_user = db_session.query(Admin).filter_by(username=Config.ADMIN_USERNAME).first()

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password and new_password == confirm_password:
            # NOTE: Update the password directly (no hashing)
            admin_user.password = new_password
            db_session.commit()
            flash('Your password has been successfully reset.')
            return redirect(url_for('home'))
        else:
            flash('Error: Passwords do not match or field is empty.')
    
    # NOTE: You'll need a simple 'reset_password.html' template for this
    return render_template('reset_password.html')

'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles admin login."""
    if 'logged_in' in session and session['logged_in']:
        # This will redirect to the home function
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')
            # Correctly reference the template filename
            return render_template('login.html')
    # Correctly reference the template filename for GET requests
    return render_template('login.html')
'''

@app.route('/logout')
def logout():
    """Logs the admin out."""
    session.pop('logged_in', None)
    # Redirect to the 'login' function, not a filename
    return redirect(url_for('login'))

@app.before_request
def require_login():
    """Checks if the user is logged in before each request."""
    # Ensure the login endpoint is not protected
    if 'logged_in' not in session and request.endpoint not in ['login', 'static', None]:
        return redirect(url_for('login'))

@app.route('/')
def home():
    """Renders the home page."""
    # Correctly reference the template filename
    return render_template('home.html')

@app.route('/build', methods=['GET', 'POST'])
def build():
    """Handles adding blocks, rooms, and beds."""
    db_session = get_db_session()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_block':
            block_name = request.form.get('block_name')
            new_block = Block(name=block_name)
            db_session.add(new_block)
            flash(f'Block "{block_name}" added successfully!')
        elif action == 'add_room':
            block_id = request.form.get('block_id')
            room_name = request.form.get('room_name')
            bed_count = request.form.get('bed_count')
            if not block_id or not room_name or not bed_count:
                flash('Please fill all fields to add a room.')
            else:
                new_room = Room(name=room_name, bed_count=int(bed_count), block_id=block_id)
                db_session.add(new_room)
                # Create beds for the new room
                for i in range(1, int(bed_count) + 1):
                    new_bed = Bed(bed_number=i, room=new_room)
                    db_session.add(new_bed)
                flash(f'Room "{room_name}" with {bed_count} beds added successfully!')
        elif action == 'add_person':
            bed_id = request.form.get('bed_id')
            person_name = request.form.get('person_name')
            aadhar = request.form.get('aadhar')
            joining_date_str = request.form.get('joining_date')
            
            if not bed_id or not person_name or not aadhar or not joining_date_str:
                flash('Please fill all person details.')
            else:
                try:
                    joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
                    new_person = Person(name=person_name, aadhar=aadhar, joining_date=joining_date)
                    db_session.add(new_person)
                    db_session.flush() # To get the new person's ID

                    bed = db_session.query(Bed).filter_by(id=bed_id).first()
                    if bed:
                        bed.is_occupied=True
                        bed.person_id = new_person.id
                    flash(f'Person "{person_name}" added and assigned to bed successfully!')
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.')
        db_session.commit()
        return redirect(url_for('build'))

    blocks = db_session.query(Block).all()
    # Correctly reference the template filename
    return render_template('build.html', blocks=blocks)


@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    """Deletes a room and its associated beds, but prevents deletion if beds are occupied."""
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    db_session = get_db_session()
    room_to_delete = db_session.query(Room).filter_by(id=room_id).first()

    if not room_to_delete:
        flash('Room not found.', 'error')
        return redirect(url_for('build'))

    # Check if any beds in this room are occupied
    occupied_beds = db_session.query(Bed).filter(
        Bed.room_id == room_id, 
        Bed.is_occupied == True # Using the correct attribute
    ).count()

    if occupied_beds > 0:
        flash(f'Cannot delete room "{room_to_delete.name}". It still has {occupied_beds} occupied bed(s).', 'error')
    else:
        # SQLAlchemy cascade='all, delete-orphan' handles deletion of associated beds
        db_session.delete(room_to_delete)
        db_session.commit()
        flash(f'Room "{room_to_delete.name}" and all its beds have been deleted successfully.')
    
    return redirect(url_for('build'))

@app.route('/profile')
def profile():
    """Displays whole statistics of the hostel (rooms occupancy block-wise)."""
    db_session = get_db_session()
    
    # 1. Global Statistics
    total_beds = db_session.query(Bed).count()
    occupied_beds = db_session.query(Bed).filter(Bed.is_occupied == True).count()
    unoccupied_beds = total_beds - occupied_beds
    
    # Calculate global occupancy percentage
    global_occupancy_percent = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    
    # Other counts
    total_persons = db_session.query(Person).filter(Person.leaving_date == None).count()
    total_workers = db_session.query(Worker).count()
    total_rooms = db_session.query(Room).count()

    # 2. Block-wise Statistics
    blocks = db_session.query(Block).all()
    block_stats = []
    
    for block in blocks:
        block_rooms = db_session.query(Room).filter(Room.block_id == block.id).all()
        
        block_total_beds = sum(room.bed_count for room in block_rooms)
        
        # Query occupied beds only for this block's rooms
        block_occupied_beds = db_session.query(Bed).join(Room).filter(
            Room.block_id == block.id,
            Bed.is_occupied == True
        ).count()
        
        block_occupancy_percent = (block_occupied_beds / block_total_beds * 100) if block_total_beds > 0 else 0

        block_stats.append({
            'name': block.name,
            'total_rooms': len(block_rooms),
            'total_beds': block_total_beds,
            'occupied_beds': block_occupied_beds,
            'unoccupied_beds': block_total_beds - block_occupied_beds,
            'occupancy_percent': round(block_occupancy_percent, 2)
        })

    # NOTE: You'll need a 'profile.html' template to display this data
    return render_template(
        'profile.html', 
        global_stats={
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'unoccupied_beds': unoccupied_beds,
            'occupancy_percent': round(global_occupancy_percent, 2),
            'total_persons': total_persons,
            'total_workers': total_workers,
            'total_rooms': total_rooms
        },
        block_stats=block_stats
    )

@app.route('/accommodate')
def accommodate():
    """Renders the accommodate page with filtering options."""
    db_session = get_db_session()
    
    blocks = db_session.query(Block).all()
    rooms = db_session.query(Room).all()
    beds = db_session.query(Bed).all()
    
    # Correctly reference the template filename
    return render_template('accommodate.html', blocks=blocks, rooms=rooms, beds=beds)

@app.route('/accommodate/filter', methods=['POST'])
def filter_accommodate():
    """API endpoint to filter beds."""
    db_session = get_db_session()
    
    block_id = request.form.get('block_filter')
    room_id = request.form.get('room_filter')
    occupied_status = request.form.get('occupied_status')
    
    query = db_session.query(Bed).join(Room).join(Block).outerjoin(Person)
    
    if block_id:
        query = query.filter(Block.id == block_id)
    if room_id:
        query = query.filter(Room.id == room_id)
    if occupied_status == 'filled':
        query = query.filter(Bed.is_occupied== True)
    elif occupied_status == 'empty':
        query = query.filter(Bed.is_occupied== False)
    
    filtered_beds = query.all()

    return render_template('_bed_table.html', beds=filtered_beds) # Using a partial template

@app.route('/payments', methods=['GET', 'POST'])
def payments():
    """Handles monthly payment tracking."""
    db_session = get_db_session()
    blocks = db_session.query(Block).all()
    
    if request.method == 'POST':
        person_name_search = request.form.get('person_name')
        room_name_search = request.form.get('room_name')
        
        query = db_session.query(Person).join(Bed).join(Room).join(Block).outerjoin(Payment)
        
        if person_name_search:
            query = query.filter(Person.name.like(f'%{person_name_search}%'))
        if room_name_search:
            query = query.filter(Room.name.like(f'%{room_name_search}%'))
        
        persons = query.all()
        # Correctly reference the template filename
        return render_template('payments.html', blocks=blocks, persons=persons, searched=True)
        
    persons = db_session.query(Person).join(Bed).join(Room).join(Block).all()
    # Correctly reference the template filename
    return render_template('payments.html', blocks=blocks, persons=persons)

@app.route('/update_payment/<int:person_id>/<string:month>', methods=['POST'])
def update_payment(person_id, month):
    """API endpoint to update a payment status."""
    db_session = get_db_session()
    
    # Get the JSON data from the request body
    data = request.get_json()
    status = data.get('status')
    eb_amount = data.get('eb_amount')

    # Convert empty string to None if needed
    if eb_amount == '':
        eb_amount = None

    payment = db_session.query(Payment).filter_by(person_id=person_id, month=month).first()
    if not payment:
        payment = Payment(person_id=person_id, month=month)
        db_session.add(payment)
    
    payment.status = status
    payment.eb_amount = eb_amount
    db_session.commit()
    return jsonify({'status': 'OK'})

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    """Handles staff management."""
    db_session = get_db_session()
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        mobile = request.form.get('mobile')
        gender = request.form.get('gender')
        new_worker = Worker(name=name, department=department, mobile=mobile, gender=gender)
        db_session.add(new_worker)
        db_session.commit()
        flash(f'Staff member "{name}" added successfully!')
        return redirect(url_for('staff'))
    
    workers = db_session.query(Worker).all()
    # Correctly reference the template filename
    return render_template('staff.html', workers=workers)

@app.route('/guests', methods=['GET', 'POST'])
def guests():
    """Handles guest information (including those who have left)."""
    db_session = get_db_session()
    
    if request.method == 'POST':
        block_filter = request.form.get('block_filter')
        room_filter = request.form.get('room_filter')
        month_filter = request.form.get('month_filter')
        
        query = db_session.query(Person).join(Bed).join(Room).join(Block)
        
        if block_filter:
            query = query.filter(Block.name == block_filter)
        if room_filter:
            query = query.filter(Room.name == room_filter)
        if month_filter:
            query = query.filter(Person.leaving_date.like(f'%-{month_filter}-%'))

        guests = query.all()
        # Correctly reference the template filename
        return render_template('guests.html', guests=guests, blocks=db_session.query(Block).all(), rooms=db_session.query(Room).all())

    guests = db_session.query(Person).join(Bed).join(Room).join(Block).all()
    # Correctly reference the template filename
    return render_template('guests.html', guests=guests, blocks=db_session.query(Block).all(), rooms=db_session.query(Room).all())

@app.route('/person/<int:person_id>/leave', methods=['POST'])
def mark_person_left(person_id):
    """Marks a person as having left and frees up their bed."""
    db_session = get_db_session()
    person = db_session.query(Person).filter_by(id=person_id).first()
    if person:
        person.leaving_date = datetime.now().date()
        bed = db_session.query(Bed).filter_by(person_id=person.id).first()
        if bed:
            bed.is_occupied = False 
            bed.person_id = None
        db_session.commit()
        flash(f'Person "{person.name}" has been marked as left.')
    # Redirect to the 'guests' function, not a filename
    return redirect(url_for('guests'))

if __name__ == '__main__':
    # Set the secret key for sessions and flash messages
    app.secret_key = Config.SECRET_KEY
    app.run(debug=True)
