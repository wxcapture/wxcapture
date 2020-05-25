# WxCapture
## Weather Satellite Capture Project
To see a preview of the site here, check out [https://wxcapture.github.io/wxcapture/server-website/wxcapture/index.html](https://wxcapture.github.io/wxcapture/server-website/wxcapture/index.html)
<!-- You can see our website (with all the data) at [INTRANET] -->

# What is WxCapture?
There are thousands of satellites currently in orbit, with many satellites passing in the sky overhead at any given moment.
You can receive some of them yourself with a cheap SDR and antenna, and with weather satellites, you can receive beautiful images of the Earth as seen from space taken by satellites in orbit, decoded in near real time.

# Installation
This is currently a manual process, with the instructions for installing the pi and server code currently being documented in the following spreadsheet:
https://github.com/wxcapture/wxcapture/blob/master/WxCapture.xlsx

In time an installer will be created...

# Webpage notes:
- ```index.html``` and ```satellites.html``` are static
- Predictions page (```satpass.html```) comes from ```schedule_passess.py```
- Captures page (```captures.html```) comes from ```move_modal.py```
- Status page (```satellitestatus.html```) comes from ```satellite_status.py```

# About this project 
This repository is a joint project between Mike (KiwiinNZ) and Albert (Technobird22). We are looking to turn this into an open source solution so that anyone can set up their own automatic decoding station. This site is currently under very active development, so you will often notice changes to it.

Please report any bugs to [wxcapture@gmail.com](mailto: wxcapture@gmail.com) or submit an issue on Github.
