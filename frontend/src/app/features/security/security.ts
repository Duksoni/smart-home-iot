import {
    ChangeDetectionStrategy,
    Component,
    computed,
    inject,
    OnDestroy,
    OnInit,
    signal,
} from '@angular/core';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {DatePipe} from '@angular/common';
import {interval, Subscription} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatIconModule} from '@angular/material/icon';
import {MatDividerModule} from '@angular/material/divider';
import {MatTableModule} from '@angular/material/table';
import {MatChipsModule} from '@angular/material/chips';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {ApiService} from '../../core/api.service';
import {AlarmService} from '../../core/alarm.service';
import {AlarmEvent} from '../../core/models';

@Component({
    selector: 'app-security',
    imports: [
        ReactiveFormsModule,
        DatePipe,
        MatButtonModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatDividerModule,
        MatTableModule,
        MatChipsModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './security.html',
    styleUrl: './security.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Security implements OnInit, OnDestroy {
    private readonly api = inject(ApiService);
    readonly alarmService = inject(AlarmService);

    // ── Derived state ──────────────────────────────────────────────────────────
    readonly alarm = this.alarmService.alarm;
    readonly isActive = computed(() => this.alarm()?.active ?? false);
    readonly isArmed = computed(() => this.alarm()?.armed ?? false);
    readonly peopleInside = computed(() => this.alarm()?.people_inside ?? 0);

    // ── Events log ────────────────────────────────────────────────────────────
    readonly events = signal<AlarmEvent[]>([]);
    readonly eventsLoading = signal(false);
    readonly eventColumns = ['time', 'action', 'reason'];

    // ── UI state ──────────────────────────────────────────────────────────────
    readonly actionPending = signal(false);
    readonly errorMessage = signal<string | null>(null);

    // ── Forms ─────────────────────────────────────────────────────────────────
    readonly deactivateForm = new FormGroup({
        pin: new FormControl('', [Validators.pattern(/^\d{4}$/)]),
    });

    readonly armForm = new FormGroup({
        pin: new FormControl('', [Validators.pattern(/^\d{4}$/)]),
    });

    private eventsPoll: Subscription | null = null;

    ngOnInit(): void {
        this.loadEvents();
        // Re-fetch events every 30 s
        this.eventsPoll = interval(30_000)
            .pipe(switchMap(() => this.api.getAlarmEvents(20)))
            .subscribe({next: (r) => this.events.set(r.events)});
    }

    ngOnDestroy(): void {
        this.eventsPoll?.unsubscribe();
    }

    private loadEvents(): void {
        this.eventsLoading.set(true);
        this.api.getAlarmEvents(20).subscribe({
            next: (r) => {
                this.events.set(r.events);
                this.eventsLoading.set(false);
            },
            error: () => this.eventsLoading.set(false),
        });
    }

    triggerAlarm(): void {
        this.actionPending.set(true);
        this.errorMessage.set(null);
        this.api.triggerAlarm('manual web trigger').subscribe({
            next: (r) => {
                this.alarmService.alarm.set(r.alarm);
                this.actionPending.set(false);
                this.loadEvents();
            },
            error: () => {
                this.errorMessage.set('Failed to trigger alarm.');
                this.actionPending.set(false);
            },
        });
    }

    deactivateAlarm(): void {
        if (this.deactivateForm.invalid) return;
        this.actionPending.set(true);
        this.errorMessage.set(null);
        const pin = this.deactivateForm.value.pin!;
        this.api.deactivateAlarm(pin).subscribe({
            next: (r) => {
                this.alarmService.alarm.set(r.alarm);
                this.deactivateForm.reset();
                this.actionPending.set(false);
                this.loadEvents();
            },
            error: (err) => {
                this.errorMessage.set(err.status === 403 ? 'Incorrect PIN.' : 'Deactivation failed.');
                this.actionPending.set(false);
            },
        });
    }

    armSystem(): void {
        if (this.armForm.invalid) return;
        this.actionPending.set(true);
        this.errorMessage.set(null);
        const pin = this.armForm.value.pin!;
        this.api.armSystem(pin).subscribe({
            next: (r) => {
                this.alarmService.alarm.set(r.alarm);
                this.armForm.reset();
                this.actionPending.set(false);
            },
            error: (err) => {
                this.errorMessage.set(err?.error?.detail ?? 'Failed to arm system.');
                this.actionPending.set(false);
            },
        });
    }

    disarmSystem(): void {
        this.actionPending.set(true);
        this.errorMessage.set(null);
        this.api.disarmSystem().subscribe({
            next: (r) => {
                this.alarmService.alarm.set(r.alarm);
                this.actionPending.set(false);
            },
            error: () => {
                this.errorMessage.set('Failed to disarm system.');
                this.actionPending.set(false);
            },
        });
    }
}
