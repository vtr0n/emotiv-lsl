import hid
from Crypto.Cipher import AES
from pylsl import StreamInfo

from emotiv_lsl.emotiv_base import EmotivBase
from config import SRATE


class EmotivEpocX(EmotivBase):
    READ_SIZE = 32

    def __init__(self) -> None:
        self.delimiter = ','

        self.cipher = AES.new(self.get_crypto_key(), AES.MODE_ECB)

    def get_hid_device(self):
        for device in hid.enumerate():
            if device['manufacturer_string'] == 'Emotiv' and device['usage'] == 2:
                return device

        raise Exception('Emotiv Epoc X not found')

    def get_crypto_key(self) -> bytearray:
        serial = self.get_hid_device()['serial_number']
        sn = bytearray()
        for i in range(0, len(serial)):
            sn += bytearray([ord(serial[i])])

        return bytearray([sn[-1], sn[-2], sn[-4], sn[-4], sn[-2], sn[-1], sn[-2], sn[-4], sn[-1], sn[-4], sn[-3], sn[-2], sn[-1], sn[-2], sn[-2], sn[-3]])

    def get_stream_info(self) -> StreamInfo:
        ch_names = ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7',
                    'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
        n_channels = len(ch_names)

        info = StreamInfo('Epoc X', 'EEG', n_channels, SRATE, 'float32')
        chns = info.desc().append_child("channels")
        for label in ch_names:
            ch = chns.append_child("channel")
            ch.append_child_value("label", label)
            ch.append_child_value("unit", "microvolts")
            ch.append_child_value("type", "EEG")
            ch.append_child_value("scaling_factor", "1")

        cap = info.desc().append_child("cap")
        cap.append_child_value("name", "easycap-M1")
        cap.append_child_value("labelscheme", "10-20")

        return info

    def decode_data(self, data) -> list:
        data = [el ^ 0x55 for el in data]
        data = self.cipher.decrypt(bytearray(data))

        packet_data = ""
        for i in range(2, 16, 2):
            packet_data = packet_data + \
                str(self.convertEPOC_PLUS(
                    str(data[i]), str(data[i+1]))) + self.delimiter

        for i in range(18, len(data), 2):
            packet_data = packet_data + \
                str(self.convertEPOC_PLUS(
                    str(data[i]), str(data[i+1]))) + self.delimiter

        packet_data = packet_data[:-len(self.delimiter)]
        packet_data = packet_data.split(self.delimiter)
        packet_data = [float(i) for i in packet_data]

        # swap positions of AF3 and F3
        packet_data[0], packet_data[2] = packet_data[2], packet_data[0]

        # swap positions of AF4 and F4
        packet_data[13], packet_data[11] = packet_data[11], packet_data[13]

        # swap positions of F7 and FC5
        packet_data[1], packet_data[3] = packet_data[3], packet_data[1]

        # swap positions of FC6 and F8
        packet_data[10], packet_data[12] = packet_data[12], packet_data[10]

        # ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
        return packet_data

    def convertEPOC_PLUS(self, value_1, value_2):
        edk_value = "%.8f" % (((int(value_1) * .128205128205129) +
                              4201.02564096001) + ((int(value_2) - 128) * 32.82051289))
        return edk_value

    def validate_data(self, data) -> bool:
        return len(data) == 32
