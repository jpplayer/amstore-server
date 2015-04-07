from app import app
from flask import Flask, send_from_directory
from flask import jsonify, abort, request, url_for
import os, shutil
import yaml

from werkzeug import secure_filename

applications = []
# For caching purpose. TODO: Use a database instead. This is maintained by upsert_application ().
applications_latest = []

# Upload section
def allowed_file(filename):
    return '.' in filename and \
		filename.endswith( '.tar.gz' ) or filename.endswith('.tgz')
#           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

import threading
class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)

# This is how to use the above
#def someOtherFunc(data, key):
#    print "someOtherFunc was called : data=%s; key=%s" % (str(data), str(key))
# 
#t1 = FuncThread(someOtherFunc, [1,2], 6)
#t1.start()
#t1.join()

# Expand tarfile
import tarfile
def untar(fname, path):
    tar = tarfile.open(fname)
    tar.extractall(path)
    tar.close()

# Get actual folder. It's the filename minus the extension
# This is used prior to 
def get_clean_folder( filename ):
	# There has to be a better way !
	if filename.endswith( '.tar.gz' ):	
		return filename[:-7] 
	if filename.endswith( '.tgz' ):
		return filename[:-4] 
#	os.path.splitext( filename )[0]

def list_folders( path ):
	return [name for name in os.listdir(path)
            if os.path.isdir(os.path.join(path, name))]

# START - Class Application

# Convention: app-id/version/
def app_get_application_dir( application ):
	return app.config['APPS_FOLDER'] + '/' + application['app_id'] + '/' + application['version']

# application_dir is the folder that contains config.yml
# Must be relative to app.config['APPS_FOLDER']
def make_application_from_folder( application_dir ):
	#Check first if the file exits
	if ( not os.path.isfile(  application_dir + "/config.yml" ) ):
		return
	# In a bad case the file could get blank, user might have made a typo in app_id or version, etc. We rebuild the minimum based on the folder.
	application = { "package": "" } 
	application['app_id'] = application_dir.split('/')[-2]
	application['version'] = application_dir.split('/')[-1]
	# TODO Should be done in constructor:	
	application['id'] = application['app_id'] + '-' + application['version']

	try: 
           #should use safe_load
           config = yaml.load(file( application_dir + "/config.yml"))
           config['id'] = config['app_id'] + "-" + str(config['version'])
	   application = config
	   print 'for application ' + application['id'] + ' using folder ' + application_dir
	except:
	   print "Error loading application in " + application_dir

	return application

def upsert_application( application_dir ):
	application =  make_application_from_folder( application_dir )

	# Upsert if same version 
	found = False
	for i in range( len(applications) ):	
		if applications[i]['app_id'] == application['app_id']:
			if applications[i]['version'] == application['version']:
				applications[i] = application
				found = True
	if not found:
		applications.append(application)	
	# Add to cache
	app_upsert_latest_application( application )
	return application


def app_upsert_latest_application( application ):
	# Upsert if newer version
        found = False
        for i in range( len(applications_latest) ):
                if applications_latest[i]['app_id'] == application['app_id']:
                        found = True
                        if applications_latest[i]['version'] <= application['version']:
                                applications_latest[i] = application
        if not found:
                applications_latest.append(application)


# Create a new application using an extracted archive
def app_create_application_from_archive( archive ):

        if archive and allowed_file(archive.filename):
                filename = secure_filename(archive.filename)

                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                archive.save(filepath)

                tmp_folder =  get_clean_folder( filename )

                expanded_folder =  app.config['UPLOAD_FOLDER'] + '/' + tmp_folder
                print 'expanding ' + filepath + ' to ' + expanded_folder
                untar( filepath, expanded_folder)

                # Look in root of archive first
		tmp_application_dir = expanded_folder
                application_onload =  make_application_from_folder( tmp_application_dir )

                # If not found, look in first folder of archive
		if not application_onload :
                	local_dir=list_folders( expanded_folder )[0]
                	tmp_application_dir = expanded_folder + '/' + local_dir
			application_onload =  make_application_from_folder( tmp_application_dir )
		
		else:
			return  # TODO Should throw an exception

                # Move all files from local_dir into application_dir
                application_dir =  app_get_application_dir( application_onload )
		# mv local_dir/* application_dir
		# Remove anything that was there first.
		if os.path.exists( application_dir ):
			shutil.rmtree( application_dir )
                print 'Moving file in ' + tmp_application_dir + ' to ' + application_dir
		names = os.listdir( tmp_application_dir)
		# Ensure target directory exists
		if not os.path.exists( application_dir ):
			os.makedirs( application_dir)
		for name in names:
			shutil.move( tmp_application_dir + '/' + name, application_dir )
