import pyshark
from Crypto.Cipher import AES
from pylsl import StreamOutlet

from emotiv_lsl.emotiv_epoc_x import EmotivEpocX


class EmotivEpocXPyShark(EmotivEpocX):

    def __init__(self) -> None:
        self.delimiter = ','

        self.cipher = AES.new(self.get_crypto_key(), AES.MODE_ECB)
        self.capture = pyshark.LiveCapture(
            interface='XHC20', bpf_filter='len == 72')
        print(self.capture)

    def validate_data(self, data) -> bool:
        return len(data) == 64

    def main_loop(self):
        outlet = StreamOutlet(self.get_stream_info())
        for packet in self.capture.sniff_continuously():
            if packet.usb.dst != 'host':
                continue

            data = str(packet.layers[1].get_field('usb.capdata'))
            data = data.replace(':', '')

            if self.validate_data(data):
                data = bytearray.fromhex(data)
                decoded = self.decode_data(data)
                outlet.push_sample(decoded)
