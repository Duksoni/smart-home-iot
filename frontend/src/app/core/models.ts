export interface AlarmStatus {
    active: boolean;
    armed: boolean;
    triggered_at: number | null;
    reason: string | null;
    people_inside: number;
}

export interface AlarmEvent {
    time: string;
    action: string | null;
    reason: string | null;
    value: number;
}


export interface SensorReading {
    measurement: string;
    code: string;
    value: number | string | null;
    simulated?: string;
    runs_on?: string;
    received_at: number;

    [key: string]: unknown;
}

export type SensorsMap = Record<string, SensorReading>;


export interface ActuatorState {
    measurement: string;
    code: string;
    value: number | string | null;
    updated_at: number;

    [key: string]: unknown;
}

export type ActuatorsMap = Record<string, ActuatorState>;


export interface TimerState {
    duration_seconds: number;
    remaining_seconds: number;
    running: boolean;
    blink_mode: boolean;
    add_seconds_increment: number;
}

export type RgbMode =
    | 'light_off'
    | 'light_red'
    | 'light_green'
    | 'light_blue'
    | 'light_cyan'
    | 'light_magenta'
    | 'light_yellow'
    | 'light_white';

export interface RgbModeOption {
    mode: RgbMode;
    label: string;
    color: string;
}

export const RGB_MODE_OPTIONS: RgbModeOption[] = [
    {mode: 'light_off',     label: 'Off',     color: '#1a1a1a'},
    {mode: 'light_red',     label: 'Red',     color: '#ff0000'},
    {mode: 'light_green',   label: 'Green',   color: '#00ff00'},
    {mode: 'light_blue',    label: 'Blue',    color: '#0000ff'},
    {mode: 'light_cyan',    label: 'Cyan',    color: '#00ffff'},
    {mode: 'light_magenta', label: 'Magenta', color: '#ff00ff'},
    {mode: 'light_yellow',  label: 'Yellow',  color: '#ffff00'},
    {mode: 'light_white',   label: 'White',   color: '#ffffff'},
];

const _modeMap = new Map(RGB_MODE_OPTIONS.map(o => [o.mode, o]));

/** Returns the human-readable label for a raw mode string, e.g. 'light_green' → 'Green'. */
export function rgbModeLabel(mode: string): string {
    return _modeMap.get(mode as RgbMode)?.label ?? mode;
}

/** Returns the CSS hex colour for a raw mode string. Falls back to transparent. */
export function rgbModeColor(mode: string): string {
    return _modeMap.get(mode as RgbMode)?.color ?? 'transparent';
}

export interface RgbState {
    mode: RgbMode;
    color: string;           // CSS hex colour for preview, e.g. '#ff0000'
    available_modes: RgbMode[];
}
