#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
import threading
import time
from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio import fec
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import soapy
from gnuradio.qtgui import Range, RangeWidget
from PyQt5 import QtCore
import sip

def convert_tmp_to_original(tmp_file, name_start_key, output_file, header_end_marker, footer_start_marker):
    """
    Converts a .tmp file back to its original format by removing the header and footer strings
    and renaming it with the provided extension.

    Args:
        tmp_file (str): Path to the .tmp file.
        name_start_key (str): Key to find the original filename.
        output_file (str): Path to save the restored file.
        header_end_marker (str): Unique string at the end of the header.
        footer_start_marker (str): Unique string at the start of the footer.

    Returns:
        str: Path to the restored original file or None if conversion fails.
    """
    try:
        if not os.path.isfile(tmp_file):
            raise FileNotFoundError(f"Temporary file '{tmp_file}' does not exist.")

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Read the content of the .tmp file
        with open(tmp_file, 'rb') as infile:
            content = infile.read()

        # Find the header end marker and remove the header
        header_end_marker_bytes = header_end_marker.encode('utf-8')
        header_end_index = content.find(header_end_marker_bytes) + len(header_end_marker_bytes)
        if header_end_index <= 0:
            raise ValueError("Header end marker not found in the file.")
        
        # Find file name 
        file_name_start_index = content.find(name_start_key.encode('utf-8')) + len(name_start_key.encode('utf-8'))
        file_name = (content[file_name_start_index + 1:(content.find(header_end_marker_bytes))]).decode('utf-8')

        # Extract the content after the header
        content_without_header = content[header_end_index:].lstrip(b"\n")

        # Find the footer start marker and remove the footer
        footer_start_marker_bytes = footer_start_marker.encode('utf-8')
        footer_start_index = content_without_header.find(footer_start_marker_bytes)
        if footer_start_index > 0:
            content_without_footer = content_without_header[:footer_start_index].rstrip(b"\n")
        else:
            content_without_footer = content_without_header

        # Write the content to the new file
        output_file = output_file + file_name

        with open(output_file, 'wb') as outfile:
            outfile.write(content_without_footer)

        try:
            open(tmp_file , 'w').close()
            print(f"Temporary file {tmp_file} deleted successfully")
        except Exception as delete_error:
            print(f"Error deleting temporary file {tmp_file}: {delete_error}")

        print("Received SUCCESSFULLY")

        return output_file

    except Exception as e:
        print(f"Conversion error: {e}")
        return None

class FileWatcher(threading.Thread):
    def __init__(self, tmp_file, name_start_key, output_file_path, header_end_marker, footer_start_marker):
        """
        Monitors a temporary file for footer and converts it to original format
        
        Args:
            tmp_file (str): Path to the temporary file to watch
            name_start_key (str): Key to find the original filename
            output_file_path (str): Directory to save converted files
            header_end_marker (str): Marker indicating end of header
            footer_start_marker (str): Marker indicating start of footer
        """
        threading.Thread.__init__(self)
        self.tmp_file = tmp_file
        self.name_start_key = name_start_key
        self.output_file_path = output_file_path
        self.header_end_marker = header_end_marker
        self.footer_start_marker = footer_start_marker
        self.daemon = True  # Allow thread to exit when main program exits
        self._stop_event = threading.Event()

    def stop(self):
        """Signal the thread to stop"""
        self._stop_event.set()

    def stopped(self):
        """Check if thread has been signaled to stop"""
        return self._stop_event.is_set()

    def run(self):
        """
        Continuously monitor the temporary file for footer and trigger conversion
        """
        last_size = 0
        while not self.stopped():
            try:
                # Only check file if it exists and has changed
                if os.path.exists(self.tmp_file):
                    current_size = os.path.getsize(self.tmp_file)
                    
                    # Read file content if size has changed
                    if current_size != last_size:
                        with open(self.tmp_file, 'rb') as f:
                            content = f.read()
                        
                        # Check for footer marker
                        if self.footer_start_marker.encode('utf-8') in content:
                            print("Footer detected. Converting file...")
                            result = convert_tmp_to_original(
                                self.tmp_file, 
                                self.name_start_key, 
                                self.output_file_path, 
                                self.header_end_marker, 
                                self.footer_start_marker
                            )
                            

                            if result:
                                print(f"File successfully restored to: {result}")
                                # Do not break, continue monitoring
                    
                    last_size = current_size
                
                time.sleep(1)  # Check every second
            
            except Exception as e:
                print(f"File watcher error: {e}")
                # Do not exit on exception, continue monitoring

