import {Component, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {RouterLink, RouterLinkActive} from '@angular/router';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatButtonModule} from '@angular/material/button';

@Component({
    selector: 'app-navbar',
    imports: [
        CommonModule,
        RouterLink,
        RouterLinkActive,
        MatToolbarModule,
        MatButtonModule,
    ],
    templateUrl: './navbar.html',
    styleUrl: './navbar.css',
})
export class Navbar implements OnInit {
    navLinks = [
        {label: 'Dashboard', path: '/dashboard'},
        {label: 'Streams', path: '/streams'},
        {label: 'Security', path: '/security'},
        {label: 'Timers', path: '/timers'},
        {label: 'Sensors', path: '/sensors'},
        {label: 'Stats', path: '/stats'},
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
