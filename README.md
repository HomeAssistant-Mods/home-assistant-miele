<a href="https://www.buymeacoffee.com/robink" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

<a href="https://paypal.me/robinkolk"><img src="https://www.paypalobjects.com/en_US/NL/i/btn/btn_donateCC_LG.gif" title="PayPal - The safer, easier way to pay online!" alt="Donate with PayPal button"></a>

# Home Assistant support for Miele@home connected appliances

## Introduction

This project exposes Miele state information of appliances connected to a Miele user account. This is achieved by communicating with the Miele Cloud Service, which exposes both applicances connected to a Miele@home Gateway XGW3000, as well as those devices connected via WiFi Con@ct.

## Prerequisite

* A running version of [Home Assistant](https://home-assistant.io). This custom component has been developed and tested with version 2024.02.0

* Following the [instructions on the Miele developer site](https://www.miele.com/f/com/en/register_api.aspx), you need to request your personal ```ClientID``` and ```ClientSecret```.

## HACS Install
We are now included in the default Repo of HACS. This is the recomanded way to install this integration.

* Install HACS if you haven't yet, instructions to install HACS can be found here : https://hacs.xyz/docs/installation/prerequisites

* Open the HACS component from your sidebar -> click integrations -> Search for Miele and install the Integration.

* Restart Home Assistant.

* To enable the new integration go to Settings -> Devices and click Add Integration, search for Miele and follow the instructions

* The Miele Integration configuration flow will show, enter the Name/ Client ID and Client Secret then follow the link to sign-in o the miele developer site (this probably will open automatically).  After logging in you should be re-directed back to home assistant and the integration is configured.

* The Default refresh is 5 seconds and the default language comes from your Home Assistant setup, this can be changed by clicking on the Miele Integration and selecting configure.

Done. If you follow all the instructions, the Miele integration should be up and running. All Miele devices that you can see in your Mobile application should now be also visible in Home Assistant (miele.*). In addition, there will be a number of ```binary_sensors``` and ```sensors``` that can be used for automation.


## Migration from YAML
YAML has been deprecated, after this update the YAML configuration settings will be copied and the Miele Device discovered in the settings -> devices.

* Go to Settings -> Devices  and click on the configure button in the Miele Device.

* You should be promped to re-login to the Miele Developer site, if not follow the link, once logged in you will be returned to home assistant and the integration setup in the UI.

* After setup remove the Miele settings from the configuration.yaml and restart.

After migration all sensors and services should work as before.


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

* Restart Home Assistant.

* To enable the new integration go to Settings -> Devices and click Add Integration, search for Miele and follow the instructions

* The Miele Integration configuration flow will show, enter the Name/ Client ID and Client Secret then follow the link to sign-in o the miele developer site (this probably will open automatically).  After logging in you should be re-directed back to home assistant and the integration is configured.

* The Default refresh is 5 seconds and the default language comes from your Home Assistant setup, this can be changed by clicking on the Miele Integration and selecting configure.

Done. If you follow all the instructions, the Miele integration should be up and running. All Miele devices that you can see in your Mobile application should now be also visible in Home Assistant (miele.*). In addition, there will be a number of ```binary_sensors``` and ```sensors``` that can be used for automation.

## Questions

Please see the [Miele@home, miele@mobile component](https://community.home-assistant.io/t/miele-home-miele-mobile-component/64508) discussion thread on the Home Assistant community site.
