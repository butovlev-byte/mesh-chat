[app]
title = MeshChat
package.name = meshchat
package.domain = org.meshchat
source.dir = src/
source.include_exts = py,png,jpg,kv,atlas,pem,db
version = 1.0.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pycryptodome==3.19.0,plyer==2.1.0,ifaddr==0.2.0
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,BLUETOOTH_ADVERTISE,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
android.gradle_dependencies = com.android.support:support-compat:28.0.0
p4a.local_recipes = 
icon.filename = %(source.dir)s/../assets/icon.png
presplash.filename = %(source.dir)s/../assets/splash.png
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
author = MeshChat Team
[buildozer]
log_level = 2
warn_on_root = 1
