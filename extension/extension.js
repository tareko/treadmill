import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

const VELOCITY_FILE = '/tmp/treadmill_velocity';
const DISTANCE_FILE = '/tmp/treadmill_distance';
const POLL_INTERVAL_SEC = 1;

export default class TreadmillVelocity extends Extension {

    enable() {
        this._displayMode = 'velocity';

        this._label = new St.Label({
            text: '-- km/h',
            y_align: 1,
        });

        this._button = new PanelMenu.Button(0.0, this.metadata.name, false);
        this._button.add_child(this._label);

        this._velocityItem = new PopupMenu.PopupMenuItem('Velocity');
        this._velocityItem.connect('activate', () => {
            this._setDisplayMode('velocity');
        });

        this._distanceItem = new PopupMenu.PopupMenuItem('Distance');
        this._distanceItem.connect('activate', () => {
            this._setDisplayMode('distance');
        });

        this._button.menu.addMenuItem(this._velocityItem);
        this._button.menu.addMenuItem(this._distanceItem);

        this._updateMenuItemOrnaments();

        Main.panel.addToStatusArea(this.uuid, this._button);

        this._timeoutId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT, POLL_INTERVAL_SEC, () => {
                this._poll();
                return GLib.SOURCE_CONTINUE;
            });

        this._poll();
    }

    disable() {
        if (this._timeoutId) {
            GLib.Source.remove(this._timeoutId);
            this._timeoutId = null;
        }
        this._button?.destroy();
        this._button = null;
        this._label = null;
        this._velocityItem = null;
        this._distanceItem = null;
    }

    _setDisplayMode(mode) {
        this._displayMode = mode;
        this._updateMenuItemOrnaments();
        this._poll();
    }

    _updateMenuItemOrnaments() {
        this._velocityItem.setOrnament(
            this._displayMode === 'velocity' ? PopupMenu.Ornament.DOT : PopupMenu.Ornament.NONE
        );
        this._distanceItem.setOrnament(
            this._displayMode === 'distance' ? PopupMenu.Ornament.DOT : PopupMenu.Ornament.NONE
        );
    }

    _poll() {
        try {
            const filePath = this._displayMode === 'velocity' ? VELOCITY_FILE : DISTANCE_FILE;
            const suffix = this._displayMode === 'velocity' ? ' km/h' : ' km';

            const file = Gio.File.new_for_path(filePath);
            if (file.query_exists(null)) {
                const [, contents] = file.load_contents(null);
                const text = new TextDecoder().decode(contents).trim();
                if (text.length > 0) {
                    this._label.set_text(`${text}${suffix}`);
                }
            }
        } catch (e) {
            // File missing or unreadable — leave display as-is
        }
    }
}
