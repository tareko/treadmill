#!/usr/bin/env python3
import argparse
import json
import sys

try:
    import serial
except ImportError:
    serial = None  # Handles cases where pySerial is not installed during development.

VELOCITY_FILE = '/tmp/treadmill_velocity'
DISTANCE_FILE = '/tmp/treadmill_distance'


class TreadmillMonitorApp:
    """Cross-platform treadmill monitor: GTK3 when available, tkinter fallback."""

    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode
        self._use_gtk = self._try_import_gtk()

        if self._use_gtk:
            self._build_gtk()
        else:
            self._build_tk()

    # ------------------------------------------------------------------
    # GTK3 backend
    # ------------------------------------------------------------------
    def _try_import_gtk(self):
        try:
            import gi  # noqa: F401
            gi.require_version('Gtk', '3.0')
            from gi.repository import GLib, Gtk  # noqa: F401
            return True
        except (ImportError, AttributeError):
            return False

    def _build_gtk(self):
        from gi.repository import GLib, Gtk

        self.window = Gtk.Window()
        self.window.set_title("Treadmill")
        self.window.set_border_width(10)
        self.window.set_default_size(300, 300)
        self.window.connect("destroy", Gtk.main_quit)

        # Main layout box
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.window.add(hbox)

        # Box for incline controls, expanded vertically
        incline_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hbox.pack_start(incline_box, False, True, 0)

        # Button for increasing incline
        up_button = Gtk.Button(label="↑")
        up_button.connect("clicked", self.send_incline_command, "up")
        incline_box.pack_start(up_button, True, True, 0)

        # Incline label
        incline_label = Gtk.Label(label="Incline")
        incline_box.pack_start(incline_label, True, True, 0)

        # Button for decreasing incline
        down_button = Gtk.Button(label="↓")
        down_button.connect("clicked", self.send_incline_command, "down")
        incline_box.pack_start(down_button, True, True, 0)

        # Vertical box for other controls
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hbox.pack_start(vbox, True, True, 0)

        # Labels for data
        self.rpm_label = Gtk.Label(label="RPM: N/A")
        self.distance_label = Gtk.Label(label="Distance: N/A km")
        self.velocity_label = Gtk.Label(label="Velocity: N/A km/h")
        vbox.pack_start(self.rpm_label, True, True, 0)
        vbox.pack_start(self.distance_label, True, True, 0)
        vbox.pack_start(self.velocity_label, True, True, 0)

        # Speed control entry
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        speed_label = Gtk.Label(label="Speed:")
        self.speed_entry = Gtk.Entry()
        self.speed_entry.set_text("{:.1f}".format(0.0))
        self.speed_entry.connect("activate", self.on_speed_entry_activate)
        speed_box.pack_start(speed_label, False, False, 0)
        speed_box.pack_start(self.speed_entry, True, True, 0)
        vbox.pack_start(speed_box, False, False, 0)

        # Reset button
        self.reset_button = Gtk.Button(label="Reset distance")
        self.reset_button.connect("clicked", self.send_reset_command)
        vbox.pack_start(self.reset_button, False, False, 0)

        # Slider for speed
        self.speed_adjustment = Gtk.Adjustment(
            value=0.0, lower=0.0, upper=15.0, step_increment=0.1
        )
        self.speed_slider = Gtk.Scale(
            orientation=Gtk.Orientation.VERTICAL,
            adjustment=self.speed_adjustment,
        )
        self.speed_slider.set_digits(1)
        self.speed_slider.set_value_pos(Gtk.PositionType.BOTTOM)
        self.speed_slider.set_inverted(True)
        self.speed_slider.connect("value-changed", self.on_speed_changed)
        hbox.pack_end(self.speed_slider, False, False, 0)

        # Serial port setup if not in developer mode
        if not self.dev_mode and serial is not None:
            self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

        # GLib timeout to read data
        GLib.timeout_add(1000, self._read_serial_data_gtk)
        self.window.show_all()

    def _read_serial_data_gtk(self):
        if not self.dev_mode and serial is not None and hasattr(self, 'ser') and self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8').strip()
            try:
                data = json.loads(line)
                self.rpm_label.set_text(f"RPM: {data.get('rpm', 'N/A')}")
                self.distance_label.set_text(f"Distance: {data.get('distance', 'N/A')} km")
                self.velocity_label.set_text(f"Velocity: {data.get('velocity', 'N/A')} km/h")
                if 'velocity' in data:
                    self._write_velocity(data['velocity'])
                if 'distance' in data:
                    self._write_distance(data['distance'])
            except json.JSONDecodeError:
                print("Error decoding JSON")
        return True  # Continue calling this function

    # ------------------------------------------------------------------
    # Tkinter fallback backend
    # ------------------------------------------------------------------
    def _build_tk(self):
        import tkinter as tk
        self._tk = tk
        from tkinter import ttk

        self.root = tk.Tk()
        self.root.title("Treadmill")
        self.root.geometry("300x300")
        self.root.resizable(True, True)

        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left column: incline controls
        incline_frame = ttk.Frame(main_frame)
        incline_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        up_button = ttk.Button(incline_frame, text="↑", command=lambda: self.send_incline_command(None, "up"))
        up_button.pack(fill=tk.X, pady=2)

        incline_label = ttk.Label(incline_frame, text="Incline")
        incline_label.pack(fill=tk.X, pady=2)

        down_button = ttk.Button(incline_frame, text="↓", command=lambda: self.send_incline_command(None, "down"))
        down_button.pack(fill=tk.X, pady=2)

        # Middle column: data and controls
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Data labels
        self.rpm_var = tk.StringVar(value="RPM: N/A")
        self.distance_var = tk.StringVar(value="Distance: N/A km")
        self.velocity_var = tk.StringVar(value="Velocity: N/A km/h")

        ttk.Label(middle_frame, textvariable=self.rpm_var).pack(fill=tk.X, pady=2)
        ttk.Label(middle_frame, textvariable=self.distance_var).pack(fill=tk.X, pady=2)
        ttk.Label(middle_frame, textvariable=self.velocity_var).pack(fill=tk.X, pady=2)

        # Speed entry
        speed_frame = ttk.Frame(middle_frame)
        speed_frame.pack(fill=tk.X, pady=4)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_entry = ttk.Entry(speed_frame)
        self.speed_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self.speed_entry.insert(0, "0.0")
        self.speed_entry.bind("<Return>", self.on_speed_entry_activate)

        # Reset button
        ttk.Button(
            middle_frame, text="Reset distance", command=self.send_reset_command
        ).pack(pady=(8, 0))

        # Right column: speed slider
        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))

        self.speed_var = tk.DoubleVar(value=0.0)
        self.speed_slider = ttk.Scale(
            slider_frame,
            from_=15.0, to=0.0,
            orient=tk.VERTICAL,
            variable=self.speed_var,
            command=self.on_speed_changed,
        )
        self.speed_slider.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

        # Serial port setup if not in developer mode
        if not self.dev_mode and serial is not None:
            self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            # Schedule serial polling
            self._poll_serial_tk()

    def _poll_serial_tk(self):
        """Poll serial data for the tkinter backend."""
        if not self.dev_mode and serial is not None and hasattr(self, 'ser') and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                data = json.loads(line)
                self.rpm_var.set(f"RPM: {data.get('rpm', 'N/A')}")
                self.distance_var.set(f"Distance: {data.get('distance', 'N/A')} km")
                self.velocity_var.set(f"Velocity: {data.get('velocity', 'N/A')} km/h")
                if 'velocity' in data:
                    self._write_velocity(data['velocity'])
                if 'distance' in data:
                    self._write_distance(data['distance'])
            except json.JSONDecodeError:
                print("Error decoding JSON")
            except Exception as exc:
                print(f"Serial read error: {exc}")
        self.root.after(1000, self._poll_serial_tk)

    # ------------------------------------------------------------------
    # UI event handlers
    # ------------------------------------------------------------------
    def on_speed_changed(self, value):
        speed = float(value) if not self._use_gtk else self._get_speed()
        self._update_speed_ui(speed)
        self.send_json_speed(speed)

    def on_speed_entry_activate(self, event):
        # For GTK: event is the widget; for Tk: event is the Tkinter Event
        if self._use_gtk:
            entry = event
        else:
            entry = event.widget

        text = entry.get()
        try:
            speed = float(text)
            if 0.0 <= speed <= 15.0:
                self._set_speed(speed)
                self.send_json_speed(speed)
        except ValueError:
            pass  # Ignore invalid input

    # ------------------------------------------------------------------
    # Common logic
    # ------------------------------------------------------------------
    def _write_velocity(self, velocity):
        try:
            with open(VELOCITY_FILE, 'w') as f:
                f.write(f"{velocity:.2f}")
        except OSError:
            pass

    def _write_distance(self, distance):
        try:
            with open(DISTANCE_FILE, 'w') as f:
                f.write(f"{distance:.2f}")
        except OSError:
            pass

    def _get_speed(self):
        if self._use_gtk:
            return self.speed_adjustment.get_value()
        return self.speed_var.get()

    def _set_speed(self, speed):
        if self._use_gtk:
            self.speed_adjustment.set_value(speed)
            self.speed_entry.set_text("{:.1f}".format(speed))
        else:
            self.speed_var.set(speed)
            self.speed_entry.delete(0, self._tk.END)
            self.speed_entry.insert(0, "{:.1f}".format(speed))

    def _update_speed_ui(self, speed):
        if self._use_gtk:
            self.speed_entry.set_text("{:.1f}".format(speed))
        else:
            self.speed_entry.delete(0, self._tk.END)
            self.speed_entry.insert(0, "{:.1f}".format(speed))

    def send_json_packet(self, data):
        if self.dev_mode:
            print(f"Sending JSON packet in dev mode: {data}")
        else:
            self.ser.write(data.encode('utf-8') + b'\n')

    def send_json_speed(self, speed):
        data = json.dumps({"velocity": speed})
        if self.dev_mode:
            print(f"Sending JSON speed packet in dev mode: {data}")
        else:
            self.ser.write(data.encode('utf-8') + b'\n')

    def send_incline_command(self, button, direction):
        data = json.dumps({"incline": direction})
        self.send_json_packet(data)

    def send_reset_command(self, button=None):
        if self.dev_mode:
            print("Sending reset command in dev mode.")
        else:
            self.ser.write(b'reset\n')

    # ------------------------------------------------------------------
    # Cross-platform run loop
    # ------------------------------------------------------------------
    def run(self):
        if self._use_gtk:
            from gi.repository import Gtk
            Gtk.main()
        else:
            self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Treadmill Monitor App")
    parser.add_argument(
        '--dev-mode', action='store_true',
        help='Run the application in developer mode without serial device',
    )
    args = parser.parse_args()

    app = TreadmillMonitorApp(dev_mode=args.dev_mode)
    app.run()


if __name__ == "__main__":
    main()