#                untar( filepath, app_folder)

                #print 'loading application at ' + os.path.join(app.config['APPS_FOLDER'], app_folder)
                application = upsert_application( application_dir )
		return application
	return

# Update application based on config file
def app_update_config_from_file( configfile ):
     if configfile and configfile.filename.endswith('.yml'):
           filename = secure_filename(configfile.filename)
           # TODO This may not be thread safe !
           filepath = os.path.join( app.config['UPLOAD_FOLDER'], filename )
           configfile.save(filepath)

           # Read the file to get app_id and version
           print 'attempting to read ' + filepath
           config = yaml.load(file( filepath ))
	   print 'Found values: ' + config['app_id'] + '-' + config['version']

           # Identify application
           application_id = config['app_id'] + '-' + config['version']
           applications_for_id = [application for application in applications if application['id'] == application_id]
           
	   if len(applications_for_id) == 0:
		print "Could not find application"
		return

#                        abort(404, 'Application ' +  config['app_id'] + ' with version ' +  config['version'] + 'not found.')
	   application = applications_for_id[0]

           # Save file to application directory
	   print 'SUCCESS: attempting to save to ' +  app_get_application_dir( application )  + '/config.yml'
           #file newfile = open( app_get_application_dir( application ) + '/config.yml', 'w')   
	   #newfile.
	   shutil.move( filepath,  app_get_application_dir( application ) + '/config.yml' )

           # Reload
           application = upsert_application(  app_get_application_dir( application ) )

           return application 

# TODO Use a database to make this much faster and cache it
def app_get_latest_applications():
	return applications_latest;

# END - Class Application

# Initialize ALL from disk. Ignore any errors.
for dir in list_folders( app.config['APPS_FOLDER'] ):
	try:
	   for vdir in list_folders( app.config['APPS_FOLDER'] + '/' + dir ):
	      upsert_application( app.config['APPS_FOLDER'] + '/' + dir + '/' + vdir)
	except:
	   print 'Errors encountered loading application in directory: ' + dir



# TODO: only return the main values. Client must drill down for more information.
def make_public_application(application):
    new_application = application
    new_application['uri'] = url_for('get_application', application_id=application['id'], _external=True)
    if application['package'] :
	# We support exernal URIs like http://, https://. We can also serve the package from the store directly.
	if application['package'].startswith('http://') or  application['package'].startswith('https://'):
		new_application['package_uri'] =  application['package']
	else :
		# Must be relative to the APPS folder
    		filename =  application['app_id'] + '/' + application['version'] + '/' + application['package']
    		new_application['package_uri'] = url_for( 'serve_file', path=filename, _external=True )   
	
#    for field in application:
#        if field == 'id':
#            new_application['uri'] = url_for('get_application', application_id=application['id'], _external=True)
#        else:
#            new_application[field] = application[field]
    return new_application

@app.route('/')
def hello():
	return '''
<html>
<title>Amstore REST API</title>
<body>
Amstore REST API<br>
<a href="/api/v1/applications">List all applications</a><br>
<a href="/api/v1/submit_application">Submit an application</a><br>
<a href="/api/v1/submit_config">Update an application configuration</a><br>
<a href="/api/v1/delete_application_form">Delete an application</a><br>
</body>	
	'''
@app.route('/api/v1/status', methods=['GET'])

def status():
	response = {}
	response['code'] = '200'
	response['message'] = 'All systems ok'
	return jsonify ( response )

@app.route('/resource/<path:path>')
def serve_file(path):
	print 'processing ' + path
	return send_from_directory( app.config['APPS_FOLDER'], path, as_attachment=True)
	

#@app.route('/resources/<path:filename>')
#def serve_file(filename):
#	print 'attempting to serve: ' + filename
#	return send_from_directory( app.config['APPS_FOLDER'] + '/', filename )

#EXAMPLE, see http://flask.pocoo.org/docs/0.10/api/ for hints on improving performance.
#@app.route('/api/v1/applications/<string:application_id>/resources/<path:filename>')
#def get_file(application_id, filename):
#	application = [application for application in applications if application['id'] == application_id]
#    	return send_from_directory( app.config['APPS_FOLDER'] + '/' + application_id + '/' + application[0]['folder'], filename, as_attachment=True  )