class rx(gr.top_block, Qt.QWidget):

    def __init__(self, MTU=1500):
        gr.top_block.__init__(self, "MediaReceiver", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        
        # Initialize file watcher thread
        self.file_watcher = FileWatcher(
            tmp_file="/home/gnuradio/temp files/output.tmp", 
            name_start_key="namestart",
            output_file_path="/home/gnuradio/ReceivedFiles/", 
            header_end_marker="information", 
            footer_start_marker="footerstarts"
        )
        
        # Start file watcher thread
        self.file_watcher.start()

        # Rest of the initialization remains the same as in the original script
        self.setWindowTitle("MediaReceiver")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "rx")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Parameters
        ##################################################
        self.MTU = MTU

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.qpsk = qpsk = digital.constellation_rect([0.707+0.707j, -0.707+0.707j, -0.707-0.707j, 0.707-0.707j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.polys = polys = [109, 79]
        self.nfilts = nfilts = 32
        self.k = k = 7
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0 = digital.adaptive_algorithm_cma( qpsk, .0001, 4).base()
        self.samp_rate = samp_rate = 1000000
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts, 1.0/float(sps), 0.35, 11*sps*nfilts)
        self.phase_bw = phase_bw = 6.28/100.0
        self.cc_dec = cc_dec = list(map( (lambda a: fec.cc_decoder.make((MTU*8),k, 2, polys, 0, (-1), fec.CC_TAILBITING, False)),range(0,1)))

        ##################################################
        # Blocks
        ##################################################

        self._phase_bw_range = Range(0.0, 1.0, 0.01, 6.28/100.0, 200)
        self._phase_bw_win = RangeWidget(self._phase_bw_range, self.set_phase_bw, "Phase: Bandwidth", "slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._phase_bw_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.soapy_bladerf_source_0 = None
        dev = 'driver=bladerf'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_bladerf_source_0 = soapy.source(dev, "fc32", 1, 'bladerf=0',
                                  stream_args, tune_args, settings)
        self.soapy_bladerf_source_0.set_sample_rate(0, samp_rate)
        self.soapy_bladerf_source_0.set_bandwidth(0, 10000)
        self.soapy_bladerf_source_0.set_frequency(0, 2.4e9)
        self.soapy_bladerf_source_0.set_frequency_correction(0, 0)
        self.soapy_bladerf_source_0.set_gain(0, min(max(10.0, -1.0), 60.0))
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            1024, #size
            samp_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['TX signal', 'RX signal', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_const_sink_x_1 = qtgui.const_sink_c(
            1024, #size
            "RX signal", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_1.set_update_time(0.10)
        self.qtgui_const_sink_x_1.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_1.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_1.enable_autoscale(True)
        self.qtgui_const_sink_x_1.enable_grid(False)
        self.qtgui_const_sink_x_1.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_1_win = sip.wrapinstance(self.qtgui_const_sink_x_1.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_const_sink_x_1_win, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.fec_extended_tagged_decoder_2 = self.fec_extended_tagged_decoder_2 = fec_extended_tagged_decoder_2 = fec.extended_tagged_decoder(decoder_obj_list=cc_dec, ann=None, puncpat='11', integration_period=10000, lentagname="packet_len", mtu=MTU)
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps,
            (62.8e-3),
            1.4,
            1.0,
            1.5,
            4,
            digital.constellation_bpsk().base(),
            digital.IR_PFB_MF,
            32,
            rrc_taps)
        self.digital_map_bb_0_0 = digital.map_bb([-1, 1])
        self.digital_map_bb_0 = digital.map_bb([0,1,2,3])
        self.digital_linear_equalizer_0 = digital.linear_equalizer(15, 4, variable_adaptive_algorithm_0, True, [ ], 'corr_est')
        self.digital_diff_decoder_bb_0 = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(phase_bw, 4, False)
        self.digital_correlate_access_code_xx_ts_0 = digital.correlate_access_code_bb_ts('00011010110011111111110000011101',
          2, 'packet_len')
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(qpsk)
        self.blocks_unpack_k_bits_bb_0_0 = blocks.unpack_k_bits_bb(2)
        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(1, 8, "", False, gr.GR_MSB_FIRST)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, '/home/gnuradio/temp files/output.tmp', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_char_to_float_2_0 = blocks.char_to_float(1, 1)
        self.blocks_char_to_float_1_1 = blocks.char_to_float(1, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_char_to_float_1_1, 0), (self.fec_extended_tagged_decoder_2, 0))
        self.connect((self.blocks_char_to_float_2_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.blocks_char_to_float_2_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0_0, 0), (self.digital_correlate_access_code_xx_ts_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.digital_diff_decoder_bb_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0, 0), (self.digital_map_bb_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_decoder_cb_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_x_1, 0))
        self.connect((self.digital_diff_decoder_bb_0, 0), (self.digital_map_bb_0, 0))
        self.connect((self.digital_linear_equalizer_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_map_bb_0, 0), (self.blocks_unpack_k_bits_bb_0_0, 0))
        self.connect((self.digital_map_bb_0_0, 0), (self.blocks_char_to_float_1_1, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_linear_equalizer_0, 0))
        self.connect((self.fec_extended_tagged_decoder_2, 0), (self.blocks_repack_bits_bb_0, 0))
        self.connect((self.soapy_bladerf_source_0, 0), (self.digital_symbol_sync_xx_0, 0))

        # ... [rest of the original __init__ method remains unchanged]

    def closeEvent(self, event):
        # Stop the file watcher thread when closing
        self.file_watcher.stop()
        
        self.settings = Qt.QSettings("GNU Radio", "rx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()
    def get_MTU(self):
        return self.MTU

    def set_MTU(self, MTU):
        self.MTU = MTU

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk
        self.digital_constellation_decoder_cb_0.set_constellation(self.qpsk)

    def get_polys(self):
        return self.polys

    def set_polys(self, polys):
        self.polys = polys

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))

    def get_k(self):
        return self.k

    def set_k(self, k):
        self.k = k

    def get_variable_adaptive_algorithm_0(self):
        return self.variable_adaptive_algorithm_0

    def set_variable_adaptive_algorithm_0(self, variable_adaptive_algorithm_0):
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.soapy_bladerf_source_0.set_sample_rate(0, self.samp_rate)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_phase_bw(self):
        return self.phase_bw

    def set_phase_bw(self, phase_bw):
        self.phase_bw = phase_bw
        self.digital_costas_loop_cc_0.set_loop_bandwidth(self.phase_bw)

    def get_cc_dec(self):
        return self.cc_dec

    def set_cc_dec(self, cc_dec):
        self.cc_dec = cc_dec



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--MTU", dest="MTU", type=intx, default=1500,
        help="Set MTU [default=%(default)r]")
    return parser

def main(top_block_cls=rx, options=None):
    if options is None:
        options = argument_parser().parse_args()

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(MTU=options.MTU)

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
    