# BladeRF Tranciever
This project is a **point-to-point communication system** implemented using **GNU Radio**, **BladeRF SDR**, and **Python** (for the GUI). It enables the transmission and reception of any type of file between two or more SDRs, with a maximum range of approximately **20 meters**. The system was implemented in WIFI frequency range (2.4 GHz).

### Key Features:
- **File Transmission**: Capable of transmitting and receiving any file type (e.g., images, audio, video, text).
- **Continuous Reception**: Supports continuous reception of multiple files without interruptions.
- **Modulation Techniques**: Utilizes **QPSK** and **FM** modulation for efficient signal transmission.
- **Error Correction**: Implements **convolutional coding** for robust error correction during transmission.

This project demonstrates how software-defined radios (SDRs) can be effectively used in modern communication systems for reliable file transfer across moderate distances.


<h3>GUI</h3>
<p>File Transmitter interface</p>
<img src="GUIImages\transmit.png" alt="System Diagram" width="500">

<p>File Receiver interface</p>
<img src="GUIImages\receive.png" alt="System Diagram" width="500">

<p>Livestream interface</p>
<img src="GUIImages\liveaudio.png" alt="System Diagram" width="500">

<h3>Analysis</h3>
<img src="BER\berVsDistance.png" alt="System Diagram" width="500">

![GNU Radio](https://img.shields.io/badge/GNU%20Radio-blue)
![BladeRF](https://img.shields.io/badge/BladeRF-green)
![Python](https://img.shields.io/badge/Python-yellow)
![Signal Processing](https://img.shields.io/badge/Signal%20Processing-red)
