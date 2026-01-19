# TeraBox Backup for Home Assistant

This custom integration allows Home Assistant to use **TeraBox** as a remote storage
backend for **Home Assistant backups**.

The integration implements a Backup Agent and enables:
- uploading Home Assistant backups to TeraBox
- downloading backups from TeraBox
- managing backups through the Home Assistant UI

⚠️ This is an **unofficial integration** based on reverse-engineered TeraBox APIs.

---

## Features

- ☁️ Store Home Assistant backups in **TeraBox**
- 🔄 Upload and download backups

---

## Installation

### HACS (recommended)

1. Add this repository as a **custom repository** in HACS
2. Install **TeraBox Backup**
3. Restart Home Assistant

### Manual installation

1. Copy the `terabox` folder into: `config/custom_components/terabox`

2. Restart Home Assistant

---

## Configuration

The integration is configured via the Home Assistant UI.

You will need:
- **Email**
- **Password** 
- **Cookies and JSToken** (optional)

⚠️ Using **session cookies and jstoken** is highly recommended for avoiding captcha responses.

You will need to provide a folder in TeraBox where backups will be stored. 
The integration will create it if it does not exist on the first upload.

Once installed, go to `Settings → System → Backups → Backup settings/Settings and history` and select **TeraBox** as the storage location.

⚠️ It is recommended to use encryption for backups stored in TeraBox. It is usually turned on by default in Home Assistant.

---

### Getting the JS Token
To use this tool you need to have a Terabox account and a JS Token key. You can get the session JS Token by logging into your Terabox account and following the sequence of steps below:

1. Open your Terabox cloud.
2. Open the browser's developer tools (F12).<br/>
![Developer tools F12](images/devf12.png)
3. Enable the "Device Toolbar" then click the back arrow to get back to Terabox.<br/> 
![Developer tools F12 "Device Toolbar"](images/devf12devicetoolbar.png) 
![Back Arrow](images/backarrow.png)
4. Go to the "Network" tab.<br/>
![Developer tools F12 Network tab](images/devf12network.png)
5. Select the "XHR" filter.<br/>
![Developer tools F12 XHR filter](images/devf12fetch.png)
6. Click any directory or file in the cloud.
7. Look for any request made to the Terabox cloud URL and click on it.<br/>
![Developer tools F12 request item](images/devf12list.png)
8. Select the "Payload" tab.<br/>
![Developer tools F12 Payload tab](images/devf12payload.png)
9. Look for the jsToken parameter in the list and copy its value.

If you can't find the jsToken parameter, try selecting any other directory or file in the cloud and look for the jsToken parameter in the request payload. Make sure that you have the "XHR" filter selected and that you are looking at the "Payload" tab.


### Getting the cookies values
Additionally to the JS Token, you will need to capture the cookies values. You can get them by following the sequence of steps below:

1. Open your Terabox cloud.
2. Open the browser's developer tools (F12).<br/>
![Developer tools F12](images/devf12.png)
3. Go to the "Application" tab.<br/>
![Developer tools F12 Application tab](images/devf12apptab.png)
4. Select the "Cookies" item in the left panel.<br/>
![Developer tools F12 Cookies tab](images/devf12cookiestab.png)
5. Look for the cookies values and copy them.<br/>
![Developer tools F12 Cookies values](images/devf12cookieval.png)

You will need to copy the csrfToken, browserid, and ndus values.

---

## Requirements

- Home Assistant 2024.6+
- TeraBox account

---

## Known Issues

- Downloading large backups may take a long time depending on your internet connection and TeraBox server load.
- HTTPS wormholes to Home Assistant may drop connections after some MBs while downloading the backups in the browser, it is not related to this component. Use local network IP access to avoid this issue.

## Security Notes

- Credentials and cookies are stored in Home Assistant's config entries
- No encryption is applied by this integration (Home Assistant handles encryption separately)

---

## Disclaimer

This project is not affiliated with or endorsed by TeraBox.  
The API behavior may change at any time, which can break compatibility.

Use at your own risk.

---

## License

Apache License 2.0

See [LICENSE](LICENSE) for more information.