@app.route('/api/v1/applications', methods=['GET'])

def get_applications():
    return jsonify( {'applications': [make_public_application(application) for application in app_get_latest_applications() ]} ) 

@app.route('/api/v1/applications/<string:application_id>', methods=['GET'])
def get_application(application_id):
	application = [application for application in applications if application['id'] == application_id]
	if len(application) == 0:
		abort(404)
	return jsonify( {'application': make_public_application( application[0]) }) 

@app.route('/api/v1/config', methods=['POST','PUT'])
def create_update_config():
     if not request.files or not 'file' in request.files:
          abort(400)
     configfile = request.files['file']

 
     try :
		application =  app_update_config_from_file( configfile )
		return jsonify( {'application':  application })
     except yaml.YAMLError, e:
		#TODO create exceptions
		if hasattr(e, 'problem_mark'):
			mark = e.problem_mark
			line = mark.line + 1
			col = mark.column + 1
			abort( 400, 'Error parsing YAML file at line ' + str(line) + ' column ' + str(col)  )
                abort( 400, 'Error parsing YAML file: ') 
	
@app.route('/api/v1/applications', methods=['POST'])

def create_application():
	if not request.files or not 'file' in request.files:
		abort(400)
	file = request.files['file']

	try:
		application = app_create_application_from_archive ( file )
		return jsonify({'application':  make_public_application(application) }), 201

	except yaml.YAMLError, e:
		abort( 400, 'Error parsing YAML file: ' + e)


# Test create application
# curl -i -H "Content-Type: application/json" -X POST -d '{"name":"TESTSVC","package_uri":"http://repo.cloud.hortonworks.com/amstore/testapp.tar.gz"}' http://localhost:5000/api/v1/applications
# curl -i -H "Content-Type: application/json" -X DELETE http://localhost:5000/api/v1/applications/2

@app.route('/api/v1/applications/<string:application_id>', methods=['DELETE'])

# Warning: we must also maintain the application cache.
def delete_application(application_id):
	application = [application for application in applications if application['id'] == application_id]
	if len(application) == 0:
		abort(404)
	# Delete all corresponding applications
	for appli in application:
		shutil.rmtree( app_get_application_dir(appli) )
		applications.remove(appli)
		applications_latest.remove(appli)
	return jsonify( {'result': True }) 
	
# Delete application. If version is empty we delete all versions (dangerous!)
# Also, TODO: change application cache behavior, it's too easy to forget about it
@app.route('/api/v1/delete_application', methods=['POST'])
def post_delete_application(  ):
	if not request.form['app_id'] :
        	abort(400)
	app_id = request.form['app_id']
	version = request.form['version']
	if not version:
		print 'Deleting all versions'
		application = [application for application in applications if application['app_id'] == app_id]
	else :
		 application = [application for application in applications if application['app_id'] == app_id and application['version'] == version ]


        if len(application) == 0:
                abort(404, "No matching applications found.")
	# Delete all
	for appli in application:
               	shutil.rmtree( app_get_application_dir(appli) )
               	applications.remove(appli)
		applications_latest.remove(appli)
		print 'Deleting folder ' +  app_get_application_dir(appli)
		print 'Removing app ' + appli['app_id']
	return  jsonify( {'result': True })		
	

@app.route('/api/v1/submit_application', methods=['GET'])
def app_submit_form():
	return '''
    <!doctype html>
    <title>Upload new Application</title>
    <h1>Upload new Application</h1>
    <form action="/api/v1/applications" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
'''


@app.route('/api/v1/submit_config', methods=['GET'])
def app_config_form():
        return '''
    <!doctype html>
    <title>Update package configuration</title>
    <h1>Update Application Configuration</h1>
    <form action="/api/v1/config" method=post enctype=multipart/form-data>
      <!--p>app_id: <input type=text name=app_id>        version: <input type=text name=version-->
      <p><input type=file name=file>
         <input type=submit value=Upload>
      <p>
    </form>
'''

@app.route('/api/v1/delete_application_form', methods=['GET'])
def app_delete_form():

        return '''
    <!doctype html>
    <title>Delete application</title>
    <h1>Delete application</h1>
    <form action="/api/v1/delete_application" method=post> 
      <p>app_id: <input type=text name=app_id>        version: <input type=text name=version>
      <p><input type=submit value=Delete>
      <p>
    </form>
'''
