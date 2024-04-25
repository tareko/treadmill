import gi
import argparse
import json
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

try:
    import serial
except ImportError:
    serial = None  # Handles cases where pySerial is not installed during development.

class TreadmillMonitorApp(Gtk.Window):
    def __init__(self, dev_mode=False):
        Gtk.Window.__init__(self, title="Treadmill")
        self.set_border_width(10)
        self.set_default_size(300, 250)  # Ensure there's enough space for the layout
        self.dev_mode = dev_mode

        # Main layout box
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.add(hbox)

        # Vertical box for labels, entry, and button
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hbox.pack_start(vbox, True, True, 0)  # Add vbox to hbox first for left side

        # Labels for data
        self.rpm_label = Gtk.Label(label="RPM: N/A")
        self.distance_label = Gtk.Label(label="Distance: N/A km")
        self.velocity_label = Gtk.Label(label="Velocity: N/A km/h")
        vbox.pack_start(self.rpm_label, True, True, 0)
        vbox.pack_start(self.distance_label, True, True, 0)
        vbox.pack_start(self.velocity_label, True, True, 0)

        # Label and Text entry for speed
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        speed_label = Gtk.Label(label="Speed:")
        self.speed_entry = Gtk.Entry()
        self.speed_entry.set_text("{:.1f}".format(0.0))  # Set to 0.0 initially
        self.speed_entry.connect("activate", self.on_speed_entry_activate)
        speed_box.pack_start(speed_label, False, False, 0)
        speed_box.pack_start(self.speed_entry, True, True, 0)
        vbox.pack_start(speed_box, False, False, 0)

        # Reset button
        self.reset_button = Gtk.Button(label="Reset distance")
        self.reset_button.connect("clicked", self.send_reset_command)
        vbox.pack_start(self.reset_button, False, False, 0)

        # Slider for speed
        self.speed_adjustment = Gtk.Adjustment(value=0.0, lower=0.0, upper=15.0, step_increment=0.1)
        self.speed_slider = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=self.speed_adjustment)
        self.speed_slider.set_digits(1)
        self.speed_slider.set_value_pos(Gtk.PositionType.BOTTOM)  # Position the value label at the bottom
        self.speed_slider.set_inverted(True)  # Invert the slider so zero is at the bottom and max is at the top
        self.speed_slider.connect("value-changed", self.on_speed_changed)
        hbox.pack_end(self.speed_slider, False, False, 0)  # Pack the slider at the end for the right side

        # Serial port setup if not in developer mode
        if not self.dev_mode and serial is not None:
            self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        
        # GLib timeout to read data every 1000 milliseconds (1 second)
        GLib.timeout_add(1000, self.read_serial_data)

    def send_json_speed(self, speed):
        data = json.dumps({"velocity": speed})
        if self.dev_mode:
            print(f"Sending JSON packet in dev mode: {data}")
        else:
            self.ser.write(data.encode('utf-8') + b'\n')

    def on_speed_changed(self, scale):
        speed = self.speed_adjustment.get_value()
        self.speed_entry.set_text("{:.1f}".format(speed))
        self.send_json_speed(speed)

    def on_speed_entry_activate(self, entry):
        text = entry.get_text()
        try:
            speed = float(text)
            if 0.0 <= speed <= 15.0:
                self.speed_adjustment.set_value(speed)
                self.send_json_speed(speed)
        except ValueError:
            pass  # Ignore invalid input

    def send_reset_command(self, button):
        if self.dev_mode:
            print("Sending reset command in dev mode.")
        else:
            self.ser.write(b'reset\n')

    def read_serial_data(self):
        if not self.dev_mode and self.ser is not None and self.ser.in_waiting > 0:
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
    parser = argparse.ArgumentParser(description="Treadmill Monitor App")
    parser.add_argument('--dev-mode', action='store_true', help='Run the application in developer mode without serial device')
    args = parser.parse_args()

    app = TreadmillMonitorApp(dev_mode=args.dev_mode)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()

