# Home Assistant support for Miele@home connected appliances

## Introduction

This project exposes Miele state information of appliances connected to a Miele user account. This is achieved by communicating with the Miele Cloud Service, which exposes both applicances connected to a Miele@home Gateway XGW3000, as well as those devices connected via WiFi Con@ct.

## Prerequisite

* A running version of [Home Assistant](https://home-assistant.io). While earlier versions may work, the custom component has been developed and tested with version 0.76.x.
* The ```requests_oauthlib``` library as part of your HA installation. Please install via ```pip3 install requests_oauthlib```.
  For Hassbian you need to install this via :
```
cd /srv/
sudo chown homeassistant:homeassistant homeassistant
sudo su -s /bin/bash homeassistant
cd /srv/homeassistant
source bin/activate
pip3 install requests_oauthlib
```

* Following the [instructions on the Miele developer site](https://www.miele.com/developer/getinvolved.html), you need to request your personal ```ClientID``` and ```ClientSecret```.

## Installation of the custom component

* Copy the content of this repository into your ```custom_components``` folder, which is a subdirectory of your Home Assistant configuration directory. By default, this directory is located under ```~/.home-assistant```. The structure of the ```custom_components``` directory should look like this afterwards:

```
- miele
    - __init__.py
    - miele_at_home.py
    - binary_sensor.py
    - light.py
    - sensor.py
```

* Enabled the new platform in your ```configuration.yaml```:

```
miele:
    client_id: <your Miele ClientID>
    client_secret: <your Miele ClientSecret>
    lang: <optional. en=english, de=german>
    cache_path: <optional. where to store the cached access token>
```

* Restart Home Assistant.
* The Home Assistant Web UI will show you a UI to configure the Miele platform. Follow the instructions to log into the Miele Cloud Service. This will communicate back an authentication token that will be cached to communicate with the Cloud Service.

Done. If you follow all the instructions, the Miele integration should be up and running. All Miele devices that you can see in your Mobile application should now be also visible in Home Assistant (miele.*). In addition, there will be a number of ```binary_sensors``` and ```sensors``` that can be used for automation.

## Questions

Please see the [Miele@home, miele@mobile component](https://community.home-assistant.io/t/miele-home-miele-mobile-component/64508) discussion thread on the Home Assistant community site.
