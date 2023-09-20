import hid
from pylsl import StreamInfo, StreamOutlet


class EmotivBase():
    READ_SIZE = 32

    def get_hid_device(self):
        pass

    def get_stream_info(self) -> StreamInfo:
        pass

    def decode_data(self) -> list:
        pass

    def validate_data(self, data) -> bool:
        pass

    def main_loop(self):
        outlet = StreamOutlet(self.get_stream_info())

        device = self.get_hid_device()
        hid_device = hid.device()
        hid_device.open_path(device['path'])

        while True:
            data = hid_device.read(self.READ_SIZE)
            if self.validate_data(data):
                decoded = self.decode_data(data)
                outlet.push_sample(decoded)
