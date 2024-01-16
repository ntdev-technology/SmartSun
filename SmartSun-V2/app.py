from flask import Flask, render_template, request, jsonify, session, redirect, send_file, get_flashed_messages, flash, make_response

from jinja2.exceptions import TemplateNotFound
from SmartSunController.Controller import Controller
import datetime
import secrets
import re
import time
import subprocess

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)

version_info = (1, 2, "delta-1")
_debug = True
__version__ = '.'.join([str(x) for x in version_info])
_time_of_init = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
controller = Controller()
controller.startThreadedJob()

@staticmethod
def generate_malf(malf):
    match = re.match(r"Malfunction (\d+) - (.+)", malf)
    if match:
        malfunction_number = match.group(1)
        malfunction_reason = match.group(2)
    return malfunction_number, malfunction_reason

@app.context_processor
def setver():
    return dict(version=__version__)

    
@app.route('/favicon.ico')
def favicon():
	return send_file('static/assets/favicon.ico')

@app.route('/')
def index():
    
    if 'ignore' not in session:
        session['ignore'] = False

    main_state = request.args.get('state', 'welcome')
    if controller.MALFUNCTION and not session['ignore']:
        if _debug: print(controller.MALFUNCTION)
        malfunction_number, malfunction_reason = generate_malf(str(controller.MALFUNCTION))
        return render_template('welcome.html', malfunction_number=malfunction_number, malfunction_reason=malfunction_reason)
        

    if main_state == 'welcome':
        return render_template('welcome.html')
    elif main_state == 'setup':
        return render_template('setup.html')


@app.route('/get_information')
def get_system_information():
    # Fetch system information from your data source
    Current_info = controller.CurrentInfo()
    if _debug: print(f"Response from [Controller]: {Current_info}")
    
    last_calc = ':'.join(str(x) for x in list(Current_info.get('last_time_checked'))[:-1])
    man_time = ':'.join(str(x) for x in list(Current_info.get('mantime'))[:-1]) \
        if Current_info.get('mantime') != None else 'None'
    
    info = {
        'online_since': _time_of_init,
        'device': 'Raspberry pi 4',
        'elevation': str(Current_info.get('current_calculated_angle')[1]) + ' deg.',
        'azimuth': str(Current_info.get('current_calculated_angle')[0]) + ' deg.',
        'last_calculation': str(last_calc),
        'status': str(Current_info.get('status')),
        'timezone': str(Current_info.get('timezone')),
        'time_source': str(Current_info.get('time_source')),
        'calculation_method': str(Current_info.get('calculation_method')),
        'calculation_value': str(Current_info.get('calculation_value')),
        'location': str(Current_info.get('location')),
        'man_time': man_time,
    }
    return jsonify(info), 200

@app.route('/flash-messages')
def flash_messages():
	options = [
		'with-categories',
		'catagory'
		]

	kwargs = dict()
	if request.args:
		kwargs = dict(request.args)

	if request.headers:
		for key, value in dict(request.headers).items():
			key = key.lower()
			if key in options:
				kwargs[key.replace('-', '_')] = value
	
	if kwargs.get('with_categories'):
		flash_messages = []
		for mtype, message in get_flashed_messages(**kwargs):
			flash_messages.append({'message': message, 'type': mtype})
		return jsonify(flash_messages)
	
	return jsonify(get_flashed_messages(**kwargs))

@app.route('/ignore_malf')
def ignore_malfunction():
    session['ignore'] = True
    response = make_response(jsonify({'message': 'OK'}))
    response.status_code = 200
    return response



@app.route('/process_setup_data', methods=['POST'])
def process_setup_data():
    try:
        changed = False
        data = request.get_json()
        # item_ids:
        # 
        # setTime
        # MoveCords
        # setLocation
        # testSetup
        # setupCalcMethod
        # confirmPowerAction
        # manTime


        if _debug: print(data)
        item_id = data.get('itemId')
        input_data = data.get('selectedOption')
        extra_field = data.get('extraField')
        if _debug: print(item_id, input_data, extra_field)
        
        if item_id == 'setTime':
            controller.ChangeSetting(timectr=input_data)
            changed = True
        
        elif item_id == 'MoveCords':
            controller.manMove(x=int(input_data[0]), y=int(input_data[1]))
        
        elif item_id == 'setLocation':
            controller.ChangeSetting(loc_set=input_data)
            changed = True

        elif item_id == 'testSetup':
            if input_data == 'stpr_max':
                 controller.manMove(x=180, y=90)
            elif input_data == 'display':
                 controller.VSIStart()
            changed = False

        elif item_id == 'setupCalcMethod':
            controller.ChangeSetting(calc_cnf=input_data)
            controller.ChangeSetting(calc_val=int(extra_field))
            changed = True
        
        elif item_id == 'confirmPowerAction':
            if _debug: print(f"Ready: {input_data}")
            if extra_field == 'power_cycle':
                controller.stopThreadedJob()
                controller.stop_all()
                subprocess.call(["shutdown", "-r", "-t", "0", "-h"])
            elif extra_field == 'shut_down':
                controller.stopThreadedJob()
                controller.stop_all(
                subprocess.call(["shutdown", "-t", "0", "-h"])
        elif item_id == 'manTime':
            if not extra_field == '':
                date_parts = extra_field.split('/')
                date_tuple = tuple(map(int, date_parts))
                print(date_tuple)
                changed = True if not len(list(date_tuple)) == 5 else False
                controller.setManTime(man_time=date_tuple)
                controller.ChangeSetting(timectr=input_data)
            

        else:
            flash("ERROR: Item ID error")

        if changed:
            if _debug: print("[App] restarting thread...")
            session['ignore'] = False
            controller.Restart()

        response_data = {
            'status': 'success',
            'message': f'Data received for item {item_id}: {input_data}'
        }

        flash("Your changes have been processed successfully")

    except Exception:
        response_data = {
            'status': 'failed',
            'message': f'Trouble processing infromation for item {item_id}: {input_data}'
        }
        flash("There was some trouble whilst processing")
    
    return jsonify(response_data)

@app.errorhandler(TemplateNotFound)
def TemplateNotFoundHandler(e):
	return redirect('/')

@app.errorhandler(404)
def pageNotFoundHandler(e):
	return redirect('/')

@app.errorhandler(500)
def pageNotFoundHandler(e):
	flash("There was some trouble")
	return redirect('/')

# if __name__ == '__main__':
#     print("WARNING! YOU ARE NOT RUNNING IN A DEV ENVIROMENT!")
#     app.run()
