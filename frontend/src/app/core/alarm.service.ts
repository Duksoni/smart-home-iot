import {inject, Injectable, signal} from '@angular/core';
import {MatSnackBar} from '@angular/material/snack-bar';
import {interval, Subscription} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {AlarmStatus} from './models';
import {ApiService} from './api.service';
import {Router} from '@angular/router';

const POLL_MS = 5_000;

@Injectable({providedIn: 'root'})
export class AlarmService {
    private readonly api = inject(ApiService);
    private readonly snackBar = inject(MatSnackBar);
    private router = inject(Router);

    readonly alarm = signal<AlarmStatus | null>(null);

    private subscription: Subscription | null = null;
    private snackBarRef: ReturnType<MatSnackBar['open']> | null = null;

    /** Call once from the root App component. */
    startPolling(): void {
        if (this.subscription) return;

        this.subscription = interval(POLL_MS)
            .pipe(switchMap(() => this.api.getAlarm()))
            .subscribe({
                next: (status) => this.handleUpdate(status),
                error: () => {
                    /* server offline – keep last known state */
                },
            });

        // Fetch immediately without waiting for the first interval tick.
        this.api.getAlarm().subscribe({
            next: (status) => this.handleUpdate(status),
            error: () => {
            },
        });
    }

    private handleUpdate(status: AlarmStatus): void {
        const previous = this.alarm();
        this.alarm.set(status);

        const justActivated = status.active && (!previous || !previous.active);
        const justCleared = !status.active && previous?.active;

        if (justActivated) {
            this.snackBarRef = this.snackBar.open(
                `🚨 ALARM ACTIVATED — ${status.reason ?? 'unknown reason'}`,
                'Go to Security',
                {panelClass: ['alarm-snackbar'], duration: 0},
            );
            this.snackBarRef.afterDismissed().subscribe(() => this.router.navigate(['/security']));
        } else if (justCleared) {
            this.snackBarRef?.dismiss();
            this.snackBarRef = null;
        }
    }
}
