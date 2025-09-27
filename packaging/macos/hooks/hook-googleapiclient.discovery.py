from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = copy_metadata('google-api-python-client')
datas += collect_data_files('googleapiclient', includes=['*.json', '*.pem'])
datas += copy_metadata('google-auth')
datas += copy_metadata('google-auth-oauthlib')
datas += copy_metadata('google-auth-httplib2')
datas += copy_metadata('httplib2')
datas += copy_metadata('pyparsing')
datas += copy_metadata('colorama')

