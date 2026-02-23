import {
    ChangeDetectionStrategy,
    Component,
    computed,
    inject,
    OnDestroy,
    OnInit,
    signal,
} from '@angular/core';
import {DatePipe} from '@angular/common';
import {interval, Subscription} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {MatCardModule} from '@angular/material/card';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatChipsModule} from '@angular/material/chips';
import {MatDividerModule} from '@angular/material/divider';
import {ApiService} from '../../core/api.service';
import {ActuatorsMap, ActuatorState, rgbModeLabel, SensorReading, SensorsMap} from '../../core/models';

interface SensorGroup {
    pi: string;
    label: string;
    codes: string[];
}

const SENSOR_GROUPS: SensorGroup[] = [
    {pi: 'PI1', label: 'PI1 – Front Door', codes: ['DS1', 'DUS1', 'DPIR1', 'DMS']},
    {pi: 'PI2', label: 'PI2 – Kitchen', codes: ['DS2', 'DUS2', 'DPIR2', 'BTN', 'DHT3', 'GSG']},
    {pi: 'PI3', label: 'PI3 – Bedroom / Living Room', codes: ['DHT1', 'DHT2', 'IR', 'DPIR3']},
];

const MULTI_READING_CODES = new Set(['DHT1', 'DHT2', 'DHT3']);

@Component({
    selector: 'app-readings',
    imports: [
        DatePipe,
        MatCardModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatChipsModule,
        MatDividerModule,
    ],
    templateUrl: './readings.html',
    styleUrl: './readings.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Readings implements OnInit, OnDestroy {
    private readonly api = inject(ApiService);

    readonly sensors = signal<SensorsMap>({});
    readonly actuators = signal<ActuatorsMap>({});
    readonly loading = signal(true);
    readonly lastUpdated = signal<Date | null>(null);

    readonly sensorGroups = SENSOR_GROUPS;

    readonly actuatorList = computed(() =>
        Object.entries(this.actuators()).map(([code, s]) => ({...s, code})),
    );

    private sensorPoll: Subscription | null = null;
    private actuatorPoll: Subscription | null = null;

    ngOnInit(): void {
        this.fetch();
        this.sensorPoll = interval(3_000)
            .pipe(switchMap(() => this.api.getSensors()))
            .subscribe({next: (r) => this.applySensors(r.sensors)});
        this.api.getActuators().subscribe({next: (r) => this.actuators.set(r.actuators)});
        this.actuatorPoll = interval(5_000)
            .pipe(switchMap(() => this.api.getActuators()))
            .subscribe({next: (r) => this.actuators.set(r.actuators)});
    }

    ngOnDestroy(): void {
        this.sensorPoll?.unsubscribe();
        this.actuatorPoll?.unsubscribe();
    }

    private fetch(): void {
        this.api.getSensors().subscribe({
            next: (r) => {
                this.applySensors(r.sensors);
                this.loading.set(false);
            },
            error: () => this.loading.set(false),
        });
    }

    private applySensors(data: SensorsMap): void {
        this.sensors.set(data);
        this.lastUpdated.set(new Date());
    }

    readingsForCode(code: string): SensorReading[] {
        const map = this.sensors();
        if (MULTI_READING_CODES.has(code)) {
            return Object.values(map).filter(
                (r) => (r.code as string)?.toUpperCase() === code,
            );
        }
        const direct = map[code];
        if (direct) return [direct];
        const found = Object.values(map).find(
            (r) => (r.code as string)?.toUpperCase() === code,
        );
        return found ? [found] : [];
    }

    formatSensorValue(reading: SensorReading): string {
        const m = (reading.measurement ?? '').toLowerCase();
        const v = reading.value;
        if (m.includes('temperature')) return `${v} °C`;
        if (m.includes('humidity')) return `${v} %`;
        if (m.includes('ultrasonic')) return `${v} cm`;
        if (m === 'motion') return v === 1 || v === '1' ? 'Motion' : 'Clear';
        if (m === 'button') return v === 1 || v === '1' ? 'Open' : 'Closed';
        if (m === 'timer_event') return "Pressed";
        if (m === 'membrane_switch') return `Key: ${v}`;
        if (m === 'gyroscope') return `Δ ${v}`;
        return String(v ?? '—');
    }

    formatActuatorValue(a: ActuatorState & {code: string}): string {
        const v = a.value;
        if (v === null || v === undefined) return '—';
        // RGB LED publishes the mode string as the value — show the pretty label.
        if (a.measurement === 'rgb_led') return rgbModeLabel(String(v));
        if (v === 1 || v === '1' || v === 'on') return 'ON';
        if (v === 0 || v === '0' || v === 'off') return 'OFF';
        return String(v);
    }

    measurementLabel(reading: SensorReading): string {
        const m = (reading.measurement ?? '').toLowerCase();
        if (m.includes('temperature')) return 'Temperature';
        if (m.includes('humidity')) return 'Humidity';
        return reading.measurement ?? '';
    }

    iconForCode(code: string): string {
        if (code.startsWith('DHT')) return 'thermostat';
        if (code.startsWith('DUS')) return 'radar';
        if (code.startsWith('DPIR')) return 'spatial_tracking';
        if (code.startsWith('DS')) return 'door_front';
        if (code === 'DMS') return 'dialpad';
        if (code === 'BTN') return 'radio_button_checked';
        if (code === 'IR') return 'settings_remote';
        if (code === 'GSG') return 'rotate_90_degrees_cw';
        return 'sensors';
    }

    iconForActuator(code: string): string {
        if (code === 'DL') return 'tungsten';
        if (code === 'DB') return 'volume_up';
        if (code === 'BRGB') return 'lightbulb';
        if (code === 'LCD') return 'text_snippet';
        if (code === '4SD') return 'timer';
        return 'electrical_services';
    }

    isSimulatedSensor(reading: SensorReading): boolean {
        return reading.simulated === 'true' || (reading.simulated as unknown) === true;
    }

    isSimulatedActuator(a: ActuatorState): boolean {
        const s = a['simulated'];
        return s === 'true' || s === true;
    }
}
