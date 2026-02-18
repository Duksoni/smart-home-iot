import {ChangeDetectionStrategy, Component, computed, inject, OnDestroy, OnInit, signal,} from '@angular/core';
import {FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {interval, Subscription} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatIconModule} from '@angular/material/icon';
import {MatDividerModule} from '@angular/material/divider';
import {ApiService} from '../../core/api.service';
import {TimerState} from '../../core/models';

@Component({
    selector: 'app-timers',
    imports: [
        ReactiveFormsModule,
        MatButtonModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatDividerModule,
    ],
    templateUrl: './timers.html',
    styleUrl: './timers.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Timers implements OnInit, OnDestroy {
    private readonly api = inject(ApiService);

    readonly timerState = signal<TimerState | null>(null);

    // Local countdown ticks every second between server polls
    readonly displayRemaining = signal(0);

    readonly isRunning = computed(() => this.timerState()?.running ?? false);
    readonly isBlinking = computed(() => this.timerState()?.blink_mode ?? false);
    readonly increment = computed(() => this.timerState()?.add_seconds_increment ?? 30);

    readonly displayMM = computed(() => {
        const s = this.displayRemaining();
        return String(Math.floor(s / 60)).padStart(2, '0');
    });

    readonly displaySS = computed(() => {
        const s = this.displayRemaining();
        return String(s % 60).padStart(2, '0');
    });

    readonly pending = signal(false);
    readonly error = signal<string | null>(null);

    readonly setForm = new FormGroup({
        minutes: new FormControl(0, [Validators.required, Validators.min(0), Validators.max(99)]),
        seconds: new FormControl(0, [Validators.required, Validators.min(0), Validators.max(59)]),
    });

    readonly incrementForm = new FormGroup({
        increment: new FormControl(30, [Validators.required, Validators.min(1), Validators.max(3600)]),
    });

    private serverPoll: Subscription | null = null;
    private localTick: Subscription | null = null;

    ngOnInit(): void {
        this.fetchTimer();
        this.serverPoll = interval(5_000)
            .pipe(switchMap(() => this.api.getTimer()))
            .subscribe({next: (t) => this.applyServerState(t)});

        // Tick locally every second to avoid jumping display between polls
        this.localTick = interval(1_000).subscribe(() => {
            if (this.isRunning()) {
                this.displayRemaining.update((v) => Math.max(0, v - 1));
            }
        });
    }

    ngOnDestroy(): void {
        this.serverPoll?.unsubscribe();
        this.localTick?.unsubscribe();
    }

    private fetchTimer(): void {
        this.api.getTimer().subscribe({next: (t) => this.applyServerState(t)});
    }

    private applyServerState(t: TimerState): void {
        this.timerState.set(t);
        this.displayRemaining.set(t.remaining_seconds);
        this.incrementForm.patchValue({increment: t.add_seconds_increment});
    }

    startTimer(): void {
        if (this.setForm.invalid) return;
        const m = this.setForm.value.minutes ?? 0;
        const s = this.setForm.value.seconds ?? 0;
        const total = m * 60 + s;
        if (total <= 0) return;
        this.pending.set(true);
        this.api.setTimer(total).subscribe({
            next: (t) => {
                this.applyServerState(t);
                this.pending.set(false);
            },
            error: () => {
                this.error.set('Failed to set timer.');
                this.pending.set(false);
            },
        });
    }

    addTime(): void {
        this.pending.set(true);
        this.api.addTimerTime().subscribe({
            next: (t) => {
                this.applyServerState(t);
                this.pending.set(false);
            },
            error: () => this.pending.set(false),
        });
    }

    stopBlink(): void {
        this.pending.set(true);
        this.api.stopTimerBlink().subscribe({
            next: (t) => {
                this.applyServerState(t);
                this.pending.set(false);
            },
            error: () => this.pending.set(false),
        });
    }

    saveIncrement(): void {
        if (this.incrementForm.invalid) return;
        const n = this.incrementForm.value.increment!;
        this.api.setTimerIncrement(n).subscribe({next: (t) => this.applyServerState(t)});
    }
}
