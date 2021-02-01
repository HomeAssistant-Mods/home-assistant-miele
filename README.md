<a href="https://www.buymeacoffee.com/robink" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

# Home Assistant support for Miele@home connected appliances

## Introduction

This project exposes Miele state information of appliances connected to a Miele user account. This is achieved by communicating with the Miele Cloud Service, which exposes both applicances connected to a Miele@home Gateway XGW3000, as well as those devices connected via WiFi Con@ct.

## Prerequisite

* A running version of [Home Assistant](https://home-assistant.io). While earlier versions may work, the custom component has been developed and tested with version 0.76.x.

* Following the [instructions on the Miele developer site](https://www.miele.com/f/com/en/register_api.aspx), you need to request your personal ```ClientID``` and ```ClientSecret```.

## HACS Install
We are now included in the default Repo of HACS. This is the recomanded way to install this integration. 

* Install HACS if you haven't yet, instructions to install HACS can be found here : https://hacs.xyz/docs/installation/prerequisites

* Open the HACS component from your sidebar -> click integrations -> Search for Miele and install the Integration.

* Enable the new platform in your ```configuration.yaml```:

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

## Manual Installation of the custom component

* Copy the content of this repository into your ```custom_components``` folder, which is a subdirectory of your Home Assistant configuration directory. By default, this directory is located under ```~/.home-assistant```. The structure of the ```custom_components``` directory should look like this afterwards:

```
- miele
    - __init__.py
    - miele_at_home.py
    - binary_sensor.py
    - light.py
    - sensor.py
```

* Enable the new platform in your ```configuration.yaml```:

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
