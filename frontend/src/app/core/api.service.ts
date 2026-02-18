import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {environment} from '../../environments/environment';
import {ActuatorsMap, AlarmEvent, AlarmStatus, RgbState, SensorsMap, TimerState,} from './models';

@Injectable({providedIn: 'root'})
export class ApiService {
    private readonly http = inject(HttpClient);
    private readonly base = environment.apiUrl;

    // ── Alarm ──────────────────────────────────────────────────────────────────

    getAlarm(): Observable<AlarmStatus> {
        return this.http.get<AlarmStatus>(`${this.base}/alarm`);
    }

    triggerAlarm(reason = 'manual'): Observable<{ ok: boolean; alarm: AlarmStatus }> {
        return this.http.post<{ ok: boolean; alarm: AlarmStatus }>(`${this.base}/alarm/trigger`, {
            reason,
        });
    }

    deactivateAlarm(pin: string): Observable<{ ok: boolean; alarm: AlarmStatus }> {
        return this.http.post<{ ok: boolean; alarm: AlarmStatus }>(
            `${this.base}/alarm/deactivate`,
            {pin},
        );
    }

    armSystem(pin: string): Observable<{ ok: boolean; alarm: AlarmStatus }> {
        return this.http.post<{ ok: boolean; alarm: AlarmStatus }>(`${this.base}/alarm/arm`, {
            pin,
        });
    }

    disarmSystem(): Observable<{ ok: boolean; alarm: AlarmStatus }> {
        return this.http.post<{ ok: boolean; alarm: AlarmStatus }>(
            `${this.base}/alarm/disarm`,
            {},
        );
    }

    getAlarmEvents(limit = 50): Observable<{ events: AlarmEvent[] }> {
        return this.http.get<{ events: AlarmEvent[] }>(
            `${this.base}/alarm/events?limit=${limit}`,
        );
    }

    // ── Sensors ────────────────────────────────────────────────────────────────

    getSensors(): Observable<{ sensors: SensorsMap }> {
        return this.http.get<{ sensors: SensorsMap }>(`${this.base}/sensors`);
    }

    getOccupancy(): Observable<{ people_inside: number }> {
        return this.http.get<{ people_inside: number }>(`${this.base}/sensors/occupancy`);
    }

    setOccupancy(count: number): Observable<{ people_inside: number }> {
        return this.http.post<{ people_inside: number }>(`${this.base}/sensors/occupancy`, {
            count,
        });
    }

    // ── Actuators ──────────────────────────────────────────────────────────────

    getActuators(): Observable<{ actuators: ActuatorsMap }> {
        return this.http.get<{ actuators: ActuatorsMap }>(`${this.base}/actuators`);
    }

    sendActuatorCommand(
        code: string,
        action: string,
        payload: Record<string, unknown> = {},
    ): Observable<{ ok: boolean }> {
        return this.http.post<{ ok: boolean }>(`${this.base}/actuators/${code}/command`, {
            action,
            payload,
        });
    }

    // ── Timer ──────────────────────────────────────────────────────────────────

    getTimer(): Observable<TimerState> {
        return this.http.get<TimerState>(`${this.base}/timer`);
    }

    setTimer(durationSeconds: number, addSecondsIncrement?: number): Observable<TimerState> {
        return this.http.post<TimerState>(`${this.base}/timer/set`, {
            duration_seconds: durationSeconds,
            add_seconds_increment: addSecondsIncrement,
        });
    }

    addTimerTime(): Observable<TimerState> {
        return this.http.post<TimerState>(`${this.base}/timer/add`, {});
    }

    stopTimerBlink(): Observable<TimerState> {
        return this.http.post<TimerState>(`${this.base}/timer/stop`, {});
    }

    setTimerIncrement(n: number): Observable<TimerState> {
        return this.http.put<TimerState>(`${this.base}/timer/increment`, {
            add_seconds_increment: n,
        });
    }

    // ── RGB ────────────────────────────────────────────────────────────────────

    getRgb(): Observable<RgbState> {
        return this.http.get<RgbState>(`${this.base}/rgb`);
    }

    setRgbMode(mode: string): Observable<RgbState> {
        return this.http.post<RgbState>(`${this.base}/rgb/mode`, {mode});
    }
}
