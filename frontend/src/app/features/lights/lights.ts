import {
    ChangeDetectionStrategy,
    Component,
    computed,
    inject,
    OnDestroy,
    OnInit,
    signal,
} from '@angular/core';
import {interval, Subscription} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatIconModule} from '@angular/material/icon';
import {MatDividerModule} from '@angular/material/divider';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {ApiService} from '../../core/api.service';
import {RGB_MODE_OPTIONS, RgbMode, RgbState} from '../../core/models';

@Component({
    selector: 'app-lights',
    imports: [
        MatButtonModule,
        MatCardModule,
        MatIconModule,
        MatDividerModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './lights.html',
    styleUrl: './lights.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Lights implements OnInit, OnDestroy {
    private readonly api = inject(ApiService);

    readonly rgb = signal<RgbState>({mode: 'light_off', color: '#000000', available_modes: []});
    readonly modeOptions = RGB_MODE_OPTIONS;
    readonly rgbPending = signal(false);

    readonly previewColor = computed(() => this.rgb().color);
    readonly currentMode = computed(() => this.rgb().mode);
    readonly isOff = computed(() => this.currentMode() === 'light_off');

    private poll: Subscription | null = null;

    ngOnInit(): void {
        this.api.getRgb().subscribe({next: (r) => this.rgb.set(r)});
        // Poll /rgb every 3 s. Because the server now syncs its HouseState._rgb
        // whenever an rgb_led actuator message arrives (including IR-triggered ones),
        // this single endpoint always reflects the true device state.
        this.poll = interval(3_000)
            .pipe(switchMap(() => this.api.getRgb()))
            .subscribe({next: (r) => this.rgb.set(r)});
    }

    ngOnDestroy(): void {
        this.poll?.unsubscribe();
    }

    selectMode(mode: RgbMode): void {
        if (this.rgbPending() || mode === this.currentMode()) return;
        this.rgbPending.set(true);
        this.api.setRgbMode(mode).subscribe({
            next: (r) => {
                this.rgb.set(r);
                this.rgbPending.set(false);
            },
            error: () => this.rgbPending.set(false),
        });
    }
}
