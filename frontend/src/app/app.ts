import {ChangeDetectionStrategy, Component, inject, OnInit} from '@angular/core';
import {RouterLink, RouterOutlet} from '@angular/router';
import {Navbar} from './features/navbar/navbar';
import {AlarmService} from './core/alarm.service';
import {MatIconModule} from '@angular/material/icon';

@Component({
    selector: 'app-root',
    imports: [RouterOutlet, Navbar, MatIconModule, RouterLink],
    templateUrl: './app.html',
    styleUrl: './app.css',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App implements OnInit {
    readonly alarmService = inject(AlarmService);

    ngOnInit(): void {
        this.alarmService.startPolling();
    }
}
