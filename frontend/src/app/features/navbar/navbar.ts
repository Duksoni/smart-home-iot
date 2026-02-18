import {ChangeDetectionStrategy, Component, inject, OnInit, signal} from '@angular/core';
import {RouterLink, RouterLinkActive} from '@angular/router';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatButtonModule} from '@angular/material/button';
import {MatBadgeModule} from '@angular/material/badge';
import {MatIconModule} from '@angular/material/icon';
import {DatePipe} from '@angular/common';
import {AlarmService} from '../../core/alarm.service';

@Component({
    selector: 'app-navbar',
    imports: [
        RouterLink,
        RouterLinkActive,
        MatToolbarModule,
        MatButtonModule,
        MatBadgeModule,
        MatIconModule,
        DatePipe,
    ],
    templateUrl: './navbar.html',
    styleUrl: './navbar.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Navbar implements OnInit {
    readonly alarmService = inject(AlarmService);

    readonly navLinks = [
        {label: 'Dashboard', path: '/dashboard'},
        {label: 'Security', path: '/security'},
        {label: 'Streams', path: '/streams'},
        {label: 'Readings', path: '/readings'},
        {label: 'Timers', path: '/timers'},
        {label: 'Lights', path: '/lights'},
    ];

    clock = signal(new Date());

    ngOnInit() {
        const tick = () => {
            const now = new Date();
            this.clock.set(now);
            const msUntilNextSecond = 1000 - now.getMilliseconds();
            setTimeout(tick, msUntilNextSecond);
        };
        tick();
    }
}
