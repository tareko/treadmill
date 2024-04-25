import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

import serial
import json

class TreadmillMonitorApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Treadmill")
        self.set_border_width(10)
        self.set_default_size(200, 100)

        # Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(vbox)

        # Labels for data
        self.rpm_label = Gtk.Label(label="RPM: N/A")
        self.distance_label = Gtk.Label(label="Distance: N/A km")  # Added units here
        self.velocity_label = Gtk.Label(label="Velocity: N/A km/h")  # Added units here
        vbox.pack_start(self.rpm_label, True, True, 0)
        vbox.pack_start(self.distance_label, True, True, 0)
        vbox.pack_start(self.velocity_label, True, True, 0)

        # Serial port setup
        self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        
        # GLib timeout to read data every 1000 milliseconds (1 second)
        GLib.timeout_add(1000, self.read_serial_data)

    def read_serial_data(self):
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8').strip()
            try:
                data = json.loads(line)
                self.rpm_label.set_text(f"RPM: {data.get('rpm', 'N/A')}")
                self.distance_label.set_text(f"Distance: {data.get('distance', 'N/A')} km")
                self.velocity_label.set_text(f"Velocity: {data.get('velocity', 'N/A')} km/h")
            except json.JSONDecodeError:
                print("Error decoding JSON")
        return True  # Continue calling this function

def main():
    app = TreadmillMonitorApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
